# video_maker/templates/short_filosofia.py

import random
import shutil
import subprocess
from pathlib import Path

from video_maker.subtitle_tools import srt_to_ass_karaoke
from video_maker.video_engine import aplicar_efeito
from video_maker.video_utils import gerar_capa, get_media_duration, listar_imagens

def criar_frame_estatico(imagem_path: Path, duracao: float, output_path: Path):
    """Cria um vídeo com frame estático a partir de uma imagem (igual ao simple.py)"""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(imagem_path),
        "-t", str(duracao),
        "-r", "30",
        "-vf", "scale=720:1280,format=yuv420p",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path

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
    ], check=True, capture_output=True)
    return str(out_path)

def render(audio_path: str, config: dict) -> Path:
    """
    Template para vídeos curtos de filosofia VERTICAL (720x1280)
    Versão melhorada e otimizada
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
            largura=720,
            altura=1280,
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
    
    # 6. CRIAR FRAME ESTÁTICO DA CAPA
    output_path = output_dir / f"{audio.stem}_filosofia.mp4"
    frame_capa_path = temp_dir / "000_capa.mp4"
    criar_frame_estatico(capa_path, 1.0, frame_capa_path)
    
    # 7. CONFIGURAR E VERIFICAR EFEITOS
    efeitos_disponiveis = [
        'panoramica_vertical',
        'zoom_invertido',
        'pan',
        'zoom_pulse',
        'camera_instavel',
    ]

    # Verificar quais efeitos estão funcionando
    efeitos_ativos = []
    print("🔍 Verificando efeitos...")
    for efeito in efeitos_disponiveis:
        try:
            teste = aplicar_efeito(efeito, imagens_selecionadas[0], 0.5)
            if teste and Path(teste.filename).exists() and Path(teste.filename).stat().st_size > 1024:
                efeitos_ativos.append(efeito)
                print(f"✅ {efeito}")
                # Limpar arquivo de teste
                Path(teste.filename).unlink(missing_ok=True)
            else:
                print(f"❌ {efeito} - Falhou no teste")
        except Exception as e:
            print(f"❌ {efeito} - {str(e)[:100]}")

    if not efeitos_ativos:
        raise Exception("❌ Nenhum efeito funcionando!")
    print(f"🎯 Efeitos ativos: {len(efeitos_ativos)}")

    # 8. PROCESSAR IMAGENS COM EFEITOS
    rest = max(0.0, float(audio_duration) - 1.0)  # Subtrair duração da capa
    imgs_restantes = imagens_selecionadas[1:]  # Pular a primeira (usada na capa)
    
    n = len(imgs_restantes)
    clips_norm = []
    
    if n > 0 and rest > 0:
        # Calcular durações com mínimo de 1.5 segundos por clipe
        duracao_minima = 1.5
        if rest < n * duracao_minima:
            # Ajustar número de imagens se áudio for muito curto
            n = max(1, int(rest / duracao_minima))
            imgs_restantes = imgs_restantes[:n]
            print(f"🔄 Ajustando para {n} imagens devido ao áudio curto")
            rest = min(rest, n * duracao_minima)
        
        base = rest / n
        durs = [max(duracao_minima, base)] * n  # Garantir duração mínima
        
        # Ajuste fino para fechar no total exato
        soma = sum(durs)
        if soma != rest:
            durs[-1] += (rest - soma)
        
        # Criar lista de concatenação
        lista_clips = temp_dir / "lista_clips.txt"
        
        with open(lista_clips, "w", encoding="utf-8") as f:
            f.write(f"file '{frame_capa_path.name}'\n")  # Capa primeiro
            
            for i, (img, seg) in enumerate(zip(imgs_restantes, durs)):
                nome_efeito = efeitos_ativos[i % len(efeitos_ativos)]
                
                try:
                    print(f"🎬 [{i+1}/{n}] {nome_efeito} ({seg:.1f}s)...")
                    
                    raw = aplicar_efeito(nome_efeito, img, seg)
                    
                    if raw and Path(raw.filename).exists() and Path(raw.filename).stat().st_size > 1024:
                        norm = normalizar_duracao(raw.filename, seg, fps=60)
                        if norm and Path(norm).exists():
                            f.write(f"file '{Path(norm).name}'\n")
                            clips_norm.append(norm)
                            print(f"   ✅ {Path(norm).name}")
                        else:
                            print(f"   ⚠️ Falha na normalização")
                    else:
                        print(f"   ⚠️ Efeito falhou")
                        
                except Exception as e:
                    print(f"   ❌ Erro: {e}")
    
    # 9. RENDER FINAL
    print("🎥 Renderizando vídeo final...")
    
    # Preparar arquivos necessários no temp_dir
    audio_temp = temp_dir / audio.name
    if not audio_temp.exists():
        shutil.copy2(audio, audio_temp)
    
    # Configurar filtro de vídeo
    vf_filter = "ass=legenda.ass" if tem_legenda else "scale=720:1280"
    
    # Comando final
    cmd_final = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", "lista_clips.txt",
        "-i", audio.name,
        "-vf", vf_filter,
        "-shortest",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "video_final.mp4"
    ]

    try:
        # Executar no temp_dir
        subprocess.run(cmd_final, check=True, cwd=temp_dir, capture_output=True)
        
        # Mover vídeo final
        video_final_temp = temp_dir / "video_final.mp4"
        if video_final_temp.exists():
            shutil.move(str(video_final_temp), str(output_path))
            print(f"✅ Vídeo final renderizado: {output_path}")
            
            # Verificar duração do resultado
            duracao_final = get_media_duration(output_path)
            print(f"⏱️ Duração do vídeo: {duracao_final:.2f}s")
        else:
            raise Exception("Vídeo final não foi criado")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no render: {e}")
        
        # Fallback: tentar sem legenda
        if tem_legenda:
            print("🔄 Tentando sem legenda...")
            cmd_final[cmd_final.index("-vf") + 1] = "scale=720:1280"
            subprocess.run(cmd_final, check=True, cwd=temp_dir, capture_output=True)
            
            video_final_temp = temp_dir / "video_final.mp4"
            if video_final_temp.exists():
                shutil.move(str(video_final_temp), str(output_path))
                print(f"✅ Vídeo final renderizado (sem legenda): {output_path}")
    
    # Limpeza opcional
    try:
        # Manter apenas o vídeo final e a capa
        for file in temp_dir.glob("*_norm.mp4"):
            file.unlink()
    except:
        pass
    
    return output_path