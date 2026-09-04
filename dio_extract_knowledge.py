#!/usr/bin/env python3
"""
DIO Knowledge Extractor — extrai resumos do state.db pra banco leve pesquisável.
Cria dio_knowledge.db com FTS5, pronto pra busca econômica.
"""
import sqlite3, json, re, hashlib, time
from pathlib import Path

STATE_DB = Path(os.environ.get('HERMES_STATE_DB', os.path.expanduser('~/.hermes/state.db')))
KNOW_DB = Path(os.environ.get('DIO_KNOWLEDGE_DB', 'dio_knowledge.db'))

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
                 'também', 'porque', 'quando', 'ainda', 'desde', 'todos', 'sobre',
                 'entre', 'depois', 'antes', 'muito', 'onde', 'qual', 'quais',
                 'você', 'ele', 'ela', 'eles', 'elas', 'nos', 'vocês', 'aqueles',
                 'aquelas', 'esta', 'estas', 'estes', 'esses', 'essas', 'cada',
                 'todo', 'toda', 'todos', 'todas', 'outro', 'outra', 'outros', 'outras',
                 'algo', 'nada', 'alguém', 'ninguém', 'algum', 'nenhum', 'alguma', 'nenhuma',
                 'para', 'pela', 'pelo', 'pelos', 'pelas', 'dessa', 'desse', 'dessas', 'desses',
                 'naquela', 'naquele', 'naqueles', 'naquelas', 'desse', 'dessa', 'desses', 'dessas',
                 'daquele', 'daquela', 'daqueles', 'daquelas', 'naquele', 'naquela', 'naqueles', 'naquelas',
                 'fazer', 'feito', 'feito', 'faz', 'fez', 'vai', 'vão', 'vou', 'ser', 'ter', 'estar',
                 'ter', 'tem', 'tinha', 'tinha', 'estava', 'está', 'estão', 'foram', 'ser', 'sido',
                 'sendo', 'seja', 'sejam', 'sejas', 'fosse', 'fossem', 'fosse', 'fossem', 'era', 'eram',
                 'havia', 'haviam', 'haveria', 'haver', 'haverá', 'haverão', 'teria', 'teriam', 'terá',
                 'terão', 'serei', 'será', 'serão', 'estarei', 'estará', 'estarão', 'virei', 'virá',
                 'virão', 'poderei', 'poderá', 'poderão', 'farei', 'fará', 'farão', 'tenho', 'tivemos',
                 'tiver', 'tiverem', 'tivermos', 'tinha', 'tinham', 'tenha', 'tenham', 'tenhamos', 'tivesse',
                 'tivessem', 'tivéssemos', 'tiver', 'tiverem', 'tivermos', 'tenha', 'tenham', 'tenhamos',
                 'tivesse', 'tivessem', 'tivéssemos', 'tiver', 'tiverem', 'tivermos', 'tenha', 'tenham',
                 'tenhamos', 'tivesse', 'tivessem', 'tivéssemos', 'tiver', 'tiverem', 'tivermos', 'tenha',
                 'tenham', 'tenhamos', 'tivesse', 'tivessem', 'tivéssemos', 'tiver', 'tiverem', 'tivermos',
                 'tenha', 'tenham', 'tenhamos', 'tivesse', 'tivessem', 'tivéssemos', 'tiver', 'tiverem',
                 'tivermos', 'tenha', 'tenham', 'tenhamos', 'tivesse', 'tivessem', 'tivéssemos', 'tiver',
                 'tiverem', 'tivermos', 'tenha', 'tenham', 'tenhamos', 'tivesse', 'tivessem', 'tivéssemos',
                 'tiver', 'tiverem', 'tivermos', 'tenha', 'tenham', 'tenhamos', 'tivesse', 'tivessem',
                 'tivéssemos', 'tiver', 'tiverem', 'tivermos', 'tenha', 'tenham', 'tenhamos', 'tivesse',
                 'tivessem', 'tivéssemos', 'tiver', 'tiverem', 'tivermos', 'tenha', 'tenham', 'tenhamos',
                 'tivesse', 'tivessem', 'tivéssemos', 'tiver', 'tiverem', 'tivermos', 'tenha', 'tenham',
                 'tenhamos', 'tivesse', 'tivessem', 'tivéssemos', 'tiver', 'tiverem', 'tivermos', 'tenha',
                 'tenham', 'tenhamos', 'tivesse', 'tivessem', 'tivéssemos', 'tiver', 'tiverem', 'tivermos',
                 'tenha', 'tenham', 'tenhamos', 'tivesse', 'tivessem', 'tivéssemos'}
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
    if not STATE_DB.exists():
        print(f"ERRO: state.db nao encontrado em {STATE_DB}")
        return
    
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
    
    # Extrai do state.db
    conn_s = sqlite3.connect(str(STATE_DB))
    
    # Pega sessões com tokens significativos
    sessions = conn_s.execute('''
        SELECT id, display_name, title, message_count, 
               COALESCE(input_tokens,0)+COALESCE(output_tokens,0) as total_tok,
               last_activity_at, model
        FROM sessions 
        WHERE COALESCE(input_tokens,0)+COALESCE(output_tokens,0) > 10000
        ORDER BY last_activity_at DESC
    ''').fetchall()
    
    print(f"Sessoes com >10k tokens: {len(sessions)}")
    
    total_extracted = 0
    for sess in sessions:
        sid, sname, stitle, msg_count, total_tok, last_at, model = sess
        # Pega mensagens significativas desta sessão
        messages = conn_s.execute('''
            SELECT role, content, timestamp, token_count
            FROM messages 
            WHERE session_id = ? 
            AND token_count > 50
            AND role IN ('user', 'assistant')
            ORDER BY timestamp ASC
        ''', (sid,)).fetchall()
        
        for role, content, ts, tok in messages:
            summary = summarize_message(content)
            keywords = extract_keywords(content)
            if summary:
                conn_k.execute('''
                    INSERT INTO knowledge 
                    (session_id, role, summary, keywords, timestamp, token_count, session_title, session_model)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (sid, role, summary, ' '.join(keywords), ts, tok, stitle, model))
                total_extracted += 1
    
    # Cria índice FTS5
    conn_k.execute('''CREATE VIRTUAL TABLE knowledge_fts 
        USING fts5(summary, keywords, content='knowledge', content_rowid='id')''')
    conn_k.execute('INSERT INTO knowledge_fts (rowid, summary, keywords) SELECT id, summary, keywords FROM knowledge')
    conn_k.execute('CREATE INDEX idx_knowledge_ts ON knowledge(timestamp)')
    conn_k.execute('CREATE INDEX idx_knowledge_session ON knowledge(session_id)')
    
    conn_k.commit()
    conn_s.close()
    
    # Stats
    sz = KNOW_DB.stat().st_size
    count = conn_k.execute('SELECT COUNT(*) FROM knowledge').fetchone()[0]
    print(f"Extraidos: {count} entradas")
    print(f"Banco leve: {sz} bytes ({sz//1024}KB)")
    print(f"Reducao: 347MB -> {sz//1024}KB ({100-sz*100//347/1024:.0f}% menor)")
    
    conn_k.close()

if __name__ == '__main__':
    build_knowledge_db()
