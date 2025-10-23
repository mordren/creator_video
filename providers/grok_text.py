# providers/grok_text.py
import ast
import os
import json
import re
import requests
from typing import Dict, Any
from .base_texto import TextoProvider, register_provider


@register_provider("grok_text")
class GrokTextProvider(TextoProvider):
    """Provider para xAI Grok — gera JSON limpo e estruturado (compatível com base_texto.py)."""

    def __init__(self):
        self.api_key = os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ XAI_API_KEY não encontrada no .env")
        self.endpoint = "https://api.x.ai/v1/chat/completions"
        self.model_name = "grok-4-fast-reasoning"

    def _clean_json_response(self, text: str) -> Dict[str, Any]:
        import json, ast, re
        print(f"🧹 Limpando resposta Grok... ({len(text)} chars)")

        # Remove blocos markdown e caracteres ocultos
        text = re.sub(r'^```(?:json)?|```$', '', text.strip(), flags=re.IGNORECASE)
        text = re.sub(r'[\x00-\x1f\x7f]', '', text)

        # 1️⃣ Caso típico: resposta é uma string Python com JSON dentro
        try:
            # tenta avaliar literalmente (converte aspas simples em objeto Python)
            maybe = ast.literal_eval(text)
            # se for string e começar com {, tenta decodificar de fato
            if isinstance(maybe, str) and maybe.strip().startswith("{"):
                maybe = json.loads(maybe)
            if isinstance(maybe, dict):
                print("✅ JSON extraído via ast.literal_eval")
                return maybe
        except Exception:
            pass

        # 2️⃣ Caso direto: o texto já é JSON normal
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                print("✅ JSON extraído diretamente")
                return data
        except Exception:
            pass

        # 3️⃣ Fallback final
        print("❌ Falha ao extrair JSON, retornando fallback simples")
        return {
            "texto": text[:2000],
            "titulo": "Reflection | Prayer",
            "descricao": "A short reflection and prayer.",
            "thumb": "prayer peace reflection",
            "tags": ["#Prayer", "#Faith", "#Peace"]
        }


    def generate(self, prompt: str) -> Dict[str, Any]:
        """Envia prompt pro Grok e retorna JSON limpo."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "Return ONLY valid JSON, no markdown, no explanations."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "top_p": 0.9,
        }

        try:
            print("🚀 Enviando prompt pro Grok...")
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=120)
            if resp.status_code != 200:
                raise RuntimeError(f"Grok retornou {resp.status_code}: {resp.text}")

            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            return self._clean_json_response(text)

        except Exception as e:
            print(f"❌ Erro Grok API: {e}")
            return {
                "texto": f"Erro: {e}",
                "titulo": "Grok Error",
                "descricao": "Falha ao gerar texto com Grok.",
                "hook": "Retry later.",
                "hook_pt": "Tente novamente mais tarde.",
                "thumb": "error",
                "tags": ["#Error"]
            }
