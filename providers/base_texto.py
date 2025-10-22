# providers/base_texto.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, Type

# ===== Tipos/Exceções =====
@dataclass
class ModelParams:
    temperature: float = 0.7
    top_p: float = 0.9
    max_output_tokens: Optional[int] = 1200
    seed: Optional[int] = None

class ProviderError(RuntimeError): ...
class ProviderAuthError(ProviderError): ...
class ProviderRateLimit(ProviderError): ...
class ProviderBadResponse(ProviderError): ...

class TextoProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, params: ModelParams) -> Dict[str, Any]:
        """Retorna dict com: id, titulo, texto_pt, (descricao), (tags)."""
        raise NotImplementedError

# ====== Registry + Aliases + Factory ======
_PROVIDER_REGISTRY: Dict[str, Type[TextoProvider]] = {}
ALIASES = {
    "gemini": "gemini_text",
    "grok":   "grok_text",
    "claude": "claude_text",
}

def register_provider(name: str):
    """Decorator para registrar providers concretos."""
    def _wrap(cls: Type[TextoProvider]):
        _PROVIDER_REGISTRY[name] = cls
        return cls
    return _wrap

def resolve_name(name: Optional[str]) -> str:
    base = (name or "gemini_text").strip()
    return ALIASES.get(base, base)

def make_provider(name: Optional[str], **kwargs) -> TextoProvider:
    """
    Cria uma instância do provider por nome lógico (com aliases).
    kwargs carrega envs específicos (api_key, model, base_url etc.).
    """
    resolved = resolve_name(name)
    try:
        cls = _PROVIDER_REGISTRY[resolved]
    except KeyError:
        available = list(_PROVIDER_REGISTRY.keys())
        raise ValueError(f"Provider '{resolved}' não encontrado. Disponíveis: {available}")
    return cls(**kwargs)  # type: ignore

# === IMPORTAR PROVIDERS PARA REGISTRO AUTOMÁTICO ===
try:
    from . import gemini_text  # Isso executa o @register_provider
except ImportError as e:
    print(f"⚠️ Aviso: Não foi possível importar gemini_text: {e}")