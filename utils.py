# utils.py
from pathlib import Path
import json, re
from typing import Any, Dict

# tokenização de "palavra" robusta (acentos + hífen/contração)
_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:[-’'][A-Za-zÀ-ÖØ-öø-ÿ0-9]+)?", re.UNICODE)

def count_words(s: str) -> int:
    return len(_WORD.findall(re.sub(r"\s+", " ", s.strip())))

def truncate_words(s: str, n: int) -> str:
    out, seen = [], 0
    for chunk in re.split(r"(\W+)", s):
        if _WORD.fullmatch(chunk):
            if seen >= n: break
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
    print(f"✅ JSON extraído: {list(data.keys())}")
    return data

def save_json(dados: Dict[str, Any], out_dir: Path) -> Path:
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

def count_words(s: str) -> int:
    return len(re.findall(r"\b\w+(?:'\w+)?\b", s or ""))