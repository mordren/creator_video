# celery_app.py
import os
from celery import Celery
from pathlib import Path
import sys

# Adiciona o diretório atual ao path
sys.path.append(str(Path(__file__).parent))

# Configuração do Celery
celery_app = Celery('creator_app',
                    broker=os.getenv('CELERY_BROKER_URL', 'redis://192.168.31.200:6379/0'),
                    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://192.168.31.200:6379/0'))

# Configurações
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_pool='solo',
    broker_connection_retry_on_startup=True,
)

# Auto-descobre e registra tarefas automaticamente
celery_app.autodiscover_tasks(['tasks'])

print("✅ Celery app configurado com sucesso!")