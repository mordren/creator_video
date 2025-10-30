#!/usr/bin/env python3
# celery_worker.py
import os
import sys
from pathlib import Path

# Adiciona o diretório atual ao path para imports
sys.path.append(str(Path(__file__).parent))

if __name__ == '__main__':
    # Use o comando do sistema para iniciar o Celery corretamente
    os.system('celery -A tasks worker --loglevel=info --pool=solo')