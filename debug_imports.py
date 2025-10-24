import sys
import os
import importlib

# Adiciona o diretório atual ao Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def testar_imports():
    """Testa todos os imports antes de executar"""
    print("🧪 Testando imports...")
    
    # Testa imports básicos
    try:
        from video_maker.video_utils import get_media_duration, listar_imagens
        print("✅ video_utils OK")
    except ImportError as e:
        print(f"❌ video_utils: {e}")
        return False

    # Testa imports de efeitos
    efeitos = [
        ('camera_instavel', 'aplicar_efeito_camera_instavel'),
        ('pan', 'criar_video_pan'),
        ('depth_3d', 'criar_video_depth_3d'),
        ('panoramica_vertical', 'criar_video_panoramica_vertical'),
        ('zoom_invertido', 'criar_video_zoom_invertido'),
        ('zoom_pulse', 'criar_video_pulse'),
    ]
    
    for modulo, funcao in efeitos:
        try:
            mod = importlib.import_module(f'video_maker.efeitos.{modulo}')
            getattr(mod, funcao)
            print(f"✅ {modulo}.{funcao} OK")
        except (ImportError, AttributeError) as e:
            print(f"❌ {modulo}.{funcao}: {e}")
            return False

    # Testa template
    try:
        from video_maker.templates.short_filosofia import render
        print("✅ short_filosofia OK")
        return True
    except ImportError as e:
        print(f"❌ short_filosofia: {e}")
        return False

if __name__ == "__main__":
    if testar_imports():
        print("\n🚀 Todos os imports funcionando! Executando template...")
        
        # Configuração de teste
        config = {
            'images_dir': r"C:\Users\mordren\Documents\Foocus\imagens geradas\out_short_segundos",
            'titulo': "TESTE FILOSOFIA",
            'output_dir': "./renders",
            'num_imagens': 5
        }
        
        # Caminho para áudio de teste (ajuste conforme necessário)
        audio_path = "./21.mp3"  # Crie este arquivo ou ajuste
        
        if not os.path.exists(audio_path):
            print(f"⚠️ Arquivo de áudio não encontrado: {audio_path}")
            print("📝 Criando áudio temporário para teste...")
            # Cria um áudio temporário de 10 segundos
            os.makedirs("./audio", exist_ok=True)
            import subprocess
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=10",
                "-ac", "2", audio_path
            ], capture_output=True)
        
        from video_maker.templates.short_filosofia import render
        
        try:
            resultado = render(audio_path, config)
            print(f"🎉 Vídeo criado com sucesso: {resultado}")
        except Exception as e:
            print(f"❌ Erro durante renderização: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n💥 Corrija os imports antes de continuar.")