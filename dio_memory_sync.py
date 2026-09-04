#!/usr/bin/env python3
"""
DIO Memory Consolidation & Auto-Sync
====================================
Integração entre o Hermes Memory (MEMORY.md / USER.md) e o Dio Never Forgets (dio_knowledge.db).

O que faz:
1. Sincroniza fatos do MEMORY.md e USER.md para o dio_knowledge.db sob a role 'memory'
2. Indexa as memórias no FTS5 para busca unificada (histórico + memórias persistentes)
3. Alivia o limite de caracteres do MEMORY.md (2.200 chars), permitindo consolidar e arquivar
"""
import sqlite3, os, time, re
from pathlib import Path
from dio_storage_resolve import pick_best_storage

KNOW_DB_PATH, _ = pick_best_storage()
KNOW_DB = Path(KNOW_DB_PATH)

def get_hermes_memory_dir():
    """Detecta pasta de memórias do Hermes."""
    candidates = [
        Path(os.environ.get('HERMES_HOME', '')) / 'memories',
        Path('/run/media/system/HERMES/.hermes/memories'),
        Path.home() / '.hermes' / 'memories',
    ]
    for c in candidates:
        if c.exists() and (c / 'MEMORY.md').exists():
            return c
    return None

def sync_memories_to_knowledge():
    """Indexa todo o MEMORY.md e USER.md no dio_knowledge.db com FTS5."""
    mem_dir = get_hermes_memory_dir()
    if not mem_dir or not KNOW_DB.exists():
        return 0

    conn = sqlite3.connect(str(KNOW_DB))
    
    # Remove registros antigos de memórias para não duplicar
    old_ids = [r[0] for r in conn.execute("SELECT id FROM knowledge WHERE session_id = 'hermes_persistent_memory'").fetchall()]
    for oid in old_ids:
        try:
            conn.execute("INSERT INTO knowledge_fts(knowledge_fts, rowid, summary, keywords) VALUES ('delete', ?, '', '')", (oid,))
        except Exception:
            pass
    conn.execute("DELETE FROM knowledge WHERE session_id = 'hermes_persistent_memory'")

    files = [('MEMORY.md', 'System Memory (Notes)'), ('USER.md', 'User Profile Memory')]
    total_added = 0

    for filename, title in files:
        fpath = mem_dir / filename
        if not fpath.exists():
            continue

        raw = fpath.read_text(encoding='utf-8')
        # Separa pelas seções '§' do Hermes
        sections = [s.strip() for s in raw.split('§') if s.strip()]

        for sec in sections:
            # Extrai palavras-chave
            words = re.findall(r'\b[a-záàâãéèêíïóôõúüç]{4,}\b', sec.lower())
            kw = ', '.join(set(words[:15]))
            
            cur = conn.execute('''
                INSERT INTO knowledge (session_id, role, summary, keywords, timestamp, token_count, session_title, session_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('hermes_persistent_memory', 'memory', sec, kw, time.time(), len(sec)//4, f'Hermes Memory ({title})', 'hermes-core'))
            
            rowid = cur.lastrowid
            conn.execute('''
                INSERT INTO knowledge_fts (rowid, summary, keywords)
                VALUES (?, ?, ?)
            ''', (rowid, sec, kw))
            total_added += 1

    conn.commit()
    conn.close()
    return total_added

if __name__ == '__main__':
    added = sync_memories_to_knowledge()
    print(f"[DIO MEMORY SYNC] ✅ {added} blocos de memória permanente consolidados no FTS5.")
