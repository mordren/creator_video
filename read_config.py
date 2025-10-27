# read_config.py
from __future__ import annotations
import os, re, sys, importlib.util, unicodedata, difflib
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any, Optional, Union

def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def _norm(s: str) -> str:
    s = _strip_accents(s).lower()
    return re.sub(r'[^a-z0-9]+', '', s)

def _resolve_base_canais() -> Path:
    # 1) variavel de ambiente
    env_dir = os.getenv("CANAIS_DIR")
    if env_dir:
        p = Path(env_dir).expanduser().resolve()
        if p.exists():
            return p
    # 2) ./canais relativo a este arquivo
    here = Path(__file__).resolve().parent
    p = (here / "canais").resolve()
    if p.exists():
        return p
    # 3) ./canais do CWD
    p = (Path.cwd() / "canais").resolve()
    if p.exists():
        return p
    return here

def _find_canal_dir_by_name(name: str, base: Path) -> Optional[Path]:
    if not base.exists():
        return None
    # tentativas literais rápidas
    for candidate in (name, name.replace(' ', '_'), name.replace(' ', '-')):
        d = base / candidate
        if d.exists() and d.is_dir():
            return d
    # normalizado (remove acentos/hífens/espacos)
    alvo = _norm(name)
    dirs = [d for d in base.iterdir() if d.is_dir()]
    for d in dirs:
        if _norm(d.name) == alvo:
            return d
    # aproximação
    nomes = [d.name for d in dirs]
    m = difflib.get_close_matches(name, nomes, n=1, cutoff=0.6)
    return (base / m[0]) if m else None

def _as_path(obj: Union[str, Path]) -> Path:
    try:
        return Path(obj).expanduser()
    except Exception:
        return Path(str(obj))

def _deduz_paths(canal_ref: Union[str, Path]) -> tuple[Path, Path]:
    """
    Retorna (canal_dir, config_path):
    - Se canal_ref for caminho p/ config.py → usa direto
    - Se for caminho p/ diretório → usa <dir>/config.py
    - Se for nome lógico → resolve em ./canais/<pasta>/config.py
    """
    p = _as_path(canal_ref)

    # Caso 1: referência direta a arquivo config.py
    if p.suffix.lower() == '.py' and p.name.lower() == 'config.py' and p.exists():
        return p.parent.resolve(), p.resolve()

    # Caso 2: referência a diretório
    if p.exists() and p.is_dir():
        cfg = p / "config.py"
        if cfg.exists():
            return p.resolve(), cfg.resolve()

    # Caso 3: nome lógico do canal → procurar em ./canais
    base = _resolve_base_canais()
    d = _find_canal_dir_by_name(str(canal_ref), base)
    if d and (d / "config.py").exists():
        return d.resolve(), (d / "config.py").resolve()

    # Falhou
    existentes = []
    if base.exists():
        existentes = sorted(d.name for d in base.iterdir() if d.is_dir())
    lista = ", ".join(existentes) if existentes else "(nenhum canal encontrado)"
    raise ValueError(
        f"Não encontrei config para '{canal_ref}'.\n"
        f"Tente passar um caminho absoluto/relativo para o diretório OU para o config.py.\n"
        f"Base de busca: {base}\nCanais disponíveis: {lista}"
    )

def _module_key(config_path: Path) -> str:
    # chave estável por caminho absoluto
    return f"config_{abs(hash(config_path.as_posix()))}"

@lru_cache(maxsize=64)
def carregar_config_canal(canal_ref: Union[str, Path]) -> Dict[str, Any]:
    canal_dir, config_path = _deduz_paths(canal_ref)

    spec = importlib.util.spec_from_file_location(_module_key(config_path), str(config_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[_module_key(config_path)] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)

    cfg: Dict[str, Any] = {
        k: getattr(module, k)
        for k in dir(module)
        if k.isupper() and not k.startswith('_')
    }
    cfg['PASTA_CANAL'] = canal_dir
    cfg['PASTA_BASE'] = Path(getattr(module, 'PASTA_BASE',
                          Path(__file__).resolve().parent.parent / "conteudo_gerado")).resolve()

    print(f"🔧 Config carregada: {canal_dir.name}")
    print(f"📁 PASTA_CANAL: {cfg['PASTA_CANAL']}")
    print(f"📁 PASTA_BASE:  {cfg['PASTA_BASE']}")
    return cfg
