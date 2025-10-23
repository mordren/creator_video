# test_filosofia_melhorado.py
import subprocess
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from templates.short_filosofia import render

# Configuração para teste
config = {
    'images_dir': './imagens',
    'titulo': 'FILOSOFIA MELHORADO',
    'num_imagens': 8,
    'output_dir': './renders_test'
}

try:
    print("🎬 Testando template melhorado...")
    resultado = render('./21.mp3', config)
    print(f"✅ Teste concluído: {resultado}")
    
    # Verificar se tem efeitos aplicados
    cmd_check = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,duration,nb_frames',
        '-of', 'csv=p=0',
        str(resultado)
    ]
    result = subprocess.run(cmd_check, capture_output=True, text=True)
    if result.returncode == 0:
        width, height, duration, frames = result.stdout.strip().split(',')
        print(f"📐 Resolução: {width}x{height}")
        print(f"⏱️ Duração: {duration}s")
        print(f"🎞️ Frames: {frames}")
        
except Exception as e:
    print(f"❌ Erro no teste: {e}")
    import traceback
    traceback.print_exc()