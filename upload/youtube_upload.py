# youtube_upload.py
from googleapiclient.http import MediaFileUpload
import time

class YouTubeUpload:
    def __init__(self, db_manager):
        self.db = db_manager

    def executar_upload(self, youtube, video_path, body, is_short: bool):
        """Executa o upload do vídeo para o YouTube"""
        try:
            print("⬆️ Iniciando upload...")
            
            media = MediaFileUpload(
                str(video_path),
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Upload resumável
            response = self._upload_resumavel(request)
            
            if response:
                video_id = response['id']
                print(f"✅ Upload concluído! Video ID: {video_id}")
                
                # Se for Short, tenta adicionar à playlist de Shorts
                if is_short:
                    self._tentar_adicionar_shorts_playlist(youtube, video_id)
                
                return video_id
            
            return None
            
        except Exception as e:
            print(f"❌ Erro durante execução do upload: {e}")
            return None

    def _upload_resumavel(self, request):
        """Executa upload resumável com retentativas"""
        response = None
        retry = 0
        max_retries = 3
        
        while response is None and retry < max_retries:
            try:
                status, response = request.next_chunk()
                if status:
                    progresso = int(status.progress() * 100)
                    print(f"📊 Progresso do upload: {progresso}%")
                    
            except Exception as e:
                retry += 1
                if retry < max_retries:
                    print(f"🔄 Retentativa {retry}/{max_retries} em 5 segundos...")
                    time.sleep(5)
                else:
                    print(f"❌ Falha após {max_retries} tentativas: {e}")
                    raise e
        
        return response

    def _tentar_adicionar_shorts_playlist(self, youtube, video_id: str):
        """Tenta adicionar o vídeo à playlist de Shorts (opcional)"""
        try:
            # Busca a playlist de uploads do canal
            channels_response = youtube.channels().list(
                part='contentDetails',
                mine=True
            ).execute()
            
            if not channels_response.get('items'):
                print("⚠️ Não foi possível obter informações do canal")
                return
            
            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Adiciona à playlist de uploads
            youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': uploads_playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': video_id
                        }
                    }
                }
            ).execute()
            
            print("📋 Vídeo adicionado à playlist de uploads do canal")
            
        except Exception as e:
            print(f"⚠️ Não foi possível adicionar à playlist: {e}")