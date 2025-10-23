# efeitos/camera_instavel.py
import subprocess

def aplicar(video_input: str, video_output: str) -> bool:
    """Aplica efeito de câmera instável/tremida"""
    try:
        filtro = 'deshake'
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_input,
            '-vf', filtro,
            '-c:a', 'copy',
            '-preset', 'medium',
            video_output
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Efeito camera_instavel aplicado com sucesso")
            return True
        else:
            print(f"❌ Erro FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao aplicar camera_instavel: {e}")
        return False