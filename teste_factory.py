import sys
import os
import subprocess
from pathlib import Path

# Adiciona o diretório raiz ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_maker.video_engine import aplicar_efeito, listar_efeitos
from video_maker.templates.short_filosofia import render

def main():
    print("🎯 Efeitos disponíveis via factory:")
    for efeito in listar_efeitos():
        print(f"  - {efeito}")
    
    # Configuração de teste
    config = {
        'images_dir': r"C:\Users\mordren\Documents\Foocus\imagens geradas\out_short_segundos",
        'titulo': "@reflexoes_do_poder",
        'output_dir': "./renders",
        'num_imagens': 18
    }
    
    # Caminho para áudio de teste
    audio_path = "21.mp3"
    
    # Criar áudio temporário se não existir
    if not os.path.exists(audio_path):
        print("📝 Criando áudio temporário para teste...")
        os.makedirs("./audio", exist_ok=True)
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=10",
            "-ac", "2", audio_path
        ], capture_output=True)
    
    try:
        resultado = render(audio_path, config)
        print(f"🎉 Vídeo criado com sucesso: {resultado}")
    except Exception as e:
        print(f"❌ Erro durante renderização: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()