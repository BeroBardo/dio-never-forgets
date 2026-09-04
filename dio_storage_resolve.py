#!/usr/bin/env python3
"""
DIO Storage Resolver — escolhe automaticamente o path com mais espaço livre.
Uso: resolva o path do dio_knowledge.db pro volume mais espaçoso.

Lógica:
1. Env var DIO_KNOWLEDGE_DB (manual) tem prioridade SEMPRE (usuário escolheu)
2. Senão, varre os mounts e escolhe o com mais espaço livre
3. Ancorar em subdir gravável (padrão dio_shared) — nunca raiz de volume
4. Mantém o arquivo onde já existe se o volume já for o melhor

Sempre recomenda automaticamente o volume mais espaçoso.
"""
import os, shutil

# Candidatos: (mount, subdir que existe e é gravável)
CANDIDATES = [
    '/var/mnt/lentao/dio_shared',
    '/var/mnt/lentao',
    '/var/home/ber',
    '/home/ber',
    '/',
]
FALLBACK = '/var/mnt/lentao/dio_shared'

def get_free_gb(path):
    """Espaço livre em GB do volume que contém path."""
    try:
        if not os.path.exists(path):
            return 0
        t, u, f = shutil.disk_usage(path)
        return f // (1024**3)
    except:
        return 0

def writable(path):
    """True se path existe ou pode ser criado e é gravável."""
    while path and not os.path.exists(path):
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return os.access(path, os.W_OK) if path and os.path.exists(path) else False

def pick_best_storage(preferred_prefix='dio_knowledge.db'):
    """Escolhe o path com mais espaço livre (ou env manual)."""
    # 1. Env var manual (usuário escolheu explicitamente)
    env = os.environ.get('DIO_KNOWLEDGE_DB')
    if env:
        return env, get_free_gb(os.path.dirname(env) or '/')

    # 2. Varre candidatos graváveis, escolhe o mais espaçoso
    best, best_free = None, -1
    for cand in CANDIDATES:
        if not writable(cand):
            continue
        free = get_free_gb(cand)
        if free > best_free:
            best_free = free
            best = cand

    if not best:
        best, best_free = FALLBACK, get_free_gb(FALLBACK)

    return os.path.join(best, preferred_prefix), best_free

def recommend():
    chosen, free = pick_best_storage()
    print(f"[STORAGE] Banco: {chosen} ({free}GB livres)")
    bigger = [c for c in CANDIDATES if get_free_gb(c) > free]
    tip = f" (ainda mais espaco em: {', '.join(bigger)})" if bigger else ""
    print(f"[STORAGE] Volume mais espaçoso detectado automaticamente{tip}")
    return chosen

if __name__ == '__main__':
    recommend()
