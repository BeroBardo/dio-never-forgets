#!/usr/bin/env python3
"""
Dio Never Forgets — Setup Interativo
====================================
"O mundo foi feito para ser governado por mim... e esse banco de dados também."

Roda a configuração inicial do Dio Never Forgets com a PERSONA do DIO.
Detecta o idioma do PC automaticamente.
Configura caminhos, auto-detecção de storage, e agendador cron real.
"""
import os, shutil, sys, configparser, locale, subprocess
from pathlib import Path

# --- Idioma ---
def detect_lang():
    """Detecta idioma do sistema (locale). Retorna 'pt' ou 'en'."""
    try:
        loc, _ = locale.getdefaultlocale()
        if loc and loc.startswith('pt'):
            return 'pt'
    except Exception:
        pass
    env = os.environ.get('LANG', os.environ.get('LC_ALL', '')).lower()
    if env.startswith('pt'):
        return 'pt'
    return 'en'

LANG = detect_lang()

# --- Storage Resolver Helpers ---
def get_free_gb(path):
    try:
        p = Path(path)
        while p and not p.exists():
            if p.parent == p:
                break
            p = p.parent
        t, u, f = shutil.disk_usage(str(p))
        return f // (1024**3)
    except Exception:
        return 0

def writable(path):
    p = Path(path)
    while p and not p.exists():
        if p.parent == p:
            break
        p = p.parent
    return p.exists() and os.access(str(p), os.W_OK)

def detect_volumes():
    volumes = []
    # 1. Diretório home
    home = str(Path.home())
    if writable(home):
        volumes.append((home, get_free_gb(home)))
    # 2. Raiz
    if writable('/'):
        volumes.append(('/', get_free_gb('/')))
    # 3. Pontos de montagem comuns
    for base in ['/media', '/mnt', '/var/mnt']:
        b = Path(base)
        if b.exists():
            try:
                for entry in b.iterdir():
                    if entry.is_dir() and writable(str(entry)):
                        volumes.append((str(entry), get_free_gb(str(entry))))
            except Exception:
                pass
    # Deduplicar
    seen = set()
    uniq = []
    for p, gb in volumes:
        try:
            dev = os.stat(p).st_dev
        except Exception:
            dev = p
        if dev not in seen:
            seen.add(dev)
            uniq.append((p, gb))
    uniq.sort(key=lambda x: x[1], reverse=True)
    return uniq

def detect_state_db():
    candidates = [
        Path.home() / '.hermes' / 'state.db',
        Path('/run/media/system/HERMES/.hermes/state.db'),
        Path('/var/home/ber/.hermes/state.db'),
        Path.cwd() / 'state.db',
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return ""

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
        'q_statedb': "  Onde está o banco principal do Hermes (state.db)?",
        'q_install': "  Onde devo instalar e manter a configuração do Dio?",
        'q_db': "  Onde devo guardar o banco de conhecimento leve (dio_knowledge.db)?",
        'q_cron': "  Quer agendar a re-extração automática semanal no cron?",
        'q_cron_opts': [
            "Sim, recomendo (todo domingo 03:00 no crontab)",
            "Não, farei isso manualmente",
        ],
        'q_auto': "  Sempre recomendar o volume com mais espaço livre?",
        'q_auto_opts': [
            "Sim (recomendado)",
            "Não, usar sempre o mesmo local",
        ],
        'q_custom': "  Digite o caminho completo:",
        'saved': "  ZA WARUDO! Config salva em: {path}",
        'saved_fallback': "  MUDA! Sem permissão em {path}. Salvando em ./dio.conf...",
        'cron_installed': "  [CRON] Agendamento inserido com sucesso no crontab!",
        'cron_failed': "  [CRON] Não foi possível atualizar o crontab automaticamente.",
        'done': [
            "  PRONTO.",
            "  Sua memória agora pertence a você, eterna.",
            "  Rodou tudo certo? Uso:",
            "",
            "    python3 {dir}/dio_extract_knowledge.py",
            "    python3 {dir}/dio_search_knowledge.py 'sua busca'",
            "",
            "  WRYYYYYYYYY! Nunca esqueça: o mundo foi feito para ser governado por mim.",
        ],
        'hint': "  (digite 1-{n})",
        'muda': "  MUDA! Isso não serve. Vou perguntar de novo.",
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
        'q_statedb': "  Where is Hermes's main database (state.db)?",
        'q_install': "  Where should I install and keep Dio configuration?",
        'q_db': "  Where should I store the lightweight knowledge database (dio_knowledge.db)?",
        'q_cron': "  Enable automatic weekly rebuild in cron?",
        'q_cron_opts': [
            "Yes, recommended (every Sunday 03:00 in crontab)",
            "No, I will run it manually",
        ],
        'q_auto': "  Always recommend the volume with most free space?",
        'q_auto_opts': [
            "Yes (recommended)",
            "No, always use the same location",
        ],
        'q_custom': "  Enter the full path:",
        'saved': "  ZA WARUDO! Config saved to: {path}",
        'saved_fallback': "  MUDA! No permission in {path}. Saving to ./dio.conf...",
        'cron_installed': "  [CRON] Scheduled task added to crontab successfully!",
        'cron_failed': "  [CRON] Could not update crontab automatically.",
        'done': [
            "  DONE.",
            "  Your memory now belongs to you, eternal.",
            "  All good? Usage:",
            "",
            "    python3 {dir}/dio_extract_knowledge.py",
            "    python3 {dir}/dio_search_knowledge.py 'your query'",
            "",
            "  WRYYYYYYYYY! Never forget: the world was made to be ruled by me.",
        ],
        'hint': "  (enter 1-{n})",
        'muda': "  MUDA! That won't do. I'll ask again.",
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
        mark = " (recomendado)" if (i-1 == default and LANG=='pt') else (" (recommended)" if i-1 == default else "")
        print(f"    [{i}] {c}{mark}")
    while True:
        try:
            r = input("  > ").strip()
            if not r:
                return default
            val = int(r)
            if 1 <= val <= len(choices):
                return val - 1
            raise ValueError
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {'> ZA WARUDO! Setup cancelado.' if LANG=='pt' else '> ZA WARUDO! Setup cancelled.'}")
            sys.exit(0)
        except Exception:
            print(t('muda'))
            print(f"    {t('hint', n=len(choices))}")

def install_cron(script_dir):
    """Adiciona cronjob semanal no crontab do usuário se não existir."""
    job_cmd = f"0 3 * * 0 cd {script_dir} && python3 dio_extract_knowledge.py >/dev/null 2>&1"
    try:
        curr = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        lines = curr.stdout.splitlines() if curr.returncode == 0 else []
        if any('dio_extract_knowledge.py' in l for l in lines):
            return True
        lines.append(job_cmd)
        new_cron = '\n'.join(lines) + '\n'
        proc = subprocess.run(['crontab', '-'], input=new_cron, text=True, capture_output=True)
        return proc.returncode == 0
    except Exception:
        return False

def setup():
    banner()
    vols = detect_volumes()
    best_path, best_free = vols[0] if vols else (str(Path.home()), get_free_gb(str(Path.home())))
    print(t('detect', path=best_path, gb=best_free))
    print()

    # 1. State DB
    state_detected = detect_state_db()
    warudo_msg = '> ZA WARUDO! O tempo parou... só pra você decidir.' if LANG=='pt' else '> ZA WARUDO! The world stopped... just for you to decide.'
    print(warudo_msg)
    if state_detected:
        st_opts = [
            f"{state_detected} (detectado)",
            "Outro caminho manual" if LANG=='pt' else "Other path (manual)"
        ]
        ch_st = ask(t('q_statedb'), st_opts, default=0)
        if ch_st == 0:
            state_db_path = state_detected
        else:
            state_db_path = input(f"  {t('q_custom')} ").strip() or state_detected
    else:
        state_db_path = input(f"  {t('q_statedb')} ({t('q_custom')}) ").strip()

    # 2. Install dir (onde salvar dio.conf e scripts)
    current_dir = str(Path(__file__).resolve().parent)
    inst_opts = [
        f"Diretório atual ({current_dir})" if LANG=='pt' else f"Current directory ({current_dir})",
        str(Path.home() / '.config' / 'dio'),
        "Outro diretório" if LANG=='pt' else "Other directory"
    ]
    print()
    ch_inst = ask(t('q_install'), inst_opts, default=0)
    if ch_inst == 0:
        install_dir = current_dir
    elif ch_inst == 1:
        install_dir = str(Path.home() / '.config' / 'dio')
    else:
        install_dir = input(f"  {t('q_custom')} ").strip() or current_dir

    # 3. Database Path
    db_opts = [
        f"{best_path}/dio_knowledge.db ({best_free}GB livres)" if LANG=='pt' else f"{best_path}/dio_knowledge.db ({best_free}GB free)",
        f"{install_dir}/dio_knowledge.db",
        "Outro local" if LANG=='pt' else "Other location"
    ]
    print()
    ch_db = ask(t('q_db'), db_opts, default=0)
    if ch_db == 0:
        db_path = f"{best_path}/dio_knowledge.db"
    elif ch_db == 1:
        db_path = f"{install_dir}/dio_knowledge.db"
    else:
        db_path = input(f"  {t('q_custom')} ").strip() or f"{best_path}/dio_knowledge.db"

    # 4. Cron rebuild
    print()
    ch_cron = ask(t('q_cron'), t('q_cron_opts'), default=0)
    cron_enabled = (ch_cron == 0)

    # 5. Auto storage recommendation
    print()
    ch_auto = ask(t('q_auto'), t('q_auto_opts'), default=0)
    auto_enabled = (ch_auto == 0)

    # Salvar dio.conf
    cfg = configparser.ConfigParser()
    cfg['dio'] = {
        'install_dir': install_dir,
        'state_db': state_db_path,
        'database': db_path,
        'auto_recomend_storage': str(auto_enabled).lower(),
        'cron_rebuild': str(cron_enabled).lower(),
        'lang': LANG,
        'installed_at': __import__('time').strftime('%Y-%m-%d %H:%M'),
    }

    cfg_file = Path(install_dir) / 'dio.conf'
    try:
        Path(install_dir).mkdir(parents=True, exist_ok=True)
        with open(cfg_file, 'w') as f:
            cfg.write(f)
        print(f"\n{t('saved', path=cfg_file)}")
    except Exception:
        fallback_file = Path.cwd() / 'dio.conf'
        with open(fallback_file, 'w') as f:
            cfg.write(f)
        print(f"\n{t('saved_fallback', path=install_dir)}")
        print(f"{t('saved', path=fallback_file)}")

    # Executar Cron se solicitado
    if cron_enabled:
        ok = install_cron(current_dir)
        if ok:
            print(t('cron_installed'))
        else:
            print(t('cron_failed'))

    # Final
    print()
    print("="*60)
    for line in t('done', dir=current_dir):
        print(line)
    print("="*60)
    print()

if __name__ == '__main__':
    setup()
