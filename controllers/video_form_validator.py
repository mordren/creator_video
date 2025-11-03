# validators/video_form_validator.py
from typing import Dict, Any, Tuple

class VideoFormValidator:
    @staticmethod
    def validate_and_extract(form_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Valida e extrai dados do formulário para roteiro e vídeo"""
        
        # Dados do roteiro
        roteiro_data = {
            'titulo': form_data.get('titulo', '').strip(),
            'id_video': form_data.get('id_video', '').strip(),
            'texto': form_data.get('texto', '').strip(),
            'descricao': form_data.get('descricao', '').strip(),
            'tags': form_data.get('tags', '').strip(),
            'audio_gerado': form_data.get('audio_gerado') == 'true',
            'video_gerado': form_data.get('video_gerado') == 'true',
            'finalizado': form_data.get('finalizado') == 'true'
        }
        
        # Validação básica
        if not roteiro_data['titulo']:
            raise ValueError("Título é obrigatório")
        
        # Dados do vídeo
        duracao = form_data.get('duracao')
        visualizacao_total = form_data.get('visualizacao_total')
        
        video_data = {
            'status_upload': form_data.get('status_upload'),
            'duracao': int(duracao) if duracao and duracao.isdigit() else None,
            'tts_provider': form_data.get('tts_provider'),
            'voz_tts': form_data.get('voz_tts'),
            'visualizacao_total': int(visualizacao_total) if visualizacao_total and visualizacao_total.isdigit() else 0,
            'arquivo_audio': form_data.get('arquivo_audio'),
            'arquivo_video': form_data.get('arquivo_video'),
            'arquivo_legenda': form_data.get('arquivo_legenda'),
            'audio_mixado': form_data.get('audio_mixado')
        }
        
        # Remove valores vazios
        roteiro_data = {k: v for k, v in roteiro_data.items() if v is not None and v != ''}
        video_data = {k: v for k, v in video_data.items() if v is not None}
        
        return roteiro_data, video_data