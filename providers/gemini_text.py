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

        # PRÉ-PROCESSAMENTO: Corrige escapes problemáticos antes de qualquer tentativa
        # Remove escapes desnecessários de aspas simples (o problema principal)
        text = re.sub(r"(?<!\\)\\'", "'", text)
        # Preserva escapes válidos de aspas duplas, mas remove os desnecessários
        text = re.sub(r'(?<![\\"])"(?![\\"])', '"', text)
        # Remove barras invertidas desnecessárias
        text = text.replace('\\\\', '\\')

        # Caso 1: JSON puro (agora com escapes corrigidos)
        try:
            return json.loads(text)
        except Exception as e1:
            print(f"❌ JSON puro falhou: {e1}")

        # Caso 2: JSON dentro de aspas (duplas ou simples)
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            unquoted_text = text[1:-1]
            # Aplica limpeza adicional no texto sem aspas
            unquoted_text = unquoted_text.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")
            try:
                return json.loads(unquoted_text)
            except Exception as e2:
                print(f"❌ JSON com aspas externas falhou: {e2}")
                # Tenta o texto sem aspas como JSON direto
                try:
                    return json.loads(unquoted_text)
                except Exception:
                    pass

        # Caso 3: JSON dentro de string Python
        try:
            maybe = ast.literal_eval(text)
            if isinstance(maybe, str):
                # Se é uma string, tenta extrair JSON dela
                cleaned_str = re.sub(r"(?<!\\)\\'", "'", maybe)
                try:
                    return json.loads(cleaned_str)
                except Exception:
                    # Tenta encontrar JSON dentro da string
                    match = re.search(r'\{[\s\S]*\}', cleaned_str)
                    if match:
                        return json.loads(match.group(0))
            elif isinstance(maybe, dict):
                return maybe
        except Exception as e3:
            print(f"❌ ast.literal_eval falhou: {e3}")

        # Caso 4: Reparação avançada - converte aspas simples em aspas duplas para chaves/valores
        try:
            # Padrão para identificar chaves e valores entre aspas simples
            repaired = re.sub(r"'([^']*)'", r'"\1"', text)
            # Corrige arrays com aspas simples
            repaired = re.sub(r"\[\s*'([^']*)'\s*\]", r'["\1"]', repaired)
            repaired = re.sub(r"\[\s*'([^']*)',\s*'([^']*)'\s*\]", r'["\1", "\2"]', repaired)
            
            return json.loads(repaired)
        except Exception as e4:
            print(f"❌ Reparação avançada falhou: {e4}")

        # Caso 5: Extração por regex robusta
        try:
            # Procura por qualquer objeto JSON, mesmo com formatação ruim
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text, re.DOTALL)
            
            for match in matches:
                try:
                    # Limpa o match encontrado
                    cleaned_match = re.sub(r"(?<!\\)\\'", "'", match)
                    cleaned_match = re.sub(r'\s+', ' ', cleaned_match)  # Normaliza espaços
                    return json.loads(cleaned_match)
                except Exception:
                    continue
        except Exception as e5:
            print(f"❌ Extração por regex falhou: {e5}")

        # Caso 6: Último recurso - tenta carregar linha por linha
        try:
            lines = text.split('\n')
            json_lines = []
            in_json = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('{') or in_json:
                    json_lines.append(line)
                    in_json = True
                if line.endswith('}'):
                    break
            
            if json_lines:
                json_text = ' '.join(json_lines)
                # Aplica limpeza final
                json_text = re.sub(r"(?<!\\)\\'", "'", json_text)
                return json.loads(json_text)
        except Exception as e6:
            print(f"❌ Extração por linhas falhou: {e6}")

        # Se falhar tudo, loga o problema
        print("❌ Falha ao decodificar JSON — conteúdo parcial:")
        print(text[:500] + ("..." if len(text) > 500 else ""))
        raise ValueError("❌ Nenhum JSON válido encontrado na resposta após múltiplas tentativas.")


    # === Geração ===
    def generate(self, prompt: str) -> Dict[str, Any]:
        """Gera texto com o Gemini e retorna JSON limpo"""
        model = genai.GenerativeModel(self.model_name)
        response = model.generate_content(prompt)
        if not response or not response.text:
            raise ValueError("Resposta vazia do Gemini")

        return self._clean_json_response(response.text)
