"""Evidencia reproduzivel: executa verificacoes sem ler o .env real ou usar rede."""
import os
from pathlib import Path
import runpy
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
REAL_ENV = ROOT / '.env'
sys.dont_write_bytecode = True


def guard(event, args):
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        if Path(os.fsdecode(args[0])).resolve() == REAL_ENV:
            raise PermissionError('Leitura do .env real bloqueada pela verificacao')
    if event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo', 'socket.sendto', 'subprocess.Popen', 'os.system'):
        raise PermissionError('Rede/subprocesso bloqueado pela verificacao')


sys.addaudithook(guard)
for name in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'EMBEDDING_MODEL', 'LLM_MODEL',
             'DOCS_DIR', 'CHROMA_DIR', 'CHROMA_COLLECTION', 'CHUNK_SIZE', 'CHUNK_OVERLAP', 'TOP_K'):
    os.environ.pop(name, None)
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

import dotenv
original_load = dotenv.load_dotenv

# Evita mensagens de assercao que possam reproduzir valores do exemplo.
for line in (ROOT / '.env.exemple').read_text(encoding='utf-8').splitlines():
    key, sep, value = line.partition('=')
    if sep and key.strip() in ('OPENAI_API_KEY', 'ANTHROPIC_API_KEY') and value.strip():
        raise SystemExit('Verificacao interrompida: exemplo possui chave preenchida; valor omitido.')

mode = sys.argv[1]
with tempfile.TemporaryDirectory(prefix='xperiun_review_') as tmp:
    empty = Path(tmp) / 'empty.env'
    empty.write_text('', encoding='utf-8')

    def safe_load(dotenv_path=None, *args, **kwargs):
        if dotenv_path is None or Path(dotenv_path).resolve() == REAL_ENV:
            dotenv_path = empty
        return original_load(dotenv_path, *args, **kwargs)

    with patch.object(dotenv, 'load_dotenv', safe_load):
        if mode == 'stack':
            sys.argv = [str(ROOT / 'scripts/check_stack.py')]
            runpy.run_path(sys.argv[0], run_name='__main__')
        elif mode == 'tests':
            sys.argv = ['unittest', 'discover', '-s', 'tests', '-v']
            runpy.run_module('unittest', run_name='__main__', alter_sys=True)
        else:
            raise SystemExit('Modo esperado: stack ou tests')
