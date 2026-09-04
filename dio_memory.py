#!/usr/bin/env python3
"""
Dio Memory Engine (v2) — Memória Local Esperta, Rápida e Enxuta
==============================================================
- 1 tabela SQLite + FTS5
- Deduplicação por fingerprint (hash)
- Relação de substituição (supersedes)
- Sync incremental real (checkpoint por ID de mensagem)
- Heurística determinística de extração (zero custo de LLM)
- Interface Python e CLI unificada
"""
import os, sys, sqlite3, hashlib, re, time
from typing import Optional, List, Dict, Any
from pathlib import Path

# --- Auto-detecção de Paths ---
def get_default_paths():
    state_candidates = [
        os.environ.get('HERMES_STATE_DB'),
        '/run/media/system/HERMES/.hermes/state.db',
        str(Path.home() / '.hermes' / 'state.db'),
        '/var/home/ber/.hermes/state.db',
    ]
    state_db = None
    for c in state_candidates:
        if c and os.path.exists(c):
            state_db = c
            break

    know_db = os.environ.get('DIO_KNOWLEDGE_DB')
    if not know_db:
        if os.path.exists('/var/mnt/lentao/dio_shared'):
            know_db = '/var/mnt/lentao/dio_shared/dio_knowledge.db'
        else:
            know_db = str(Path.home() / '.dio_knowledge.db')

    return state_db, know_db

DEFAULT_STATE_DB, DEFAULT_KNOW_DB = get_default_paths()


class DioMemory:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DEFAULT_KNOW_DB
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                kind TEXT NOT NULL,
                supersedes INTEGER,
                fingerprint TEXT UNIQUE,
                src TEXT,
                ts REAL
            )''')
            conn.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS memos_fts USING fts5(
                text, kind, content='memos', content_rowid='id'
            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS sync_checkpoints (
                source_name TEXT PRIMARY KEY,
                last_msg_id INTEGER,
                last_sync_ts REAL
            )''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memos_kind ON memos(kind)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_memos_fp ON memos(fingerprint)')

    @staticmethod
    def _make_fingerprint(kind: str, text: str) -> str:
        norm = re.sub(r'\s+', ' ', text.strip().lower())
        raw = f"{kind}|{norm}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]

    def remember(self, text: str, kind: str = 'fact', src: str = 'manual', auto_supersede: bool = False, conn: Optional[sqlite3.Connection] = None) -> int:
        """Salva ou atualiza um fato/decisão/configuração."""
        text = text.strip()
        if not text:
            return 0

        fp = self._make_fingerprint(kind, text)
        now = time.time()
        supersedes_id = None

        def _exec(c):
            nonlocal supersedes_id
            if auto_supersede and kind in ('config', 'decision'):
                words = [w for w in re.findall(r'\b\w{4,}\b', text.lower()) if w not in ('usar', 'usando', 'para', 'com')]
                if words:
                    q = ' OR '.join(words[:3])
                    try:
                        prev = c.execute('''
                            SELECT m.id FROM memos_fts f
                            JOIN memos m ON m.id = f.rowid
                            WHERE memos_fts MATCH ? AND m.kind = ? AND m.id NOT IN (SELECT supersedes FROM memos WHERE supersedes IS NOT NULL)
                            ORDER BY m.ts DESC LIMIT 1
                        ''', (q, kind)).fetchone()
                        if prev:
                            supersedes_id = prev[0]
                    except Exception:
                        pass

            existing = c.execute('SELECT id FROM memos WHERE fingerprint = ?', (fp,)).fetchone()
            if existing:
                memo_id = existing[0]
                c.execute('UPDATE memos SET ts = ?, src = ? WHERE id = ?', (now, src, memo_id))
                return int(memo_id)

            cur = c.execute('''
                INSERT INTO memos (text, kind, supersedes, fingerprint, src, ts)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (text, kind, supersedes_id, fp, src, now))
            memo_id = cur.lastrowid or 0

            c.execute('INSERT INTO memos_fts (rowid, text, kind) VALUES (?, ?, ?)', (memo_id, text, kind))
            return int(memo_id)

        if conn is not None:
            return _exec(conn)
        else:
            with self._get_conn() as c:
                return _exec(c)

    def recall(self, query: str, kinds: Optional[List[str]] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Busca inteligente FTS5. Retorna fatos ordenados por relevância e recência."""
        if not query.strip():
            return []

        words = query.strip().split()
        fts_query = ' OR '.join(words)
        results = []

        with self._get_conn() as conn:
            try:
                rows = conn.execute('''
                    SELECT m.id, m.text, m.kind, m.supersedes, m.ts, m.src
                    FROM memos_fts f
                    JOIN memos m ON m.id = f.rowid
                    WHERE memos_fts MATCH ?
                    ORDER BY rank, m.ts DESC
                    LIMIT ?
                ''', (fts_query, limit * 2)).fetchall()
            except Exception:
                q_like = f"%{query}%"
                rows = conn.execute('''
                    SELECT id, text, kind, supersedes, ts, src
                    FROM memos
                    WHERE text LIKE ?
                    ORDER BY ts DESC
                    LIMIT ?
                ''', (q_like, limit)).fetchall()

            for r in rows:
                mid, txt, k, sup, ts, src = r
                if kinds and k not in kinds:
                    continue
                results.append({
                    'id': mid,
                    'text': txt,
                    'kind': k,
                    'supersedes': sup,
                    'timestamp': ts,
                    'source': src
                })
                if len(results) >= limit:
                    break

        return results

    def sync_incremental(self, state_db_path: Optional[str] = None, batch_limit: int = 5000) -> int:
        """Varre apenas mensagens novas do state.db a partir do último checkpoint em uma única transação rápida."""
        sdb_path = state_db_path or DEFAULT_STATE_DB
        if not sdb_path or not os.path.exists(sdb_path):
            print(f"[SYNC] Erro: state.db não encontrado em '{sdb_path}'")
            return 0

        last_id = 0
        with self._get_conn() as conn:
            row = conn.execute('SELECT last_msg_id FROM sync_checkpoints WHERE source_name = ?', ('hermes_state_db',)).fetchone()
            if row:
                last_id = row[0]

        conn_s = sqlite3.connect(sdb_path)
        conn_s.row_factory = sqlite3.Row
        
        new_msgs = conn_s.execute('''
            SELECT id, session_id, role, content, timestamp
            FROM messages
            WHERE id > ? AND LENGTH(content) > 20
            ORDER BY id ASC
            LIMIT ?
        ''', (last_id, batch_limit)).fetchall()

        if not new_msgs:
            conn_s.close()
            return 0

        extracted_count = 0
        max_seen_id = last_id

        # Realiza todas as inserções numa transação única e veloz
        with self._get_conn() as conn_k:
            for msg in new_msgs:
                mid = msg['id']
                if mid > max_seen_id:
                    max_seen_id = mid

                content = msg['content'] or ''
                sid = msg['session_id'] or 'unknown'
                src_tag = f"session:{sid[:8]} msg:{mid}"

                # Ignora tool tags e blocos enormes de código
                clean = re.sub(r'<antm:.*?</antm:.*?>', '', content, flags=re.DOTALL)
                clean = re.sub(r'```[\s\S]*?```', '[code]', clean)
                clean = re.sub(r'\s+', ' ', clean).strip()

                if len(clean) < 25 or len(clean) > 2000:
                    continue

                lower = clean.lower()
                kind = None
                
                if any(k in lower for k in ['porta ', 'port ', 'ip ', 'tailscale', 'host', 'sink', 'gpu', 'bazzite', 'driver', 'modelo:']):
                    kind = 'config'
                elif any(k in lower for k in ['decid', 'defini', 'vou usar', 'escolh', 'mudei para', 'troquei para', 'regra permanente']):
                    kind = 'decision'
                elif any(k in lower for k in ['prefiro', 'sempre use', 'nunca use', 'não gosto', 'gosto de']):
                    kind = 'pref'
                elif any(k in lower for k in ['é um ', 'funciona com ', 'salvo em ', 'localizado em ']) and len(clean) < 400:
                    kind = 'fact'

                if kind:
                    memo_text = clean[:350] + ('...' if len(clean) > 350 else '')
                    self.remember(memo_text, kind=kind, src=src_tag, auto_supersede=False, conn=conn_k)
                    extracted_count += 1

            conn_k.execute('''
                INSERT INTO sync_checkpoints (source_name, last_msg_id, last_sync_ts)
                VALUES ('hermes_state_db', ?, ?)
                ON CONFLICT(source_name) DO UPDATE SET last_msg_id = ?, last_sync_ts = ?
            ''', (max_seen_id, time.time(), max_seen_id, time.time()))

        conn_s.close()
        return extracted_count

    def stats(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            total = conn.execute('SELECT COUNT(*) FROM memos').fetchone()[0]
            by_kind = dict(conn.execute('SELECT kind, COUNT(*) FROM memos GROUP BY kind').fetchall())
            superseded = conn.execute('SELECT COUNT(*) FROM memos WHERE supersedes IS NOT NULL').fetchone()[0]
            last_sync = conn.execute('SELECT last_msg_id, last_sync_ts FROM sync_checkpoints WHERE source_name = ?', ('hermes_state_db',)).fetchone()
            db_size_kb = Path(self.db_path).stat().st_size // 1024 if os.path.exists(self.db_path) else 0

        return {
            'total_memos': total,
            'by_kind': by_kind,
            'superseded_memos': superseded,
            'db_size_kb': db_size_kb,
            'last_sync_msg_id': last_sync[0] if last_sync else 0,
            'last_sync_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_sync[1])) if last_sync else 'Never'
        }


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help', 'help'):
        print("Dio Memory Engine CLI")
        print("Uso:")
        print("  dio recall <query> [--kind <kind>] [--limit N]")
        print("  dio remember <text> [--kind <kind>]")
        print("  dio sync")
        print("  dio stats")
        return

    cmd = args[0]
    mem = DioMemory()

    if cmd == 'recall':
        query_words = []
        limit = 5
        kinds = None
        i = 1
        while i < len(args):
            if args[i] == '--limit' and i + 1 < len(args):
                limit = int(args[i+1])
                i += 2
            elif args[i] == '--kind' and i + 1 < len(args):
                kinds = [args[i+1]]
                i += 2
            else:
                query_words.append(args[i])
                i += 1
        
        q = ' '.join(query_words)
        results = mem.recall(q, kinds=kinds, limit=limit)
        if not results:
            print(f"Nenhum memo encontrado para '{q}'")
            return
        
        print(f"=== {len(results)} memos encontrados ===")
        for r in results:
            t = time.strftime('%d/%m %H:%M', time.localtime(r['timestamp']))
            sup_str = f" [substitui #{r['supersedes']}]" if r['supersedes'] else ""
            print(f"• [{r['kind'].upper()}] ({t}){sup_str} {r['text']}")

    elif cmd == 'remember':
        text_words = []
        kind = 'fact'
        i = 1
        while i < len(args):
            if args[i] == '--kind' and i + 1 < len(args):
                kind = args[i+1]
                i += 2
            else:
                text_words.append(args[i])
                i += 1
        txt = ' '.join(text_words)
        mid = mem.remember(txt, kind=kind, auto_supersede=True)
        print(f"✅ Memo gravado (#{mid}): [{kind}] {txt}")

    elif cmd == 'sync':
        print("[SYNC] Executando sincronização incremental...")
        count = mem.sync_incremental()
        print(f"✅ Sync concluído: {count} novos memos extraídos.")

    elif cmd == 'stats':
        st = mem.stats()
        print("=== Dio Memory Stats ===")
        print(f"Total de Memos: {st['total_memos']}")
        print(f"Tamanho do Banco: {st['db_size_kb']} KB ({st['db_size_kb']/1024:.2f} MB)")
        print(f"Por Categoria: {st['by_kind']}")
        print(f"Memos Substituídos/Históricos: {st['superseded_memos']}")
        print(f"Último Checkpoint ID: {st['last_sync_msg_id']} ({st['last_sync_time']})")


if __name__ == '__main__':
    main()
