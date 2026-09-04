#!/usr/bin/env python3
"""
DIO Knowledge Search — busca econômica no banco de conhecimento leve.
Uso: python3 dio_search_knowledge.py "query" [--limit N]
Retorna top-N resultados com resumo + keywords + fonte.
"""
import sqlite3, sys, re
from pathlib import Path

KNOW_DB = Path(os.environ.get('DIO_KNOWLEDGE_DB', 'dio_knowledge.db'))

def search(query, limit=5):
    if not KNOW_DB.exists():
        print("ERRO: dio_knowledge.db nao existe. Rode dio_extract_knowledge.py primeiro.")
        return []
    
    conn = sqlite3.connect(str(KNOW_DB))
    
    # Busca FTS5 — très trigram (flexível)
    try:
        # Tenta busca FTS direta
        rows = conn.execute('''
            SELECT k.summary, k.keywords, k.timestamp, k.role, k.session_title,
                   rank
            FROM knowledge_fts f
            JOIN knowledge k ON k.id = f.rowid
            WHERE knowledge_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ''', (query, limit)).fetchall()
    except:
        # Fallback: busca LIKE
        q = f'%{query}%'
        rows = conn.execute('''
            SELECT summary, keywords, timestamp, role, session_title, 0
            FROM knowledge 
            WHERE summary LIKE ? OR keywords LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (q, q, limit)).fetchall()
    
    conn.close()
    return rows

def format_result(row):
    import time
    summary, keywords, ts, role, title, rank = row
    t = time.strftime('%d/%m %H:%M', time.localtime(ts)) if ts else '?'
    icon = '👤' if role == 'user' else '🤖'
    return f"{icon} [{t}] {title or 'sessão'}: {summary[:150]}"

if __name__ == '__main__':
    query = ' '.join(sys.argv[1:])
    if not query:
        print("USO: dio_search_knowledge.py 'query'")
        sys.exit(1)
    
    limit = 5
    if '--limit' in sys.argv:
        idx = sys.argv.index('--limit')
        limit = int(sys.argv[idx+1])
    
    results = search(query, limit)
    if not results:
        print(f"Nenhum resultado para: {query}")
    else:
        print(f"=== {len(results)} resultados para: {query} ===")
        for r in results:
            print(format_result(r))
            print()
