# efeitos/depth_3d.py
import subprocess

def aplicar(video_input: str, video_output: str) -> bool:
    """Aplica efeito de profundidade 3D"""
    try:
        filtro = 'stereo3d=sbsl:ml'
        
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
            print(f"✅ Efeito depth_3d aplicado com sucesso")
            return True
        else:
            print(f"❌ Erro FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao aplicar depth_3d: {e}")
        return False