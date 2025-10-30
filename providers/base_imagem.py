# providers/base_image.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from typing import Optional, Dict, Any, Type
import requests
from datetime import datetime
from pathlib import Path

@dataclass
class ImageParams:
    width: int = 1280
    height: int = 720
    # ✅ REMOVIDO: quality não é mais suportado
    style: str = "natural"

class ImageProviderError(RuntimeError): ...
class ImageProviderAuthError(ImageProviderError): ...
class ImageProviderRateLimit(ImageProviderError): ...

class ImageProvider(ABC):
    @abstractmethod
    def generate_image(self, prompt: str, params: ImageParams, pasta_video: Path) -> Dict[str, Any]:
        """Gera imagem e retorna dict com: filepath, url, filename, size"""
        raise NotImplementedError

# ====== Registry + Aliases + Factory ======
_IMAGE_PROVIDER_REGISTRY: Dict[str, Type[ImageProvider]] = {}

ALIASES_IMAGE = {
    "grok": "grok_imagem",
    "dalle": "xai_image",
    "openai": "xai_image",
    "stable": "stable_imagem",  # ✅ NOVO ALIAS

}

def register_image_provider(name: str):
    def _wrap(cls: Type[ImageProvider]):
        _IMAGE_PROVIDER_REGISTRY[name] = cls
        return cls
    return _wrap

def resolve_image_name(name: Optional[str]) -> str:
    base = (name or "xai_image").strip()
    return ALIASES_IMAGE.get(base, base)

def make_image_provider(name: Optional[str], **kwargs) -> ImageProvider:
    """Cria uma instância do provider de imagem por nome lógico (com aliases)"""
    resolved = resolve_image_name(name)
    try:
        cls = _IMAGE_PROVIDER_REGISTRY[resolved]
    except KeyError:
        available = list(_IMAGE_PROVIDER_REGISTRY.keys())
        raise ValueError(f"Image provider '{resolved}' não encontrado. Disponíveis: {available}")
    return cls(**kwargs)