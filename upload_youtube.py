#!/usr/bin/env python3
import os
import sys
import pickle
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Adiciona o diretório atual ao path para imports
sys.path.append(str(Path(__file__).parent))

class YouTubeUploader:
    def __init__(self):
        from crud.manager import DatabaseManager
        self.db = DatabaseManager()

    def upload_video(self, roteiro_id: int) -> bool:
        """Faz upload de um vídeo para o YouTube baseado no ID do roteiro, respeitando agendamentos"""
        print(f"📤 Iniciando upload para YouTube do Roteiro ID: {roteiro_id}")
        
        try:
            # Busca roteiro no banco
            roteiro = self.db.roteiros.buscar_por_id(roteiro_id)
            if not roteiro:
                print(f"❌ Roteiro não encontrado com ID: {roteiro_id}")
                return False

            # Busca canal
            canal = self.db.canais.buscar_por_id(roteiro.canal_id)
            if not canal:
                print(f"❌ Canal não encontrado para o roteiro {roteiro_id}")
                return False

            # Busca informações do vídeo
            video_info = self.db.videos.buscar_por_roteiro_id(roteiro_id)
            if not video_info or not video_info.arquivo_video:
                print(f"❌ Arquivo de vídeo não encontrado para o roteiro {roteiro_id}")
                return False

            video_path = Path(video_info.arquivo_video)
            if not video_path.exists():
                print(f"❌ Arquivo de vídeo não existe: {video_path}")
                return False

            # Busca agendamentos para este vídeo
            agendamentos = self.db.agendamentos.buscar_por_video_id(roteiro_id)
            agendamento_yt = None
            
            for agendamento in agendamentos:
                plataformas = json.loads(agendamento.plataformas)
                if 'youtube' in plataformas and agendamento.status == 'agendado':
                    agendamento_yt = agendamento
                    break

            # Carrega configuração do canal
            from read_config import carregar_config_canal
            config = carregar_config_canal(canal.config_path)
            print(f"🔧 Config carregada: {config.get('NOME_CANAL', 'desconhecido')}")

            # Autenticação no YouTube
            youtube = self._autenticar(canal, config)
            if not youtube:
                return False

            # Determina se é Short ou Long
            is_short = self._is_video_short(roteiro, video_path)

            # Faz o upload com agendamento se existir
            success = self._fazer_upload(
                youtube, 
                video_path, 
                roteiro, 
                is_short, 
                agendamento_yt
            )

            if success and agendamento_yt:
                # Atualiza o status do agendamento
                self.db.agendamentos.atualizar(agendamento_yt.id, status='agendado_no_youtube')
                print("✅ Upload agendado com sucesso!")
            elif success:
                print("✅ Upload realizado com sucesso!")
            else:
                print("❌ Falha no upload")
                return False

            return True

        except Exception as e:
            print(f"❌ Erro durante o upload: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _autenticar(self, canal, config):
        """Autentica no YouTube usando as credenciais do canal"""
        # ✅ CORREÇÃO: Converte para Path
        credentials_path = Path('assets/client_secret.json')
        token_path = Path(canal.config_path) / 'token.pickle'
        
        SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
        
        creds = None
        
        # Carrega token existente
        if token_path.exists():
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

        # Se não há credenciais válidas, faz o fluxo OAuth
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    print(f"❌ Arquivo de credenciais não encontrado: {credentials_path}")
                    return None
                
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Salva as credenciais para o próximo uso
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

        return build('youtube', 'v3', credentials=creds)

    def _is_video_short(self, roteiro, video_path):
        """Determina se o vídeo é um Short baseado na resolução ou duração"""
        # Primeiro tenta pela resolução do roteiro
        if roteiro.resolucao:
            resolucao_lower = roteiro.resolucao.lower()
            if '720x1280' in resolucao_lower or '1080x1920' in resolucao_lower or 'vertical' in resolucao_lower:
                return True
            if '1280x720' in resolucao_lower or '1920x1080' in resolucao_lower or 'horizontal' in resolucao_lower:
                return False
        
        # Se não conseguir pela resolução, tenta pelo nome
        video_name = video_path.name.lower()
        if 'short' in video_name:
            return True
        
        # Como fallback, considera como não-Short
        return False

    def _fazer_upload(self, youtube, video_path, roteiro, is_short, agendamento):
        """Faz o upload do vídeo para o YouTube, com agendamento se especificado"""
        try:
            # Prepara os metadados do vídeo
            body = {
                'snippet': {
                    'title': roteiro.titulo,
                    'description': roteiro.descricao or '',
                    'tags': roteiro.tags.split(',') if roteiro.tags else [],
                    'categoryId': '22'  # Educacional
                },
                'status': {
                    'privacyStatus': 'private'  # Inicialmente privado
                }
            }

            # Se for Short, adiciona a tag específica
            if is_short:
                body['snippet']['tags'].append('shorts')
                print("🎯 Uploading as YouTube Short")

            # Se houver agendamento, configura a data de publicação
            if agendamento:
                # ✅ CORREÇÃO DE FUSO HORÁRIO: Converte para UTC
                data_publicacao = datetime.strptime(agendamento.data_publicacao, '%Y-%m-%d')
                hora_publicacao = datetime.strptime(agendamento.hora_publicacao, '%H:%M').time()
                data_hora_local = datetime.combine(data_publicacao, hora_publicacao)
                
                # Converte para UTC (assumindo que o horário agendado é no fuso local)
                # Para Brasil (UTC-3), adiciona 3 horas para converter para UTC
                data_hora_utc = data_hora_local + timedelta(hours=3)
                
                # Formato ISO 8601 requerido pelo YouTube (UTC)
                publish_at = data_hora_utc.isoformat() + 'Z'
                
                body['status']['publishAt'] = publish_at
                body['status']['privacyStatus'] = 'private'  # Será publicado no horário agendado
                
                print(f"⏰ Agendando vídeo para {data_hora_local} (horário local)")
                print(f"🌐 Convertido para UTC: {data_hora_utc}")
            else:
                # Upload imediato
                body['status']['privacyStatus'] = 'public'
                print("🚀 Publicando vídeo imediatamente")

            # Faz o upload
            media = MediaFileUpload(
                str(video_path),
                chunksize=-1,
                resumable=True
            )

            request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )

            response = self._upload_resumable(request)
            
            if response:
                video_id = response['id']
                print(f"✅ Upload concluído! Video ID: {video_id}")
                
                # Se for Short, adiciona à playlist de Shorts (opcional)
                if is_short:
                    self._adicionar_a_shorts(youtube, video_id)
                
                return True
            
            return False

        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            return False

    def _adicionar_a_shorts(self, youtube, video_id):
        """Adiciona vídeo à playlist de Shorts do canal (opcional)"""
        try:
            # Busca a playlist de uploads do canal (que inclui Shorts)
            channels_response = youtube.channels().list(
                part='contentDetails',
                mine=True
            ).execute()
            
            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Adiciona à playlist de uploads (já é automático, mas podemos confirmar)
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
            
            print("📋 Vídeo adicionado à playlist de uploads")
            
        except Exception as e:
            print(f"⚠️ Não foi possível adicionar à playlist: {e}")

    def _upload_resumable(self, request):
        """Faz upload resumável para lidar com vídeos grandes"""
        response = None
        retry = 0
        while response is None and retry < 3:
            try:
                status, response = request.next_chunk()
                if status:
                    print(f"📊 Progresso: {int(status.progress() * 100)}%")
            except Exception as e:
                retry += 1
                print(f"🔄 Retentativa {retry}/3...")
                if retry >= 3:
                    raise e
        
        return response

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fazer upload de vídeo para YouTube')
    parser.add_argument('roteiro_id', type=int, help='ID do roteiro no banco de dados')
    
    args = parser.parse_args()
    
    success = YouTubeUploader().upload_video(args.roteiro_id)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()