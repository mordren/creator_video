# efeitos/pan.py
import subprocess

def aplicar(video_input: str, video_output: str) -> bool:
    """Aplica efeito de pan (movimento horizontal)"""
    try:
        filtro = 'crop=iw*0.8:ih:20*t:0,scale=1920:1080'
        
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
            print(f"✅ Efeito pan aplicado com sucesso")
            return True
        else:
            print(f"❌ Erro FFmpeg: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao aplicar pan: {e}")
        return False