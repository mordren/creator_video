#!/usr/bin/env python3
import sys
from pathlib import Path

# Adiciona o diretório atual ao path para imports
sys.path.append(str(Path(__file__).parent))

from upload.youtube_auth import YouTubeAuth
from upload.youtube_metadata import YouTubeMetadata
from upload.youtube_upload import YouTubeUpload

class YouTubeUploader:
    def __init__(self):
        from crud.manager import DatabaseManager
        self.db = DatabaseManager()
        self.auth = YouTubeAuth()
        self.metadata = YouTubeMetadata(self.db)
        self.upload = YouTubeUpload(self.db)

    def upload_video(self, roteiro_id: int, publicar_imediato: bool = False) -> bool:
        """Faz upload de um vídeo para o YouTube"""
        print(f"📤 Iniciando upload para YouTube - Roteiro ID: {roteiro_id}")
        
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

            # Autenticação no YouTube
            youtube = self.auth.autenticar(canal.config_path)
            if not youtube:
                return False

            # Determina tipo de vídeo (Short/Long)
            is_short = self.metadata.determinar_tipo_video(roteiro, video_path)

            # Prepara metadados
            body = self.metadata.preparar_metadados(roteiro, is_short, agendamento_yt, publicar_imediato)

            # Faz o upload
            youtube_video_id = self.upload.executar_upload(youtube, video_path, body, is_short)

            if youtube_video_id:
                # Salva informações no banco usando YouTubeManager
                success = self.db.youtube.salvar_informacoes_upload(
                    roteiro_id, youtube_video_id, agendamento_yt, is_short
                )
                
                # Atualiza status
                if success:
                    self._atualizar_status_upload(agendamento_yt, roteiro_id)
                
                return success
            
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
            import json
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