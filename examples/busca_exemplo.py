#!/usr/bin/env python3
"""Exemplo de busca no Dio Never Forgets"""
from dio_search_knowledge import search, format_result

results = search("banco de dados", limit=3)
for r in results:
    print(format_result(r))
