# tasks.py - VERSÃO CORRIGIDA
from celery_app import celery_app
import sys
from pathlib import Path

# Adiciona o diretório atual ao path
sys.path.append(str(Path(__file__).parent))

def safe_exception_info(e):
    """Garante que exceções sejam serializáveis corretamente"""
    return {
        'exc_type': type(e).__name__,
        'exc_message': str(e),
        'exc_module': type(e).__module__
    }

@celery_app.task(bind=True)
def generate_audio_task(self, video_id):
    """Tarefa para geração de áudio - VERSÃO CORRIGIDA"""
    try:
        # Importação DINÂMICA dentro da função
        from audio import AudioSystem
        
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 10,
                'total': 100,
                'status': 'Iniciando geração de áudio...',
                'video_id': video_id
            }
        )
        
        print(f"🎵 Gerando áudio para vídeo: {video_id}")
        
        audio_system = AudioSystem()
        success = audio_system.generate_audio(video_id)
        
        if success:
            self.update_state(
                state='SUCCESS',
                meta={
                    'current': 100,
                    'total': 100,
                    'status': 'Áudio gerado com sucesso!',
                    'video_id': video_id
                }
            )
            return {'status': 'success', 'message': 'Áudio gerado com sucesso!'}
        else:
            self.update_state(
                state='FAILURE',
                meta={
                    'current': 100,
                    'total': 100,
                    'status': 'Falha na geração do áudio',
                    'video_id': video_id
                }
            )
            return {'status': 'error', 'message': 'Falha ao gerar áudio'}
            
    except Exception as e:
        print(f"❌ Erro na geração de áudio: {e}")
        # ✅ CORREÇÃO: Usar safe_exception_info
        exc_info = safe_exception_info(e)
        self.update_state(
            state='FAILURE',
            meta={
                'current': 100,
                'total': 100,
                'status': f'Erro: {str(e)}',
                'video_id': video_id,
                'exc_info': exc_info  # ✅ Informações de exceção serializáveis
            }
        )
        # ✅ CORREÇÃO: Relançar a exceção corretamente
        raise

@celery_app.task(bind=True)
def generate_video_task(self, video_id):
    """Tarefa para geração de vídeo - VERSÃO CORRIGIDA"""
    try:
        # Importação DINÂMICA dentro da função
        from video import VideoGenerator
        
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 10,
                'total': 100,
                'status': 'Iniciando geração de vídeo...',
                'video_id': video_id
            }
        )
        
        print(f"🎬 Gerando vídeo para: {video_id}")
        
        video_gen = VideoGenerator()
        success = video_gen.gerar_video(video_id)
        
        if success:
            self.update_state(
                state='SUCCESS',
                meta={
                    'current': 100,
                    'total': 100,
                    'status': 'Vídeo gerado com sucesso!',
                    'video_id': video_id
                }
            )
            return {'status': 'success', 'message': 'Vídeo gerado com sucesso!'}
        else:
            self.update_state(
                state='FAILURE',
                meta={
                    'current': 100,
                    'total': 100,
                    'status': 'Falha na geração do vídeo',
                    'video_id': video_id
                }
            )
            return {'status': 'error', 'message': 'Falha ao gerar vídeo'}
            
    except Exception as e:
        print(f"❌ Erro na geração de vídeo: {e}")
        # ✅ CORREÇÃO: Usar safe_exception_info
        exc_info = safe_exception_info(e)
        self.update_state(
            state='FAILURE',
            meta={
                'current': 100,
                'total': 100,
                'status': f'Erro: {str(e)}',
                'video_id': video_id,
                'exc_info': exc_info
            }
        )
        raise

@celery_app.task(bind=True)
def upload_youtube_task(self, roteiro_id, publicar_imediato=False):
    """Tarefa para upload no YouTube - VERSÃO CORRIGIDA"""
    try:
        # Importação DINÂMICA dentro da função
        from upload_youtube import YouTubeUploader
        
        self.update_state(
            state='PROGRESS',
            meta={
                'current': 10,
                'total': 100,
                'status': 'Iniciando upload para YouTube...',
                'roteiro_id': roteiro_id
            }
        )
        
        print(f"📤 Fazendo upload para YouTube: {roteiro_id}")
        
        uploader = YouTubeUploader()
        success = uploader.upload_video(roteiro_id, publicar_imediato)
        
        if success:
            self.update_state(
                state='SUCCESS',
                meta={
                    'current': 100,
                    'total': 100,
                    'status': 'Upload concluído com sucesso!',
                    'roteiro_id': roteiro_id
                }
            )
            return {'status': 'success', 'message': 'Upload para YouTube concluído!'}
        else:
            self.update_state(
                state='FAILURE',
                meta={
                    'current': 100,
                    'total': 100,
                    'status': 'Falha no upload para YouTube',
                    'roteiro_id': roteiro_id
                }
            )
            return {'status': 'error', 'message': 'Falha no upload para YouTube'}
            
    except Exception as e:
        print(f"❌ Erro no upload para YouTube: {e}")
        # ✅ CORREÇÃO: Usar safe_exception_info
        exc_info = safe_exception_info(e)
        self.update_state(
            state='FAILURE',
            meta={
                'current': 100,
                'total': 100,
                'status': f'Erro: {str(e)}',
                'roteiro_id': roteiro_id,
                'exc_info': exc_info
            }
        )
        raise

# ✅ CORREÇÃO: Tarefa simplificada para verificar status
@celery_app.task(bind=True)
def check_task_status(self, task_id):
    """Verifica o status de uma tarefa - VERSÃO CORRIGIDA"""
    try:
        from celery.result import AsyncResult
        task = AsyncResult(task_id)
        
        response = {
            'state': task.state,
            'task_id': task_id
        }
        
        if task.state == 'PENDING':
            response['status'] = 'Pendente'
        elif task.state == 'PROGRESS':
            response.update({
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 100),
                'status': task.info.get('status', ''),
                'video_id': task.info.get('video_id'),
                'roteiro_id': task.info.get('roteiro_id')
            })
        elif task.state == 'SUCCESS':
            response['result'] = task.result
        elif task.state == 'FAILURE':
            # ✅ CORREÇÃO: Lidar com falhas de forma segura
            response['status'] = 'Falha na tarefa'
            if hasattr(task, 'info') and task.info:
                if isinstance(task.info, dict):
                    response['error'] = task.info.get('status', 'Erro desconhecido')
                else:
                    response['error'] = str(task.info)
        
        return response
            
    except Exception as e:
        # ✅ CORREÇÃO: Retornar erro serializável
        return {
            'state': 'ERROR',
            'status': f'Erro ao verificar status: {str(e)}',
            'task_id': task_id
        }

print("✅ Tarefas Celery corrigidas e registradas!")