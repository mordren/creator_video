# youtube_info_manager.py
from datetime import datetime
from crud.models import VideoYouTube, TipoConteudo

class YouTubeInfoManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def salvar_informacoes_youtube(self, roteiro_id: int, youtube_video_id: str, 
                                 agendamento=None, is_short: bool = False):
        """Salva informações do vídeo do YouTube no banco de dados"""
        try:
            # Busca o vídeo principal pelo roteiro_id
            video_info = self.db.videos.buscar_por_roteiro_id(roteiro_id)
            if not video_info:
                print(f"❌ Vídeo não encontrado para roteiro_id {roteiro_id}")
                return False

            # Determina tipo de conteúdo
            tipo_conteudo = TipoConteudo.SHORT if is_short else TipoConteudo.LONG
            
            # Gera o link do vídeo
            link = f"https://youtu.be/{youtube_video_id}"
            
            # Prepara dados para VideoYouTube
            dados_youtube = {
                'video_id': video_info.id,
                'youtube_video_id': youtube_video_id,
                'link': link,
                'hora_upload': datetime.utcnow(),
                'tipo_conteudo': tipo_conteudo
            }
            
            # Se houver agendamento, define hora_estreia
            if agendamento:
                data_publicacao = datetime.strptime(agendamento.data_publicacao, '%Y-%m-%d')
                hora_publicacao = datetime.strptime(agendamento.hora_publicacao, '%H:%M').time()
                dados_youtube['hora_estreia'] = datetime.combine(data_publicacao, hora_publicacao)
            
            # Busca registro existente
            video_youtube = self.db.youtube.buscar_por_video_id(video_info.id)
            
            if video_youtube:
                # Atualiza registro existente
                for campo, valor in dados_youtube.items():
                    setattr(video_youtube, campo, valor)
                self.db.youtube.atualizar(video_youtube)
                print(f"📝 Informações do YouTube atualizadas (ID: {video_youtube.id})")
            else:
                # Cria novo registro
                video_youtube = VideoYouTube(**dados_youtube)
                self.db.youtube.criar(video_youtube)
                print(f"📹 Novo registro YouTube criado (ID: {video_youtube.id})")
            
            print(f"🔗 Link do vídeo: {link}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar informações do YouTube: {e}")
            import traceback
            traceback.print_exc()
            return False