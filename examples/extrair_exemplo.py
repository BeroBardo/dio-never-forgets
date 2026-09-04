#!/usr/bin/env python3
"""Exemplo de extração"""
import os
os.environ['HERMES_STATE_DB'] = '/caminho/para/state.db'
os.environ['DIO_KNOWLEDGE_DB'] = 'dio_knowledge.db'
from dio_extract_knowledge import build_knowledge_db
build_knowledge_db()
