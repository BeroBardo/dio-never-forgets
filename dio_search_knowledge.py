#!/usr/bin/env python3
"""DIO Knowledge Search — busca economica no banco leve."""
import sqlite3, sys, time

KNOW_DB = '/var/mnt/lentao/dio_shared/dio_knowledge.db'

def search(query, limit=5):
    conn = sqlite3.connect(KNOW_DB)
    fts_query = ' OR '.join(query.split())
    try:
        rows = conn.execute('''
            SELECT k.summary, k.keywords, k.timestamp, k.role, k.session_title
            FROM knowledge_fts f
            JOIN knowledge k ON k.id = f.rowid
            WHERE knowledge_fts MATCH ?
            ORDER BY rank LIMIT ?
        ''', (fts_query, limit)).fetchall()
    except:
        q = f'%{query}%'
        rows = conn.execute('''
            SELECT summary, keywords, timestamp, role, session_title
            FROM knowledge WHERE summary LIKE ? OR keywords LIKE ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (q, q, limit)).fetchall()
    conn.close()
    return rows

def format_result(row):
    summary, keywords, ts, role, title = row
    t = time.strftime('%d/%m %H:%M', time.localtime(ts)) if ts else '?'
    icon = 'U' if role == 'user' else 'A'
    return f"{icon} [{t}] {title or 'session'}: {summary[:150]}"

if __name__ == '__main__':
    args = sys.argv[1:]
    limit = 5
    if '--limit' in args:
        idx = args.index('--limit')
        limit = int(args[idx+1])
        del args[idx:idx+2]
    query = ' '.join(args)
    if not query:
        print("USO: dio_search_knowledge.py 'query'")
        sys.exit(1)
    results = search(query, limit)
    if not results:
        print(f"Nenhum resultado para: {query}")
    else:
        print(f"=== {len(results)} resultados para: {query} ===")
        for r in results:
            print(format_result(r))
            print()
