# youtube_metadata.py
from datetime import datetime, timedelta
from pathlib import Path

class YouTubeMetadata:
    def __init__(self, db_manager):
        self.db = db_manager

    def preparar_metadados(self, roteiro, is_short: bool, agendamento=None, publicar_imediato: bool = False):
        """Prepara os metadados do vídeo para upload"""
        # Tags básicas
        tags = []
        if roteiro.tags:
            tags = [tag.strip() for tag in roteiro.tags.split(',') if tag.strip()]
        
        # Adiciona tag de Short se necessário
        if is_short:
            tags.append('shorts')
            print("🏷️ Adicionada tag 'shorts'")
        
        # Limita tags a 500 caracteres (limite do YouTube)
        all_tags = ','.join(tags)
        if len(all_tags) > 500:
            print(f"⚠️ Tags muito longas ({len(all_tags)} chars), truncando...")
            tags = tags[:10]  # Mantém apenas as primeiras 10 tags
        
        body = {
            'snippet': {
                'title': roteiro.titulo[:100],  # Limite de 100 caracteres
                'description': (roteiro.descricao or '')[:5000],  # Limite de 5000 caracteres
                'tags': tags,
                'categoryId': '22'  # Educação
            },
            'status': {
                'privacyStatus': 'private'  # Padrão: privado
            }
        }
        
        # Configura status de publicação
        self._configurar_status_publicacao(body, agendamento, publicar_imediato)
        
        print(f"📝 Metadados preparados - Título: {roteiro.titulo}")
        print(f"📋 Tags: {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}")
        
        return body

    def _configurar_status_publicacao(self, body: dict, agendamento, publicar_imediato: bool):
        """Configura o status de publicação baseado nas opções"""
        if publicar_imediato:
            # Publicação imediata
            body['status']['privacyStatus'] = 'public'
            print("🚀 Configurado para PUBLICAR IMEDIATAMENTE")
            
        elif agendamento:
            # Agendamento
            data_publicacao = datetime.strptime(agendamento.data_publicacao, '%Y-%m-%d')
            hora_publicacao = datetime.strptime(agendamento.hora_publicacao, '%H:%M').time()
            data_hora_local = datetime.combine(data_publicacao, hora_publicacao)
            
            # Converte para UTC (Brasil UTC-3 → UTC)
            data_hora_utc = data_hora_local + timedelta(hours=3)
            publish_at = data_hora_utc.isoformat() + 'Z'
            
            body['status']['publishAt'] = publish_at
            body['status']['privacyStatus'] = 'private'  # YouTube muda para público no horário
            
            print(f"⏰ Agendado para: {data_hora_local} (local)")
            print(f"🌐 Horário UTC: {data_hora_utc}")
            
        else:
            # Sem agendamento, sem publicação imediata → privado
            body['status']['privacyStatus'] = 'private'
            print("🔒 Vídeo será enviado como PRIVADO")

    def determinar_tipo_video(self, roteiro, video_path: Path) -> bool:
        """Determina se o vídeo é Short ou Long"""
        # Por resolução
        if roteiro.resolucao:
            resolucao = roteiro.resolucao.lower()
            if any(vert in resolucao for vert in ['720x1280', '1080x1920', 'vertical']):
                print("🎯 Vídeo identificado como SHORT (resolução vertical)")
                return True
            if any(horiz in resolucao for horiz in ['1280x720', '1920x1080', 'horizontal']):
                print("🎬 Vídeo identificado como LONG (resolução horizontal)")
                return False
        
        # Por nome do arquivo
        video_name = video_path.name.lower()
        if 'short' in video_name:
            print("🎯 Vídeo identificado como SHORT (nome do arquivo)")
            return True
        if 'long' in video_name:
            print("🎬 Vídeo identificado como LONG (nome do arquivo)")
            return False
        
        # Fallback: considera como Long
        print("ℹ️ Tipo de vídeo não identificado, usando LONG como padrão")
        return False