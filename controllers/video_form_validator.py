# video_form_validator.py
from typing import Any, Dict
from crud.models import StatusUpload  # ajuste o caminho se seus pacotes tiverem prefixo

_TRUEY = {"true", "1", "on", "yes", "y", "sim"}

def _clean_str(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None

def _to_bool(val: Any) -> bool:
    if val is None:
        return False
    return str(val).strip().lower() in _TRUEY

def _to_int(val: Any) -> int | None:
    if val is None:
        return None
    s = str(val).strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        return None

def _to_status(val: Any) -> StatusUpload | None:
    s = _clean_str(val)
    if s is None:
        return None
    # valores válidos: rascunho, enviando, publicado, erro
    # (definidos no Enum StatusUpload) 
    try:
        return StatusUpload(s)
    except ValueError:
        raise ValueError(f"status_upload inválido: {s!r}")

def _prune(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None e strings vazias; mantém False e 0."""
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, str) and v == "":
            continue
        out[k] = v
    return out

class VideoFormValidator:
    """
    Única porta de entrada para parse/validação do formulário.
    Retorna UM dicionário 'roteiro_data' com todos os campos do modelo Roteiro.
    """
    @staticmethod
    def validate_and_extract(form_data: Dict[str, Any]) -> Dict[str, Any]:
        titulo = _clean_str(form_data.get("titulo"))
        if not titulo:
            raise ValueError("Título é obrigatório")

        roteiro_data: Dict[str, Any] = {
            # básicos
            "titulo": titulo,
            "id_video": _clean_str(form_data.get("id_video")),
            "texto": _clean_str(form_data.get("texto")),
            "descricao": _clean_str(form_data.get("descricao")),
            "tags": _clean_str(form_data.get("tags")),
            "thumb": _clean_str(form_data.get("thumb")),
            # flags
            "audio_gerado": _to_bool(form_data.get("audio_gerado")),
            "video_gerado": _to_bool(form_data.get("video_gerado")),
            "finalizado": _to_bool(form_data.get("finalizado")),
            # “campos de vídeo” que agora moram no Roteiro
            "status_upload": _to_status(form_data.get("status_upload")),
            "duracao": _to_int(form_data.get("duracao")),
            "tts_provider": _clean_str(form_data.get("tts_provider")),
            "voz_tts": _clean_str(form_data.get("voz_tts")),
            "visualizacao_total": _to_int(form_data.get("visualizacao_total")) or 0,
            "arquivo_audio": _clean_str(form_data.get("arquivo_audio")),
            "arquivo_video": _clean_str(form_data.get("arquivo_video")),
            "arquivo_legenda": _clean_str(form_data.get("arquivo_legenda")),
            "audio_mixado": _clean_str(form_data.get("audio_mixado")),
            # opcionais adicionais do modelo
            "resolucao": _clean_str(form_data.get("resolucao")),
        }

        return _prune(roteiro_data)
