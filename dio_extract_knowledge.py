#!/usr/bin/env python3
"""
DIO Knowledge Extractor — extrai resumos do state.db pra banco leve pesquisável.
Cria dio_knowledge.db (FTS5), no volume com mais espaço livre (ou env DIO_KNOWLEDGE_DB).
Lê configuração do dio.conf (criado pelo setup.py).
"""
import sqlite3, json, re, hashlib, time, os
from pathlib import Path
from dio_storage_resolve import pick_best_storage, read_dio_conf

# Detecta state.db: env > dio.conf > locais padrão
def find_state_db():
    # 1. Variável de ambiente
    env = os.environ.get('HERMES_STATE_DB')
    if env and Path(env).exists():
        return Path(env)
    # 2. dio.conf
    conf, _ = read_dio_conf()
    if conf.get('state_db') and Path(conf['state_db']).exists():
        return Path(conf['state_db'])
    # 3. Locais padrão do Hermes
    candidates = [
        Path.home() / '.hermes' / 'state.db',
        Path('/run/media/system/HERMES/.hermes/state.db'),
        Path('/var/home/ber/.hermes/state.db'),
        Path.cwd() / 'state.db',
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

STATE_DB = find_state_db()
# KNOW_DB: escolha automática (env manual > dio.conf > volume mais espaçoso)
KNOW_DB_PATH, _free = pick_best_storage()
KNOW_DB = Path(KNOW_DB_PATH)

def extract_keywords(text):
    """Extrai keywords-chave de texto."""
    if not text:
        return []
    # Remove tool calls, URLs longas, JSON
    text = re.sub(r'<antm:.*?</antm:.*?>', '', text, flags=re.DOTALL)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\{[^{}]{50,}\}', '', text)
    # Pega palavras significativas (>3 chars, não é número)
    words = re.findall(r'\b[a-záàâãéèêíïóôõúüç]{4,}\b', text.lower())
    # Filtra stopwords
    stopwords = {'para', 'como', 'isso', 'aquele', 'esta', 'este', 'mais', 'pode',
                 'tambem', 'porque', 'quando', 'ainda', 'desde', 'todos', 'sobre',
                 'entre', 'depois', 'antes', 'muito', 'onde', 'qual', 'quais',
                 'voce', 'ele', 'ela', 'eles', 'elas', 'nos', 'voces', 'aqueles',
                 'aquelas', 'esta', 'estas', 'estes', 'esses', 'essas', 'cada',
                 'todo', 'toda', 'todos', 'todas', 'outro', 'outra', 'outros', 'outras',
                 'algo', 'nada', 'alguem', 'ninguem', 'algum', 'nenhum', 'alguma', 'nenhuma',
                 'pela', 'pelo', 'pelos', 'pelas', 'dessa', 'desse', 'dessas', 'desses',
                 'naquela', 'naquele', 'naqueles', 'naquelas', 'daquele', 'daquela',
                 'daqueles', 'daquelas', 'fazer', 'feito', 'faz', 'fez', 'vai', 'vao',
                 'vou', 'ser', 'ter', 'estar', 'tem', 'tinha', 'estava', 'esta', 'estao',
                 'foram', 'sido', 'sendo', 'seja', 'sejam', 'sejas', 'fosse', 'fossem',
                 'era', 'eram', 'havia', 'haviam', 'haveria', 'haver', 'havera', 'haverao',
                 'teria', 'teriam', 'tera', 'terao', 'serei', 'sera', 'serao', 'estarei',
                 'estara', 'estarao', 'virei', 'vira', 'virao', 'poderei', 'podera', 'poderao',
                 'farei', 'fara', 'farao', 'tenho', 'tivemos', 'tiver', 'tiverem', 'tivermos',
                 'tenha', 'tenham', 'tenhamos', 'tivesse', 'tivessem', 'tivessemos'}
    seen = set()
    kw = []
    for w in words:
        if w not in stopwords and w not in seen and len(w) > 4:
            seen.add(w)
            kw.append(w)
            if len(kw) >= 15:
                break
    return kw

def summarize_message(content, max_chars=300):
    """Gera resumo curto de uma mensagem."""
    if not content:
        return ""
    # Limpa tool calls internos
    content = re.sub(r'<antm:.*?</antm:.*?>', '[tool output]', content, flags=re.DOTALL)
    # Pega primeiros chars significativos
    clean = re.sub(r'\s+', ' ', content).strip()
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars] + '...'

def build_knowledge_db():
    """Extrai state.db -> dio_knowledge.db leve."""
    if not STATE_DB or not STATE_DB.exists():
        print(f"ERRO: state.db nao encontrado. Defina HERMES_STATE_DB ou rode o setup.py")
        print(f"Locais verificados: ~/.hermes/state.db, /run/media/system/HERMES/.hermes/state.db")
        return
    
    print(f"[EXTRACT] Lendo state.db: {STATE_DB}")
    print(f"[EXTRACT] Gravando em: {KNOW_DB}")
    
    # Cria banco leve
    KNOW_DB.parent.mkdir(parents=True, exist_ok=True)
    conn_k = sqlite3.connect(str(KNOW_DB))
    conn_k.execute('DROP TABLE IF EXISTS knowledge')
    conn_k.execute('DROP TABLE IF EXISTS knowledge_fts')
    conn_k.execute('''CREATE TABLE knowledge (
        id INTEGER PRIMARY KEY,
        session_id TEXT,
        role TEXT,
        summary TEXT,
        keywords TEXT,
        timestamp REAL,
        token_count INTEGER,
        session_title TEXT,
        session_model TEXT
    )''')
    conn_k.execute('''CREATE VIRTUAL TABLE knowledge_fts USING fts5(
        summary, keywords, session_title, content='knowledge', content_rowid='id'
    )''')
    
    # Abre state.db
    conn_s = sqlite3.connect(str(STATE_DB))
    conn_s.row_factory = sqlite3.Row
    
    # Busca sessions
    sessions = conn_s.execute('''
        SELECT id, display_name, title, message_count, 
               model, system_prompt, created_at
        FROM sessions
        ORDER BY created_at DESC
    ''').fetchall()
    
    print(f"[EXTRACT] {len(sessions)} sessoes encontradas")
    
    total = 0
    for sess in sessions:
        sid = sess['id']
        title = sess['display_name'] or sess['title'] or sid[:8]
        model = sess['model'] or 'unknown'
        
        # Messages da sessão
        msgs = conn_s.execute('''
            SELECT role, content, timestamp, token_count
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
        ''', (sid,)).fetchall()
        
        for msg in msgs:
            content = msg['content'] or ''
            if not content.strip() or len(content) < 50:
                continue
            
            summary = summarize_message(content)
            if not summary:
                continue
                
            keywords = extract_keywords(content)
            kw_str = ', '.join(keywords)
            
            cur = conn_k.execute('''
                INSERT INTO knowledge (session_id, role, summary, keywords, timestamp, token_count, session_title, session_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (sid, msg['role'], summary, kw_str, msg['timestamp'] or 0, msg['token_count'] or 0, title, model))
            
            rowid = cur.lastrowid
            conn_k.execute('INSERT INTO knowledge_fts(rowid, summary, keywords, session_title) VALUES (?, ?, ?, ?)',
                          (rowid, summary, kw_str, title))
            total += 1
    
    conn_k.commit()
    conn_k.close()
    conn_s.close()
    
    # Conecta no sync de memórias do Hermes se existir
    try:
        from dio_memory_sync import sync_memories_to_knowledge
        sync_memories_to_knowledge()
    except Exception:
        pass

if __name__ == '__main__':
    build_knowledge_db()