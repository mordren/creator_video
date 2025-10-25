#!/usr/bin/env python3
# short_sequencial.py - Template para vídeos shorts sequenciais de terror
import random
import shutil
import subprocess
from pathlib import Path

from video_maker.subtitle_tools import srt_to_ass_karaoke
from video_maker.video_engine import aplicar_efeito
from video_maker.video_utils import (
    get_media_duration, listar_imagens, quebrar_texto,
    criar_frame_estatico, normalizar_duracao, gerar_capa_pillow,
    preparar_diretorios_trabalho, limpar_diretorio_temp
)

def mixar_audio_com_musica(audio_voz, musica_path, ganho_musica=-15):
    """Mixa áudio de voz com música de fundo"""
    audio_path = Path(audio_voz)
    musica = Path(musica_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Áudio não encontrado: {audio_path}")
    if not musica.exists():
        raise FileNotFoundError(f"Música não encontrada: {musica}")

    saida = audio_path.with_name(f"{audio_path.stem}_com_musica.mp3")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_path),
        "-i", str(musica),
        "-filter_complex",
        f"[0:a]volume=0dB[a0];"
        f"[1:a]volume={ganho_musica}dB,aloop=loop=-1:size=2e+09[a1];"
        f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=2,"
        f"dynaudnorm=f=250:g=3[a]",
        "-map", "[a]",
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        "-ar", "48000",
        str(saida)
    ]

    subprocess.run(cmd, check=True, capture_output=True)
    return saida

def render(audio_path: str, config: dict) -> Path:
    """
    Template para vídeos curtos sequenciais de terror VERTICAL (720x1280)
    """
    audio = Path(audio_path)
    
    # Configurações
    images_dir = Path(config.get('IMAGES_DIR_SHORT') or config.get('IMAGE_DIR') or "./imagens")
    hook = config.get('hook', config.get('titulo', "HISTÓRIA DE TERROR"))
    num_imagens = config.get('num_imagens', 18)
    musica_path = config.get('MUSICA')
    
    # Configurar diretórios
    output_dir, temp_dir = preparar_diretorios_trabalho(
        config.get('PASTA_VIDEOS') or config.get('output_dir', "./renders")
    )
    
    print(f"🎯 Hook: {hook}")
    print(f"📁 Imagens: {images_dir}")
    print(f"📁 Saída: {output_dir}")
    
    try:
        # 1. Selecionar imagens
        imagens = listar_imagens(images_dir)
        if not imagens:
            raise ValueError(f"Nenhuma imagem encontrada em: {images_dir}")
        
        # Usar exatamente num_imagens, repetindo se necessário
        imagens_selecionadas = []
        while len(imagens_selecionadas) < num_imagens:
            imagens_selecionadas.extend(imagens)
        imagens_selecionadas = imagens_selecionadas[:num_imagens]
        random.shuffle(imagens_selecionadas)
        
        print(f"🎞️ Usando {len(imagens_selecionadas)} imagens")
        
        # 2. Obter duração do áudio
        audio_duration = get_media_duration(audio)
        print(f"⏱️ Duração do áudio: {audio_duration:.2f}s")
        
        # 3. Mixar áudio com música se disponível
        audio_final = audio
        if musica_path and Path(musica_path).exists():
            print("🎵 Mixando áudio com música...")
            audio_final = mixar_audio_com_musica(audio, musica_path)
            audio_duration = get_media_duration(audio_final)
            print(f"🎶 Áudio mixado: {audio_duration:.2f}s")
        
        # 4. Gerar capa
        capa_path = temp_dir / "capa.png"
        if imagens_selecionadas:
            gerar_capa_pillow(imagens_selecionadas[0], hook, capa_path)
            print(f"🖼️ Capa gerada: {capa_path}")
        
        # 5. Processar legendas
        ass_path = temp_dir / "legenda.ass"
        tem_legenda = False
        
        srt_path = audio.with_suffix('.srt')
        if srt_path.exists():
            try:
                srt_to_ass_karaoke(str(srt_path), str(ass_path), "vertical")
                tem_legenda = ass_path.exists() and ass_path.stat().st_size > 100
                print("✅ Legenda processada" if tem_legenda else "⚠️ Legenda vazia")
            except Exception as e:
                print(f"❌ Erro na legenda: {e}")
        
        # 6. Criar frame da capa (3 segundos)
        video_id = audio.stem
        output_path = output_dir / f"{video_id}.mp4"
        frame_capa_path = temp_dir / "000_capa.mp4"
        criar_frame_estatico(capa_path, 3.0, frame_capa_path)
        
        # 7. Processar imagens com efeitos
        rest = max(0.0, audio_duration - 3.0)
        imgs_restantes = imagens_selecionadas[1:]
        
        clips_norm = []
        if imgs_restantes and rest > 0:
            n = len(imgs_restantes)
            duracao_minima = 2.0
            
            # Ajustar número de imagens se áudio for curto
            if rest < n * duracao_minima:
                n = max(1, int(rest / duracao_minima))
                imgs_restantes = imgs_restantes[:n]
                rest = min(rest, n * duracao_minima)
            
            # Calcular durações
            base = rest / n
            durs = [max(duracao_minima, base)] * n
            durs[-1] += (rest - sum(durs))  # Ajuste fino
            
            print(f"📊 Durações calculadas: {[f'{d:.1f}s' for d in durs]}")
            
            # Gerar clipes com efeitos
            lista_clips = temp_dir / "lista_clips.txt"
            with open(lista_clips, "w", encoding="utf-8") as f:
                f.write(f"file '{frame_capa_path.name}'\n")
                
                efeitos = ['panoramica_vertical', 'zoom_invertido', 'pan', 'zoom_pulse', 'camera_instavel']
                
                for i, (img, seg) in enumerate(zip(imgs_restantes, durs)):
                    efeito = efeitos[i % len(efeitos)]
                    
                    try:
                        print(f"🎬 [{i+1}/{n}] {efeito} ({seg:.1f}s)...")
                        raw = aplicar_efeito(efeito, img, seg)
                        
                        if raw and hasattr(raw, 'filename') and Path(raw.filename).exists():
                            norm = normalizar_duracao(raw.filename, seg, fps=30)
                            if norm and Path(norm).exists():
                                nome_arquivo = f"clip_{i:03d}.mp4"
                                destino = temp_dir / nome_arquivo
                                shutil.copy2(norm, destino)
                                f.write(f"file '{nome_arquivo}'\n")
                                clips_norm.append(norm)
                                
                                # Limpar temporários
                                Path(norm).unlink(missing_ok=True)
                                Path(raw.filename).unlink(missing_ok=True)
                                print(f"   ✅ {nome_arquivo}")
                    except Exception as e:
                        print(f"   ❌ Erro: {e}")
        
        # 8. Render final
        print("🎥 Renderizando vídeo final...")
        
        # Copiar áudio para temp_dir
        audio_temp = temp_dir / audio_final.name
        if not audio_temp.exists():
            shutil.copy2(audio_final, audio_temp)
        
        # Configurar comando FFmpeg
        vf_filter = "ass=legenda.ass" if tem_legenda else "scale=720:1280:flags=lanczos"
        
        cmd_final = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", "lista_clips.txt",
            "-i", str(audio_temp),
            "-vf", vf_filter,
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        # Executar render
        result = subprocess.run(cmd_final, check=True, cwd=temp_dir, capture_output=True, text=True)
        
        if output_path.exists():
            duracao_final = get_media_duration(output_path)
            print(f"✅ Vídeo final: {output_path}")
            print(f"⏱️ Duração: {duracao_final:.2f}s")
            return output_path
        else:
            raise Exception("Vídeo final não foi criado")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no render: {e}")
        # Tentar sem legenda se falhou
        if tem_legenda:
            print("🔄 Tentando sem legenda...")
            cmd_final[cmd_final.index("-vf") + 1] = "scale=720:1280:flags=lanczos"
            try:
                subprocess.run(cmd_final, check=True, cwd=temp_dir, capture_output=True)
                return output_path if output_path.exists() else None
            except:
                pass
        return None
        
    except Exception as e:
        print(f"❌ Erro no template: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        limpar_diretorio_temp(temp_dir)