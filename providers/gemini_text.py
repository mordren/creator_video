# providers/gemini_text.py
import os
import json
import re
import google.generativeai as genai
from typing import Dict, Any
from .base_texto import TextoProvider, register_provider

@register_provider("gemini_text")
class GeminiTextProvider(TextoProvider):
    """Provider para Google Gemini com JSON limpo e sem fallback"""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente")
        genai.configure(api_key=self.api_key)
        self.model_name = model or "gemini-2.0-flash"

    # === Limpeza e extração JSON ===
    def _clean_json_response(self, text: str) -> Dict[str, Any]:
        """
        Limpa e extrai JSON da resposta do modelo (robusto para Gemini, Grok, etc.)
        Suporta blocos markdown, aspas externas, escapes e strings Python com JSON dentro.
        """
        import json, ast, re

        print(f"🧹 Limpando resposta... ({len(text)} chars)")

        # Remove blocos ```json e ``` simples
        text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
        text = re.sub(r"```$", "", text)
        text = re.sub(r"[\x00-\x1f\x7f]", "", text)  # remove caracteres de controle

        # Remove quebras de linha duplicadas e espaços inúteis
        text = text.strip()

        # Caso 1: JSON puro
        try:
            return json.loads(text)
        except Exception:
            pass

        # Caso 2: JSON dentro de aspas (duplas ou simples)
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        text = text.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")

        try:
            return json.loads(text)
        except Exception:
            pass

        # Caso 3: JSON dentro de string Python
        try:
            maybe = ast.literal_eval(text)
            if isinstance(maybe, str) and maybe.strip().startswith("{"):
                return json.loads(maybe)
            if isinstance(maybe, dict):
                return maybe
        except Exception:
            pass

        # Caso 4: JSON dentro de bloco markdown interno
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        # Se falhar tudo, loga o problema
        print("❌ Falha ao decodificar JSON — conteúdo parcial:")
        print(text[:500] + ("..." if len(text) > 500 else ""))
        raise ValueError("❌ Nenhum JSON válido encontrado na resposta.")


    # === Geração ===
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Gera texto com o Gemini e retorna JSON limpo"""
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        if not response or not response.text:
            raise ValueError("Resposta vazia do Gemini")

        return self._clean_json_response(response.text)
