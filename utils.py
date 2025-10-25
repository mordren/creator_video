# utils.py
from pathlib import Path
import json, re
from typing import Any, Dict

# tokenização de "palavra" robusta (acentos + hífen/contração)
_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:[-''][A-Za-zÀ-ÖØ-öø-ÿ0-9]+)?", re.UNICODE)

def count_words(s: str) -> int:
    """Conta palavras de forma robusta, incluindo acentos e hífens"""
    return len(_WORD.findall(re.sub(r"\s+", " ", s.strip())))

def truncate_words(s: str, n: int) -> str:
    """Trunca texto por número de palavras"""
    out, seen = [], 0
    for chunk in re.split(r"(\W+)", s):
        if _WORD.fullmatch(chunk):
            if seen >= n: 
                break
            seen += 1
        out.append(chunk)
    return "".join(out).strip()

def extract_json_maybe(text: str) -> dict:
    """
    Função simplificada apenas para compatibilidade
    O processamento principal agora está no gemini_text.py
    """
    if isinstance(text, dict):
        return text
    
    # Se for string, tenta fazer parse direto (para outros providers)
    try:
        return json.loads(text)
    except:
        # Fallback básico
        return {
            "texto": str(text)[:1000],
            "titulo": "Generated Content",
            "descricao": "Automatically generated content",
            "hook": "Default hook",
            "hook_pt": "Hook padrão", 
            "thumb": "default",
            "tags": ["#default"]
        }

def save_json(dados: Dict[str, Any], out_dir: Path) -> Path:
    """Salva dados em arquivo JSON"""
    out_dir.mkdir(parents=True, exist_ok=True)
    _id = (dados.get("id") or "tmp").lstrip("#") or "tmp"
    path = out_dir / f"{_id}.json"
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return path

def criar_pasta_roteiro(pasta_base: Path, id_video: str) -> Path:
    """
    Cria pasta para o roteiro baseado no ID do vídeo
    
    Args:
        pasta_base: Pasta base dos vídeos (ex: E:\Canal Dark\Vídeos Automáticos)
        id_video: ID único do vídeo
    
    Returns:
        Path: Caminho da pasta criada
    """
    pasta_roteiro = pasta_base / id_video
    pasta_roteiro.mkdir(parents=True, exist_ok=True)
    return pasta_roteiro

def save_json_completo(dados: dict, pasta_roteiro: Path):
    """
    Salva arquivos JSON e TXT do roteiro na pasta especificada
    
    Args:
        dados: Dados do roteiro
        pasta_roteiro: Pasta onde salvar os arquivos
    
    Returns:
        tuple: (caminho_json, caminho_txt)
    """
    id_video = dados["id_video"]
    
    # Salva JSON com metadados
    caminho_json = pasta_roteiro / f"{id_video}.json"
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    # Salva texto em arquivo .txt
    caminho_txt = pasta_roteiro / f"{id_video}.txt"
    texto_pt = dados.get("texto_pt", dados.get("texto", ""))
    with open(caminho_txt, 'w', encoding='utf-8') as f:
        f.write(texto_pt)
    
    return caminho_json, caminho_txt

def obter_proximo_id(pasta_base: Path) -> str:
    """Obtém o próximo ID sequencial baseado nas pastas existentes"""
    if not pasta_base.exists():
        return "1"
    
    ids_existentes = []
    for item in pasta_base.iterdir():
        if item.is_dir() and item.name.isdigit():
            try:
                ids_existentes.append(int(item.name))
            except ValueError:
                continue
    
    proximo_id = max(ids_existentes) + 1 if ids_existentes else 1
    return str(proximo_id)

def vertical_horizontal(resolucao: str) -> str:
    """Determina se a resolução é vertical ou horizontal"""
    return "vertical" if resolucao == "720x1280" else "horizontal"

def clean_json_response(text: str) -> Dict[str, Any]:
    """
    Limpa e extrai JSON da resposta do modelo (robusto para Gemini, Grok, etc.)
    Versão standalone da função que estava no gemini_text.py
    """
    import ast
    
    # Remove blocos ```json e ``` simples
    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"```$", "", text)
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)  # remove caracteres de controle
    text = text.strip()

    # PRÉ-PROCESSAMENTO: Corrige escapes problemáticos
    text = re.sub(r"(?<!\\)\\'", "'", text)
    text = re.sub(r'(?<![\\"])"(?![\\"])', '"', text)
    text = text.replace('\\\\', '\\')

    # Caso 1: JSON puro
    try:
        return json.loads(text)
    except Exception:
        pass

    # Caso 2: JSON dentro de aspas
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        unquoted_text = text[1:-1]
        unquoted_text = unquoted_text.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")
        try:
            return json.loads(unquoted_text)
        except Exception:
            try:
                return json.loads(unquoted_text)
            except Exception:
                pass

    # Caso 3: JSON dentro de string Python
    try:
        maybe = ast.literal_eval(text)
        if isinstance(maybe, str):
            cleaned_str = re.sub(r"(?<!\\)\\'", "'", maybe)
            try:
                return json.loads(cleaned_str)
            except Exception:
                match = re.search(r'\{[\s\S]*\}', cleaned_str)
                if match:
                    return json.loads(match.group(0))
        elif isinstance(maybe, dict):
            return maybe
    except Exception:
        pass

    # Caso 4: Reparação avançada
    try:
        repaired = re.sub(r"'([^']*)'", r'"\1"', text)
        repaired = re.sub(r"\[\s*'([^']*)'\s*\]", r'["\1"]', repaired)
        repaired = re.sub(r"\[\s*'([^']*)',\s*'([^']*)'\s*\]", r'["\1", "\2"]', repaired)
        return json.loads(repaired)
    except Exception:
        pass

    # Caso 5: Extração por regex
    try:
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                cleaned_match = re.sub(r"(?<!\\)\\'", "'", match)
                cleaned_match = re.sub(r'\s+', ' ', cleaned_match)
                return json.loads(cleaned_match)
            except Exception:
                continue
    except Exception:
        pass

    # Caso 6: Extração por linhas
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
            json_text = re.sub(r"(?<!\\)\\'", "'", json_text)
            return json.loads(json_text)
    except Exception:
        pass

    raise ValueError(f"Não foi possível extrair JSON válido da resposta: {text[:200]}...")