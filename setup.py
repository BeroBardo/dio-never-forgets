#!/usr/bin/env python3
"""
Dio Never Forgets — Setup Interativo
====================================
"O mundo foi feito para ser governado por mim... e esse banco de dados também."

Roda a configuração inicial do Dio Never Forgets com a PERSONA do DIO.
Detecta o idioma do PC automaticamente.
"""
import os, shutil, sys, configparser, locale
from pathlib import Path

# --- Idioma ---
def detect_lang():
    """Detecta idioma do sistema (locale). Retorna 'pt' ou 'en'."""
    try:
        loc, _ = locale.getdefaultlocale()
        if loc and loc.startswith('pt'):
            return 'pt'
    except:
        pass
    env = os.environ.get('LANG', os.environ.get('LC_ALL', '')).lower()
    if env.startswith('pt'):
        return 'pt'
    return 'en'

LANG = detect_lang()

# --- Textos ---
T = {
    'pt': {
        'banner': [
            "="*60,
            "  KONO DIO DA!",
            "  Bem-vindo ao Dio Never Forgets.",
            "  Memória eterna, como convém a um deus.",
            "="*60,
        ],
        'intro': [
            "  Hoje você acorda como o dono de uma memória eterna.",
            "  Antes de eu transformar seus dados em poder, preciso de algumas respostas.",
        ],
        'detect': "  [STORAGE] Detectei o volume mais espaçoso: {path} ({gb}GB livres)",
        'q_install': "  Onde devo instalar os scripts do Dio Never Forgets?",
        'q_install_opts': [
            "{path} (recomendado, {gb}GB livres)",
            "~/dio-never-forgets",
            "Diretório atual (./dio-never-forgets)",
            "Outro diretório",
        ],
        'q_db': "  Onde devo guardar o banco de conhecimento (dio_knowledge.db)?",
        'q_db_opts': [
            "{path}/dio_knowledge.db (recomendado, {gb}GB livres)",
            "Perto dos scripts (mesma pasta)",
            "Outro local",
        ],
        'q_cron': "  Quer re-extração automática semanal do banco?",
        'q_cron_opts': [
            "Sim, recomendo (todo domingo 03:00)",
            "Não, me avise quando precisar",
        ],
        'q_auto': "  Sempre recomendar o volume com mais espaço livre?",
        'q_auto_opts': [
            "Sim (recomendado)",
            "Não, usar sempre o mesmo local",
        ],
        'q_custom': "  Digite o caminho completo:",
        'saved': "  ZA WARUDO! Config salva em: {path}",
        'saved_fallback': "  MUDA! Sem permissão em {path}. Salvando em ./dio.conf...",
        'done': [
            "  PRONTO.",
            "  Sua memória agora pertence a você, eterna.",
            "  Rodou tudo certo? Uso:",
            "",
            "    export DIO_KNOWLEDGE_DB={db}",
            "    python3 {dir}/dio_extract_knowledge.py",
            "    python3 {dir}/dio_search_knowledge.py 'sua busca'",
            "",
            "  WRYYYYYYYYY! Nunca esqueça: o mundo foi feito para ser governado por mim.",
        ],
        'hint': "  (digite 1-{n})",
        'muda': "  MUDA! Isso não serve. Vou perguntar de novo.",
        'other': "  Outro",
    },
    'en': {
        'banner': [
            "="*60,
            "  KONO DIO DA!",
            "  Welcome to Dio Never Forgets.",
            "  Eternal memory, as befitting a god.",
            "="*60,
        ],
        'intro': [
            "  You wake today as the owner of an eternal memory.",
            "  Before I turn your data into power, I need a few answers.",
        ],
        'detect': "  [STORAGE] Detected most spacious volume: {path} ({gb}GB free)",
        'q_install': "  Where should I install the Dio Never Forgets scripts?",
        'q_install_opts': [
            "{path} (recommended, {gb}GB free)",
            "~/dio-never-forgets",
            "Current directory (./dio-never-forgets)",
            "Other directory",
        ],
        'q_db': "  Where should I store the knowledge database (dio_knowledge.db)?",
        'q_db_opts': [
            "{path}/dio_knowledge.db (recommended, {gb}GB free)",
            "Same folder as scripts",
            "Other location",
        ],
        'q_cron': "  Enable automatic weekly database rebuild?",
        'q_cron_opts': [
            "Yes, recommended (every Sunday 03:00)",
            "No, notify me when needed",
        ],
        'q_auto': "  Always recommend the volume with most free space?",
        'q_auto_opts': [
            "Yes (recommended)",
            "No, always use the same location",
        ],
        'q_custom': "  Enter the full path:",
        'saved': "  ZA WARUDO! Config saved to: {path}",
        'saved_fallback': "  MUDA! No permission in {path}. Saving to ./dio.conf...",
        'done': [
            "  DONE.",
            "  Your memory now belongs to you, eternal.",
            "  All good? Usage:",
            "",
            "    export DIO_KNOWLEDGE_DB={db}",
            "    python3 {dir}/dio_extract_knowledge.py",
            "    python3 {dir}/dio_search_knowledge.py 'your query'",
            "",
            "  WRYYYYYYYYY! Never forget: the world was made to be ruled by me.",
        ],
        'hint': "  (enter 1-{n})",
        'muda': "  MUDA! That won't do. I'll ask again.",
        'other': "  Other",
    },
}

def t(key, **kw):
    s = T[LANG].get(key, key)
    if kw:
        return s.format(**kw)
    return s

def banner():
    print()
    for line in t('banner'):
        print(line)
    print()
    for line in t('intro'):
        print(line)
    print()

def ask(question, choices, default=0):
    print(f"  {question}")
    for i, c in enumerate(choices, 1):
        mark = " (recommended)" if i-1 == default else ""
        print(f"    [{i}] {c}{mark}")
    while True:
        try:
            r = input("  > ").strip()
            if not r:
                return default
            r = int(r)
            if 1 <= r <= len(choices):
                return r-1
            raise ValueError
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {'> ZA WARUDO! Setup cancelled. Run again anytime.' if LANG=='en' else '> ZA WARUDO! Setup cancelado. Rode de novo quando quiser.'}")
            sys.exit(0)
        except:
            print(t('muda'))
            print(f"    {t('hint', n=len(choices))}")

# --- Storage ---
CANDIDATES = ['/var/mnt/lentao/dio_shared', '/var/mnt/lentao',
              str(Path.home()), '/home', '/var/home/ber']

def free_gb(p):
    try:
        if not os.path.exists(p):
            return 0
        t, u, f = shutil.disk_usage(p)
        return f // (1024**3)
    except:
        return 0

def pick_best():
    best, best_free = None, -1
    for c in CANDIDATES:
        f = free_gb(c)
        if f > best_free:
            best_free, best = f, c
    return best, best_free

def setup():
    banner()
    best, bf = pick_best()
    print(t('detect', path=best, gb=bf))
    print()

    # 1. Install dir
    opts = [o.format(path=best, gb=bf) for o in t('q_install_opts')]
    wh = ask(t('q_install'), opts)
    locs = [best, str(Path.home() / 'dio-never-forgets'), './dio-never-forgets', '']
    install_dir = locs[wh]

    # 2. Database path
    opts2 = [o.format(path=best, gb=bf) for o in t('q_db_opts')]
    print()
    warudo_line = '> ZA WARUDO! The world stopped... just for you to decide.' if LANG=='en' else '> ZA WARUDO! O tempo parou... só pra você decidir.'
    print(warudo_line)
    wh2 = ask(t('q_db'), opts2)
    if wh2 == 0:
        db_path = f"{best}/dio_knowledge.db"
    elif wh2 == 1:
        db_path = f"{install_dir}/dio_knowledge.db"
    else:
        print()
        db_path = input(f"  {t('q_custom')} ").strip()
        if not db_path:
            db_path = f"{best}/dio_knowledge.db"

    # 3. Cron rebuild
    print()
    print(warudo_line)
    wh3 = ask(t('q_cron'), t('q_cron_opts'))
    cron = wh3 == 0

    # 4. Auto storage recommendation
    print()
    wh4 = ask(t('q_auto'), t('q_auto_opts'))
    auto = wh4 == 0

    # Write config
    cfg = configparser.ConfigParser()
    cfg['dio'] = {
        'install_dir': install_dir,
        'database': db_path,
        'auto_recomend_storage': str(auto).lower(),
        'cron_rebuild': str(cron).lower(),
        'lang': LANG,
        'installed_at': __import__('time').strftime('%Y-%m-%d %H:%M'),
        'mode': 'setup-pelas-maos-do-dono',
    }
    cfg_path = Path(os.path.join(install_dir, 'dio.conf'))
    try:
        if not os.path.exists(install_dir):
            os.makedirs(install_dir, exist_ok=True)
        with open(cfg_path, 'w') as f:
            cfg.write(f)
        print(f"\n  {t('saved', path=cfg_path)}")
    except (PermissionError, OSError):
        cfg_path = Path('./dio.conf')
        with open(cfg_path, 'w') as f:
            cfg.write(f)
        print(f"\n  {t('saved_fallback', path=install_dir)}")
        print(f"  {t('saved', path=cfg_path)}")

    # Done
    print()
    print("="*60)
    for line in t('done', db=db_path, dir=install_dir):
        print(line)
    print("="*60)
    print()

if __name__ == '__main__':
    setup()
