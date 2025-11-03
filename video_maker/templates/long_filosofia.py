

import random
import re
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

# Importar os efeitos horizontais
from video_maker.efeitos.pan import criar_video_pan_horizontal
from video_maker.efeitos.panoramica_vertical import criar_video_panoramica_horizontal
from video_maker.efeitos.zoom_invertido import criar_video_zoom_invertido_horizontal
from video_maker.efeitos.zoom_pulse import criar_video_pulse_horizontal
from video_maker.efeitos.camera_instavel import criar_video_camera_instavel_horizontal


def aplicar_efeito_horizontal(nome_efeito: str, img_path: str, temp: float):
    """Aplica efeitos na versão horizontal 16:9"""
    efeitos_horizontal = {
        'pan': criar_video_pan_horizontal,
        'panoramica_vertical': criar_video_panoramica_horizontal,
        'zoom_invertido': criar_video_zoom_invertido_horizontal,
        'zoom_pulse': criar_video_pulse_horizontal,
        'camera_instavel': criar_video_camera_instavel_horizontal,
    }
    
    if nome_efeito not in efeitos_horizontal:
        raise ValueError(f"Efeito horizontal '{nome_efeito}' não encontrado. Efeitos disponíveis: {list(efeitos_horizontal.keys())}")
    
    return efeitos_horizontal[nome_efeito](img_path, temp)

def render(audio_path: str, config: dict, roteiro) -> Path:
    """
    Template para vídeos LONGOS (16:9) com transições suaves
    - Formato horizontal 1280x720
    - Imagens aleatórias da pasta de longos
    - Transições com xfade
    - Capa com hook
    - Usa apenas efeitos horizontais disponíveis
    """
    audio = Path(audio_path)

    # Configurações para vídeos longos
    images_dir = Path(config.get('IMAGES_DIR_LONG') or config.get('IMAGE_DIR') or "./imagens_long")
    hook = roteiro.thumb
    num_imagens = config.get('num_imagens_long', 15)  # Mais imagens para vídeos longos
    dur_fade = float(config.get('duracao_transicao_long', 1.2))  # Transições mais longas
    width = 1280  # Fixo para 16:9
    height = 720   # Fixo para 16:9
    fps = int(config.get('fps_long', 30))

    # Configurar diretórios
    output_dir, temp_dir = preparar_diretorios_trabalho(
        config.get('PASTA_VIDEOS') or config.get('output_dir', "./renders_long")
    )

    print(f"🎯 Hook: {hook}")
    print(f"📁 Imagens Longas: {images_dir}")
    print(f"📁 Saída: {output_dir}")
    print(f"✨ Transição: xfade 'fade' ({dur_fade:.2f}s)")
    print(f"📐 Tamanho: {width}x{height} @ {fps}fps")
    print(f"🎲 Modo: Seleção aleatória de imagens")
    print(f"🎬 Efeitos: Versões horizontais 16:9")

    try:
        # 1. Selecionar imagens aleatoriamente
        imagens = listar_imagens(images_dir)
        if not imagens:
            raise ValueError(f"Nenhuma imagem encontrada em: {images_dir}")
        
        # Embaralhar e selecionar imagens
        random.shuffle(imagens)
        imagens_selecionadas = imagens[:min(num_imagens, len(imagens))]
        print(f"🎲 {len(imagens_selecionadas)} imagens selecionadas aleatoriamente")

        # 2. Obter duração do áudio
        audio_duration = get_media_duration(audio)
        print(f"⏱️ Duração do áudio: {audio_duration:.2f}s")

        # 3. Processar legendas
        ass_path = temp_dir / "legenda.ass"
        tem_legenda = False

        srt_name = re.sub(r'^(.*?)(?:_com_musica)?\.[^.]+$', r'\1.srt', audio.name, flags=re.IGNORECASE)
        srt_path = audio.with_name(srt_name)
        
        if srt_path.exists():
            try:
                srt_to_ass_karaoke(str(srt_path), str(ass_path), "horizontal")  # Legendas horizontais
                tem_legenda = ass_path.exists() and ass_path.stat().st_size > 100
                print("✅ Legenda processada" if tem_legenda else "⚠️ Legenda vazia")
            except Exception as e:
                print(f"❌ Erro na legenda: {e}")

        # 4. Gerar capa com hook (primeira imagem)
        capa_path = temp_dir / "capa_com_hook.png"
        if imagens_selecionadas:
            primeira_imagem = imagens_selecionadas[0]
            try:
                gerar_capa_pillow(primeira_imagem, hook, capa_path)
                print(f"📝 Capa com hook gerada a partir de: {Path(primeira_imagem).name}")
            except Exception as e:
                print(f"❌ Erro ao gerar capa: {e}")
                # Fallback: usar imagem diretamente
                capa_path = Path(primeira_imagem)

        # 5. CRIAR CLIPES (CAPA + OUTRAS IMAGENS) 
        video_id = audio.stem
        output_path = output_dir / f"{video_id}.mp4"

        clip_files = []
        clip_durations = []

        # Lista para debug
        lista_clips = temp_dir / "lista_clips.txt"
        with open(lista_clips, "w", encoding="utf-8") as f:
            f.write("")

        # CAPA com efeito especial (mais longa para vídeos longos)
        duracao_capa = min(6.0, max(3.0, audio_duration * 0.08))  # 8% do áudio

        capa_gerada = False
        try:
            print(f"🎬 [CAPA] zoom_pulse horizontal com hook ({duracao_capa:.1f}s)...")
            capa_com_efeito = aplicar_efeito_horizontal('zoom_pulse', str(capa_path), duracao_capa)

            if capa_com_efeito and hasattr(capa_com_efeito, 'filename') and Path(capa_com_efeito.filename).exists():
                norm_capa = normalizar_duracao(capa_com_efeito.filename, duracao_capa, fps=fps)
                if norm_capa and Path(norm_capa).exists():
                    nome_capa = "capa_com_efeito.mp4"
                    destino_capa = temp_dir / nome_capa
                    shutil.copy2(norm_capa, destino_capa)
                    clip_files.append(destino_capa)
                    clip_durations.append(duracao_capa)
                    with open(lista_clips, "a", encoding="utf-8") as f:
                        f.write(f"file '{nome_capa}'\n")
                    # Limpar temporários
                    Path(norm_capa).unlink(missing_ok=True)
                    Path(capa_com_efeito.filename).unlink(missing_ok=True)
                    capa_gerada = True
                    print("✅ Capa com hook e efeito horizontal criada")
        except Exception as e:
            print(f"❌ Erro na capa com hook horizontal: {e}")

        # Fallback: capa estática
        if not capa_gerada:
            try:
                fallback_capa = temp_dir / "capa_estatica.mp4"
                criar_frame_estatico(capa_path, duracao_capa, fallback_capa)
                clip_files.append(fallback_capa)
                clip_durations.append(duracao_capa)
                with open(lista_clips, "a", encoding="utf-8") as f:
                    f.write(f"file 'capa_estatica.mp4'\n")
                print("✅ Fallback: capa estática criada")
            except Exception as e2:
                print(f"❌ Fallback da capa também falhou: {e2}")

        # 6. Demais imagens (todas as imagens, incluindo a primeira se não foi usada na capa)
        tempo_usado = sum(clip_durations)
        rest = audio_duration - tempo_usado
        imgs_restantes = imagens_selecionadas[1:] if capa_gerada else imagens_selecionadas

        if imgs_restantes and rest > 0:
            n_total = len(imgs_restantes)
            duracao_minima = 3.0  # Mais longo para vídeos longos

            # Ajustar número de imagens conforme duração restante
            if rest < n_total * duracao_minima:
                n_total = max(1, int(rest / duracao_minima))
                imgs_restantes = imgs_restantes[:n_total]
                rest = min(rest, n_total * duracao_minima)

            # Calcular durações
            base = rest / n_total if n_total > 0 else rest
            durs = [max(duracao_minima, base) for _ in range(n_total)]
            
            # Ajustar a última duração para preencher o tempo
            if n_total > 0:
                diferenca = rest - sum(durs)
                if abs(diferenca) > 0.1:
                    durs[-1] += diferenca

            # USANDO APENAS EFEITOS HORIZONTAIS DISPONÍVEIS
            efeitos_horizontais = ['pan', 'panoramica_vertical', 'zoom_invertido', 'zoom_pulse', 'camera_instavel']
            print(f"🎬 Efeitos horizontais disponíveis: {efeitos_horizontais}")

            for i, (img, seg) in enumerate(zip(imgs_restantes, durs)):
                if seg < 1.0:  # Duração mínima prática
                    print(f"⏩ Pulando imagem {i+1}: duração muito curta ({seg:.1f}s)")
                    continue
                    
                efeito = efeitos_horizontais[i % len(efeitos_horizontais)]
                try:
                    print(f"🎬 [{i+1}/{n_total}] {Path(img).name} → {efeito}_horizontal ({seg:.1f}s)...")
                    raw = aplicar_efeito_horizontal(efeito, img, seg)

                    if raw and hasattr(raw, 'filename') and Path(raw.filename).exists():
                        norm = normalizar_duracao(raw.filename, seg, fps=fps)
                        if norm and Path(norm).exists():
                            nome_arquivo = f"clip_{i:03d}.mp4"
                            destino = temp_dir / nome_arquivo
                            shutil.copy2(norm, destino)
                            clip_files.append(destino)
                            clip_durations.append(float(seg))
                            with open(lista_clips, "a", encoding="utf-8") as f:
                                f.write(f"file '{nome_arquivo}'\n")
                            # Limpar temporários
                            Path(norm).unlink(missing_ok=True)
                            Path(raw.filename).unlink(missing_ok=True)
                except Exception as e:
                    print(f"   ❌ Erro no efeito {efeito}_horizontal: {e}")
                    # Fallback: criar clipe estático
                    try:
                        nome_arquivo = f"fallback_{i:03d}.mp4"
                        fallback_path = temp_dir / nome_arquivo
                        criar_frame_estatico(img, seg, fallback_path)
                        clip_files.append(fallback_path)
                        clip_durations.append(float(seg))
                        with open(lista_clips, "a", encoding="utf-8") as f:
                            f.write(f"file '{nome_arquivo}'\n")
                        print(f"   ✅ Fallback estático criado")
                    except Exception as fallback_error:
                        print(f"   ❌ Fallback também falhou: {fallback_error}")
        else:
            print("⚠️  Não há imagens suficientes para continuar após a capa")

        if not clip_files:
            raise RuntimeError("Nenhum clipe foi gerado para montar o vídeo final.")

        print(f"📊 Resumo: {len(clip_files)} clipes, {sum(clip_durations):.1f}s de vídeo")

        # 7. RENDER FINAL COM XFADE
        print("🎥 Montando vídeo longo com transições...")

        # Copiar áudio para temp_dir
        audio_temp = temp_dir / audio.name
        if not audio_temp.exists():
            shutil.copy2(audio, audio_temp)

        # Construir comando FFmpeg
        cmd_final = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"]

        # Adicionar cada clipe como input
        for cf in clip_files:
            cmd_final += ["-i", str(cf.name)]

        # Adicionar o áudio como último input
        cmd_final += ["-i", str(audio_temp.name)]

        # Construir filter_complex para xfade
        filter_parts = []
        
        # 1. Pré-processamento de cada vídeo
        for idx in range(len(clip_files)):
            filter_parts.append(f"[{idx}:v]scale={width}:{height}:flags=lanczos,fps={fps},format=yuv420p,setpts=PTS-STARTPTS[v{idx}]")

        # 2. Encadeamento com xfade
        if len(clip_files) == 1:
            current = "v0"
        else:
            current = "v0"
            accumulated_time = 0.0
            
            for i in range(1, len(clip_files)):
                # xfade offset deve começar nos últimos 'dur_fade' segundos
                # do input 1 (timeline acumulada até o clipe i-1), o que resulta em:
                #   offset_i = (dur0 + ... + dur{i-1}) - i*dur_fade
                # usando accumulated_time como soma até i-2, somamos o dur do (i-1)
                offset = (accumulated_time + clip_durations[i-1]) - (i * dur_fade)
                if offset < 0:
                    offset = 0.0
                output_label = f"xfade{i}"

                filter_parts.append(
                    f"[{current}][v{i}]xfade=transition=fade:duration={dur_fade:.3f}:offset={offset:.3f}[{output_label}]"
                )
                current = output_label
                accumulated_time += clip_durations[i-1]

        # 3. Aplicar legenda se existir
        video_output = current
        if tem_legenda and ass_path.exists():
            filter_parts.append(f"[{video_output}]ass={ass_path.name}[vout]")
            video_output = "vout"

        filter_complex = ";".join(filter_parts)

        # Comando final
        cmd_final += [
            "-filter_complex", filter_complex,
            "-map", f"[{video_output}]",
            "-map", f"{len(clip_files)}:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            "-r", str(fps),
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]

        # Executar render
        try:
            print("🔧 Executando FFmpeg para vídeo longo...")
            result = subprocess.run(cmd_final, check=True, cwd=temp_dir, capture_output=True, text=True, timeout=600)
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro no FFmpeg (xfade): {e}")
            if e.stderr:
                print(f"🔍 STDERR: {e.stderr[:500]}...")
            
            # Tentar fallback sem legenda
            if "ass=" in filter_complex:
                print("🔄 Tentando sem legenda...")
                filter_simple = ";".join([part for part in filter_parts if "ass=" not in part])
                cmd_simple = [
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"
                ]
                for cf in clip_files:
                    cmd_simple += ["-i", str(cf.name)]
                cmd_simple += ["-i", str(audio_temp.name)]
                cmd_simple += [
                    "-filter_complex", filter_simple,
                    "-map", "[vout]" if "vout" in filter_simple else f"[{current}]",
                    "-map", f"{len(clip_files)}:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart",
                    "-r", str(fps), "-pix_fmt", "yuv420p",
                    str(output_path)
                ]
                try:
                    subprocess.run(cmd_simple, check=True, cwd=temp_dir, timeout=600)
                except subprocess.CalledProcessError as e2:
                    print(f"❌ Também falhou sem legenda: {e2}")
                    return None

        if output_path.exists():
            duracao_final = get_media_duration(output_path)
            print(f"✅ VÍDEO LONGO gerado: {output_path}")
            print(f"⏱️ Duração: {duracao_final:.2f}s")
            print(f"🎬 Clipes: {len(clip_files)}")
            print(f"✨ Transições: {max(0, len(clip_files)-1)}")
            print(f"📐 Formato: 16:9 ({width}x{height})")
            print(f"🎯 Efeitos: Todos horizontais")
            return output_path
        else:
            raise Exception("Vídeo final não foi criado")

    except Exception as e:
        print(f"❌ Erro crítico no template longo: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        try:
            limpar_diretorio_temp(temp_dir)
        except Exception:
            pass