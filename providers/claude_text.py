# providers/claude_text.py
import os
import json
import re
import requests
from typing import Dict, Any
from .base_texto import TextoProvider, register_provider


@register_provider("claude_text")
class ClaudeTextProvider(TextoProvider):
    """Provider para Anthropic Claude: retorna JSON estruturado.

    Requer CLAUDE_API_KEY no ambiente (.env).
    """

    def __init__(self, model: str = None, base_url: str = None, api_key: str = None):
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY não encontrada no ambiente (.env)")
        # CORREÇÃO: Usando modelo válido da Anthropic
        self.model_name = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")
        self.base_url = base_url or os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")

    def _clean_json_response(self, text: str) -> Dict[str, Any]:
        # Remove cercas markdown e caracteres de controle
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r"[\x00-\x1f\x7f]", "", text)

        # Tenta JSON direto
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        # Fallback simples
        return {
            "texto": text[:2000],
            "titulo": "Reflexão e Oração",
            "descricao": "Uma breve reflexão com oração.",
            "thumb": "reflexao oracao paz",
            "tags": ["#Fé", "#Paz", "#Reflexão"],
            "hook": "Uma reflexão profunda sobre a vida",  # Campo hook adicionado no fallback
        }

    def generate(self, prompt: str) -> Dict[str, Any]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        url = f"{self.base_url}/messages"
        
        payload = {
            "model": self.model_name,
            "max_tokens": 2000,
            "temperature": 0.7,
            "system": "Responda SOMENTE com JSON válido, sem explicações. Inclua todos os campos solicitados no prompt.",
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            if resp.status_code != 200:
                raise RuntimeError(f"Claude retornou {resp.status_code}: {resp.text}")

            data = resp.json()
            # Claude retorna conteúdo em data["content"][0]["text"] normalmente
            parts = data.get("content", [])
            text = ""
            if parts and isinstance(parts, list):
                # Cada part pode ser {"type": "text", "text": "..."}
                text = "\n".join([p.get("text", "") for p in parts if isinstance(p, dict)])
            else:
                # Fallback para formatos antigos
                text = data.get("completion") or ""

            return self._clean_json_response(text)
        except Exception as e:
            print(f"Erro Claude API: {e}")
            return {
                "texto": f"Erro: {e}",
                "titulo": "Claude Error",
                "descricao": "Falha ao gerar texto com Claude.",
                "thumb": "erro",
                "tags": ["#Error"],
                "hook": "Erro na geração do conteúdo",  # Campo hook adicionado no erro
            }