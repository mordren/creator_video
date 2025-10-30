#!/usr/bin/env python3
import os
import sys
import pickle
import json
from pathlib import Path
from datetime import datetime, timedelta
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
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

    def upload_video(self, roteiro_id: int, publicar_imediato: bool = False) -> bool:
        """Faz upload de um vídeo para o YouTube com suporte a agendamento e publicação imediata"""
        print(f"📤 Iniciando upload para YouTube - Roteiro ID: {roteiro_id}")
        print(f"🚀 Modo: {'PUBLICAÇÃO IMEDIATA' if publicar_imediato else 'AGENDAMENTO/RESPEITAR AGENDAMENTOS'}")
        
        try:
            # Busca informações no banco
            roteiro, canal, video_info = self._buscar_dados_banco(roteiro_id)
            if not all([roteiro, canal, video_info]):
                return False

            # Verifica se o arquivo de vídeo existe
            video_path = Path(video_info.arquivo_video)
            if not self._verificar_arquivo_video(video_path):
                return False

            # Busca agendamentos (a menos que seja publicação imediata)
            agendamento_yt = None
            if not publicar_imediato:
                agendamento_yt = self._buscar_agendamento_youtube(roteiro_id)

            # Carrega configuração do canal
            config = self._carregar_config_canal(canal.config_path)
            if not config:
                return False

            # Autenticação no YouTube
            youtube = self._autenticar(canal)
            if not youtube:
                return False

            # Determina tipo de vídeo (Short/Long)
            is_short = self._determinar_tipo_video(roteiro, video_path)

            # Faz o upload
            success = self._fazer_upload(
                youtube=youtube,
                video_path=video_path,
                roteiro=roteiro,
                is_short=is_short,
                agendamento=agendamento_yt,
                publicar_imediato=publicar_imediato
            )

            # Atualiza status se bem-sucedido
            if success:
                self._atualizar_status_upload(agendamento_yt, roteiro_id)
                return True
            
            return False

        except Exception as e:
            print(f"❌ Erro crítico durante upload: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _buscar_dados_banco(self, roteiro_id: int):
        """Busca dados necessários no banco de dados"""
        try:
            roteiro = self.db.roteiros.buscar_por_id(roteiro_id)
            if not roteiro:
                print(f"❌ Roteiro não encontrado: {roteiro_id}")
                return None, None, None

            canal = self.db.canais.buscar_por_id(roteiro.canal_id)
            if not canal:
                print(f"❌ Canal não encontrado para roteiro: {roteiro_id}")
                return None, None, None

            video_info = self.db.videos.buscar_por_roteiro_id(roteiro_id)
            if not video_info:
                print(f"❌ Informações de vídeo não encontradas: {roteiro_id}")
                return None, None, None

            print(f"✅ Dados carregados - Canal: {canal.nome}, Vídeo: {roteiro.titulo}")
            return roteiro, canal, video_info

        except Exception as e:
            print(f"❌ Erro ao buscar dados no banco: {e}")
            return None, None, None

    def _verificar_arquivo_video(self, video_path: Path) -> bool:
        """Verifica se o arquivo de vídeo existe e é válido"""
        if not video_path.exists():
            print(f"❌ Arquivo de vídeo não encontrado: {video_path}")
            return False
        
        if video_path.stat().st_size == 0:
            print(f"❌ Arquivo de vídeo está vazio: {video_path}")
            return False
        
        print(f"✅ Arquivo de vídeo válido: {video_path} ({video_path.stat().st_size / (1024*1024):.1f} MB)")
        return True

    def _buscar_agendamento_youtube(self, roteiro_id: int):
        """Busca agendamentos ativos para YouTube"""
        try:
            agendamentos = self.db.agendamentos.buscar_por_video_id(roteiro_id)
            
            for agendamento in agendamentos:
                plataformas = json.loads(agendamento.plataformas)
                if 'youtube' in plataformas and agendamento.status == 'agendado':
                    print(f"📅 Agendamento encontrado: {agendamento.data_publicacao} {agendamento.hora_publicacao}")
                    return agendamento
            
            print("ℹ️ Nenhum agendamento ativo encontrado para YouTube")
            return None

        except Exception as e:
            print(f"⚠️ Erro ao buscar agendamentos: {e}")
            return None

    def _carregar_config_canal(self, config_path: str):
        """Carrega configuração do canal"""
        try:
            from read_config import carregar_config_canal
            config = carregar_config_canal(config_path)
            print(f"✅ Configuração carregada: {config.get('NOME_CANAL', 'desconhecido')}")
            return config
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            return None

    def _autenticar(self, canal):
        """Autentica no YouTube API"""
        try:
            credentials_path = Path('assets/client_secret.json')
            token_path = Path(canal.config_path) / 'token.pickle'
            
            if not credentials_path.exists():
                print(f"❌ Arquivo de credenciais não encontrado: {credentials_path}")
                return None

            creds = self._carregar_credenciais(token_path)
            
            if not creds or not creds.valid:
                creds = self._renovar_credenciais(creds, credentials_path, token_path)
                if not creds:
                    return None

            print("✅ Autenticação no YouTube bem-sucedida")
            return build('youtube', 'v3', credentials=creds)

        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            return None

    def _carregar_credenciais(self, token_path: Path):
        """Carrega credenciais existentes do token"""
        if token_path.exists():
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
                print("✅ Credenciais carregadas do token existente")
                return creds
            except Exception as e:
                print(f"⚠️ Erro ao carregar token: {e}")
        return None

    def _renovar_credenciais(self, creds, credentials_path: Path, token_path: Path):
        """Renova ou obtém novas credenciais"""
        try:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refrescando credenciais expiradas...")
                creds.refresh(Request())
            else:
                print("🔐 Iniciando fluxo de autenticação OAuth...")
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), self.SCOPES)
                creds = flow.run_local_server(port=0, open_browser=True)
            
            # Salva as credenciais para uso futuro
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            print("✅ Novas credenciais salvas")
            return creds
            
        except Exception as e:
            print(f"❌ Erro ao renovar credenciais: {e}")
            return None

    def _determinar_tipo_video(self, roteiro, video_path: Path) -> bool:
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

    def _fazer_upload(self, youtube, video_path: Path, roteiro, is_short: bool, 
                     agendamento, publicar_imediato: bool) -> bool:
        """Executa o upload do vídeo para o YouTube"""
        try:
            # Prepara metadados
            body = self._preparar_metadados(roteiro, is_short)
            
            # Configura status de publicação
            self._configurar_status_publicacao(body, agendamento, publicar_imediato)
            
            # Executa upload
            return self._executar_upload(youtube, video_path, body, is_short)
            
        except Exception as e:
            print(f"❌ Erro durante o upload: {e}")
            return False

    def _preparar_metadados(self, roteiro, is_short: bool) -> dict:
        """Prepara os metadados do vídeo"""
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

    def _executar_upload(self, youtube, video_path: Path, body: dict, is_short: bool) -> bool:
        """Executa o upload propriamente dito"""
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
                
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erro durante execução do upload: {e}")
            return False

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
                    import time
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

    def _atualizar_status_upload(self, agendamento, roteiro_id: int):
        """Atualiza status no banco após upload bem-sucedido"""
        try:
            if agendamento:
                # Atualiza status do agendamento
                self.db.agendamentos.atualizar(agendamento.id, status='agendado_no_youtube')
                print("📅 Status do agendamento atualizado para 'agendado_no_youtube'")
            else:
                # Atualiza status do vídeo
                self.db.roteiros.atualizar(roteiro_id, finalizado=True)
                print("✅ Status do vídeo atualizado para 'finalizado'")
                
        except Exception as e:
            print(f"⚠️ Erro ao atualizar status no banco: {e}")

def main():
    """Função principal para execução via linha de comando"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fazer upload de vídeo para YouTube')
    parser.add_argument('roteiro_id', type=int, help='ID do roteiro no banco de dados')
    parser.add_argument('--publicar-agora', action='store_true', 
                       help='Publicar vídeo imediatamente (ignora agendamentos)')
    
    args = parser.parse_args()
    
    success = YouTubeUploader().upload_video(
        roteiro_id=args.roteiro_id,
        publicar_imediato=args.publicar_agora
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()