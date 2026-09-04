#!/usr/bin/env python3
"""
DIO Storage Resolver — escolhe automaticamente o path com mais espaço livre.
Lê configuração do dio.conf, env var, e detecta volumes reais do sistema.
"""
import os, shutil, configparser
from pathlib import Path

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
    p = Path(path)
    while p and not p.exists():
        if p.parent == p:
            break
        p = p.parent
    return p.exists() and os.access(p, os.W_OK)

def detect_volumes():
    """Varre pontos de montagem reais do sistema e retorna lista de (path, free_gb) graváveis."""
    volumes = []
    # 1. Raiz sempre
    if writable('/'):
        volumes.append(('/', get_free_gb('/')))
    # 2. /home
    if writable('/home'):
        volumes.append(('/home', get_free_gb('/home')))
    # 3. Diretório do usuário
    home = Path.home()
    if home != Path('/') and writable(str(home)):
        volumes.append((str(home), get_free_gb(str(home))))
    # 4. /media e /mnt (volumes externos)
    for base in ['/media', '/mnt']:
        b = Path(base)
        if b.exists():
            try:
                for entry in b.iterdir():
                    if entry.is_dir() and writable(str(entry)):
                        volumes.append((str(entry), get_free_gb(str(entry))))
            except:
                pass
    # 5. XDG data dir (opcional)
    xdg = os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))
    xdg_p = Path(xdg)
    if xdg_p.exists() and writable(str(xdg_p)):
        volumes.append((str(xdg_p), get_free_gb(str(xdg_p))))
    # Dedupe por device (evita duplicar montagens)
    seen = set()
    uniq = []
    for p, gb in volumes:
        try:
            dev = os.stat(p).st_dev
        except:
            dev = hash(p)
        if dev not in seen:
            seen.add(dev)
            uniq.append((p, gb))
    return uniq

def read_dio_conf():
    """Lê dio.conf do diretório atual, do dir do script, ou do XDG_CONFIG_HOME."""
    search_paths = [
        Path.cwd() / 'dio.conf',
        Path(__file__).parent / 'dio.conf',
        Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'dio' / 'dio.conf',
        Path.home() / '.config' / 'dio' / 'dio.conf',
    ]
    for p in search_paths:
        if p.exists():
            cfg = configparser.ConfigParser()
            cfg.read(p)
            if 'dio' in cfg:
                return dict(cfg['dio']), str(p)
    return {}, None

def pick_best_storage(preferred_prefix='dio_knowledge.db'):
    """Escolhe o path com mais espaço livre. Prioridade: env > dio.conf > auto-detect."""
    # 1. Env var manual (usuário escolheu explicitamente)
    env = os.environ.get('DIO_KNOWLEDGE_DB')
    if env:
        return env, get_free_gb(os.path.dirname(env) or '/')

    # 2. dio.conf (config salvo pelo setup)
    conf, _ = read_dio_conf()
    if conf.get('database'):
        return conf['database'], get_free_gb(os.path.dirname(conf['database']) or '/')

    # 3. Auto-detect: volume gravável com mais espaço
    volumes = detect_volumes()
    if not volumes:
        # Fallback extremo: home do usuário
        home = str(Path.home())
        return os.path.join(home, preferred_prefix), get_free_gb(home)

    best_path, best_free = max(volumes, key=lambda x: x[1])
    return os.path.join(best_path, preferred_prefix), best_free

def recommend():
    chosen, free = pick_best_storage()
    print(f"[STORAGE] Banco: {chosen} ({free}GB livres)")
    volumes = detect_volumes()
    bigger = [p for p, gb in volumes if gb > free]
    tip = f" (ainda mais espaço em: {', '.join(bigger)})" if bigger else ""
    print(f"[STORAGE] Volume mais espaçoso detectado automaticamente{tip}")
    return chosen

if __name__ == '__main__':
    recommend()