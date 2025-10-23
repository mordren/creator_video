# templates/short_filosofia.py
from pathlib import Path
import random
import subprocess
import shutil
import sys
import os

# Adiciona o caminho pai ao sys.path para imports absolutos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..video_utils import (
    get_media_duration, 
    listar_imagens,
    gerar_capa,    
)
from ..subtitle_tools import srt_to_ass_karaoke

# Importar os efeitos que funcionam (baseado no seu simple.py)
from ..efeitos.camera_instavel import criar_video_camera_instavel
from ..efeitos.depth_3d import criar_video_depth_3d
from ..efeitos.pan import criar_video_pan
from ..efeitos.panoramica_vertical import criar_video_panoramica_vertical
from ..efeitos.zoom_invertido import criar_video_zoom_invertido
from ..efeitos.zoom_pulse import criar_video_pulse

def normalizar_duracao(in_path, target_s, fps=60):
    """Normaliza a duração de um vídeo para o tempo exato (igual ao simple.py)"""
    in_path = Path(in_path)
    if not in_path.exists():
        return None
    out_path = in_path.with_name(in_path.stem + "_norm.mp4")
    
    subprocess.run([
        "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(in_path),
        "-r", str(fps),
        "-t", f"{target_s:.3f}",
        "-an",  # vídeo puro
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p",
        str(out_path)
    ], check=True)
    return str(out_path)

def criar_clip_capa(capa_path: Path, dur=1.0) -> str:
    """Cria um clipe da capa (igual ao simple.py)"""
    saida = "./renders/temp/000_capa.mp4"
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(capa_path),
        "-t", str(dur),
        "-r", "30",
        "-vf", "scale=720:1280,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        saida
    ]
    subprocess.run(cmd, check=True)
    return saida

def render(audio_path: str, config: dict) -> Path:
    """
    Template para vídeos curtos de filosofia VERTICAL (720x1280)
    Baseado no simple.py que funciona
    """
    audio = Path(audio_path)
    
    # Configurações
    images_dir = Path(config.get('images_dir', "./imagens"))
    titulo = config.get('titulo', "REFLEXÕES FILOSÓFICAS")
    output_dir = Path(config.get('output_dir', "./renders"))
    num_imagens = config.get('num_imagens', 18)
    
    # 1. Preparar diretórios
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir / "temp"
    
    # Limpar diretório temp se existir
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(exist_ok=True)
    
    # 2. Selecionar imagens
    imagens = listar_imagens(images_dir)
    if not imagens:
        raise ValueError(f"Nenhuma imagem encontrada em: {images_dir}")
    
    random.shuffle(imagens)
    num_imagens = min(num_imagens, len(imagens))
    imagens_selecionadas = imagens[:num_imagens]
    
    print(f"🎞️ Usando {len(imagens_selecionadas)} imagens")
    
    # 3. Obter duração do áudio
    audio_duration = get_media_duration(audio)
    print(f"⏱️ Duração do áudio: {audio_duration:.2f}s")
    
    # 4. Gerar capa VERTICAL
    capa_path = temp_dir / "capa.png"
    if imagens_selecionadas:
        imagem_capa = imagens_selecionadas[0]
        
        gerar_capa(
            imagem=imagem_capa,
            titulo=titulo,
            largura=720,    # VERTICAL
            altura=1280,    # VERTICAL
            cor_texto="#6B10D3",
            cor_borda="#FFFFFF"
        )
        
        # Mover a capa gerada
        capa_original = Path("capa.png")
        if capa_original.exists():
            if capa_path.exists():
                capa_path.unlink()
            capa_original.rename(capa_path)
            print("✅ Capa gerada com sucesso")
    
    # 5. Processar legendas
    srt_path = audio.with_suffix('.srt')
    ass_path = temp_dir / "legenda.ass"
    tem_legenda = False
    
    if srt_path.exists():
        try:
            print("📝 Convertendo SRT para ASS...")
            srt_to_ass_karaoke(str(srt_path), str(ass_path), "vertical")
            
            if ass_path.exists() and ass_path.stat().st_size > 100:
                tem_legenda = True
                print("✅ Legenda ASS gerada com sucesso")
            else:
                print("⚠️ Arquivo ASS vazio ou inválido")
                
        except Exception as e:
            print(f"❌ Erro ao gerar legenda ASS: {e}")
    else:
        print("⚠️ Arquivo SRT não encontrado")
    
    # 6. CRIAR CLIPES COM EFEITOS (igual ao simple.py)
    output_path = output_dir / f"{audio.stem}_filosofia.mp4"
    
    # Criar clipe da capa
    clip_capa = criar_clip_capa(capa_path, dur=1.0)
    
    # Lista de efeitos disponíveis (igual ao simple.py)
    efeitos = [
        criar_video_panoramica_vertical,
        criar_video_zoom_invertido,
        criar_video_pan,
        criar_video_pulse,
        criar_video_camera_instavel,
        # criar_video_depth_3d,  # Mais pesado, usar com cautela
    ]
    
    # Calcular durações (igual ao simple.py)
    rest = max(0.0, float(audio_duration) - 1.0)  # Subtrair duração da capa
    imgs_restantes = imagens_selecionadas[1:]  # Pular a primeira que foi usada na capa
    
    n = len(imgs_restantes)
    clips_norm = []
    
    if n > 0 and rest > 0:
        base = rest / n
        durs = [base] * n
        # Ajuste fino do último para fechar no total
        soma = sum(durs)
        durs[-1] += (rest - soma)
        
        # Criar arquivo de lista para concatenação
        lista_clips = temp_dir / "lista_clips.txt"
        
        with open(lista_clips, "w", encoding="utf-8") as f:
            # Adicionar capa primeiro
            f.write(f"file '{Path(clip_capa).resolve()}'\n")
            
            # Processar cada imagem com efeitos
            for i, (img, seg) in enumerate(zip(imgs_restantes, durs)):
                ef = random.choice(efeitos)
                seg = max(0.3, float(seg))
                
                try:
                    print(f"🎬 Aplicando {ef.__name__} na imagem {i+1}...")
                    raw = ef(img, seg)  # Cria com ~seg
                    
                    if raw and hasattr(raw, 'filename') and Path(raw.filename).exists():
                        norm = normalizar_duracao(raw.filename, seg, fps=60)
                        if norm:
                            f.write(f"file '{Path(norm).resolve()}'\n")
                            clips_norm.append(norm)
                        else:
                            print(f"⚠️ Falha ao normalizar clipe {i+1}")
                    else:
                        print(f"⚠️ Efeito {ef.__name__} falhou na imagem {i+1}")
                        
                except Exception as e:
                    print(f"❌ Erro ao processar imagem {i+1} com {ef.__name__}: {e}")
    
    # 7. RENDER FINAL (igual ao simple.py)
    print("🎥 Renderizando vídeo final...")
    
    vf_final = f"ass={ass_path.name}" if tem_legenda else "scale=720:1280"
    
    cmd_final = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(lista_clips),
        "-i", str(audio),
        "-vf", vf_final,
        "-shortest",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    # Executar no diretório temp para evitar problemas de caminho com legendas
    result = subprocess.run(cmd_final, capture_output=True, text=True, cwd=temp_dir)
    
    if result.returncode != 0:
        print(f"❌ Erro no render final: {result.stderr}")
        # Tentar sem legenda se houver erro
        if tem_legenda:
            print("🔄 Tentando sem legenda...")
            cmd_final_sem_legenda = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(lista_clips),
                "-i", str(audio),
                "-vf", "scale=720:1280",
                "-shortest",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                str(output_path)
            ]
            subprocess.run(cmd_final_sem_legenda, check=True)
    
    print(f"✅ Vídeo final renderizado: {output_path}")
    
    # Verificar o vídeo final
    try:
        cmd_info = [
            'ffprobe', '-v', 'quiet',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=duration,width,height,nb_frames',
            '-of', 'csv=p=0',
            str(output_path)
        ]
        info_result = subprocess.run(cmd_info, capture_output=True, text=True)
        if info_result.returncode == 0:
            info = info_result.stdout.strip().split(',')
            print(f"📊 Vídeo final: {info[2]}x{info[3]}, {info[0]}s, {info[1]} frames")
        
        tamanho_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"📊 Tamanho do vídeo: {tamanho_mb:.1f} MB")
    except:
        print("📊 Estatísticas do vídeo não disponíveis")
    
    return output_path