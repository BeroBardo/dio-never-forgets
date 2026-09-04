---
name: dio-knowledge
description: Busca econômica em banco de conhecimento leve. Use quando precisar de contexto passado de conversas anteriores.
category: note-taking
---

# DIO Knowledge — Busca Econômica

Quando precisar de contexto de conversas passadas:

1. **NÃO** carregar state.db inteiro no contexto
2. **SIM** usar `dio_search_knowledge.py "query"` pra buscar no banco leve
3. Retorna top-5 resultados com resumo + keywords
4. Se não encontrar, aí sim tentar session_search

## Setup (1 vez)
```bash
# Extrair conhecimento do state.db
python3 dio_extract_knowledge.py
```

## Uso
```bash
# Buscar contexto
python3 dio_search_knowledge.py "licitações PNCP"
python3 dio_search_knowledge.py "emprego Gabi"
python3 dio_search_knowledge.py "WhatsApp bridge"
```

## Economia
- state.db: 347MB (93K mensagens)
- dio_knowledge.db: 32KB (resumos + FTS5)
- Redução: 99.99%
- Busca: ~50 tokens (vs ~184MB no contexto)
