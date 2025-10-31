# short_filosofia.py - template com transições (xfade) entre clipes
import json
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

def render(audio_path: str, config: dict, roteiro) -> Path:
    audio = Path(audio_path)

    # ================== Configurações ==================
    images_dir = Path(config.get('IMAGES_DIR_SHORT') or config.get('IMAGE_DIR') or "./imagens")
    hook = roteiro.thumb
    num_imagens = int(config.get('num_imagens', 18))

    dur_fade = float(config.get('duracao_transicao', 1.2))    # duração do xfade (s)
    vfade = float(config.get('fade_out_video', 0.8))          # fade-out vídeo no final (s)
    afade = float(config.get('fade_out_audio', 0.8))          # fade-out áudio no final (s)

    width = int(config.get('largura', 720))
    height = int(config.get('altura', 1280))
    fps = int(config.get('fps', 30))

    output_dir, temp_dir = preparar_diretorios_trabalho(
        config.get('PASTA_VIDEOS') or config.get('output_dir', "./renders")
    )

    print(f"🎯 Hook: {hook}")
    print(f"📁 Imagens: {images_dir}")
    print(f"📁 Saída: {output_dir}")
    print(f"✨ Transição: xfade 'fade' ({dur_fade:.2f}s)")
    print(f"🌓 Fade final: vídeo={vfade:.2f}s | áudio={afade:.2f}s")
    print(f"📐 Tamanho: {width}x{height} @ {fps}fps")

    try:
        # ================== Coleta de entradas ==================
        imagens = listar_imagens(images_dir)
        if not imagens:
            raise ValueError(f"Nenhuma imagem encontrada em: {images_dir}")

        audio_duration = get_media_duration(audio)
        print(f"⏱️ Duração do áudio: {audio_duration:.3f}s")

        # Legenda (SRT -> ASS)
        ass_path = temp_dir / "legenda.ass"
        tem_legenda = False

        srt_name = re.sub(r'^(.*?)(?:_com_musica)?\.[^.]+$', r'\1.srt', audio.name, flags=re.IGNORECASE)
        srt_path = audio.with_name(srt_name)
        if srt_path.exists():
            try:
                srt_to_ass_karaoke(str(srt_path), str(ass_path), "vertical")
                tem_legenda = ass_path.exists() and ass_path.stat().st_size > 100
                print("✅ Legenda processada" if tem_legenda else "⚠️ Legenda vazia")
            except Exception as e:
                print(f"❌ Erro na legenda: {e}")

        # Embaralha e seleciona
        random.shuffle(imagens)
        imagens_selecionadas = imagens[:min(num_imagens, len(imagens))]

        # ================== Capa com hook ==================
        capa_path = temp_dir / "capa_com_hook.png"
        if imagens_selecionadas:
            primeira_imagem = imagens_selecionadas[0]
            gerar_capa_pillow(primeira_imagem, hook, capa_path)
            print(f"📝 Capa com hook gerada a partir de: {Path(primeira_imagem).name}")

        # ================== Preparação de saídas ==================
        video_id = audio.stem
        output_path = output_dir / f"{video_id}.mp4"

        clip_files = []
        clip_durations = []

        # Capa: 3–4s ou 10% do áudio
        duracao_capa = min(4.0, max(2.0, audio_duration * 0.10))

        try:
            capa_com_efeito = aplicar_efeito('camera_instavel', str(capa_path), duracao_capa)
            if capa_com_efeito and hasattr(capa_com_efeito, 'filename') and Path(capa_com_efeito.filename).exists():
                norm = normalizar_duracao(capa_com_efeito.filename, duracao_capa, fps=fps)
                if norm and Path(norm).exists():
                    destino = temp_dir / "capa_com_efeito.mp4"
                    shutil.copy2(norm, destino)
                    clip_files.append(destino)
                    clip_durations.append(float(duracao_capa))
                    Path(norm).unlink(missing_ok=True)
                    Path(capa_com_efeito.filename).unlink(missing_ok=True)
                    print("✅ Capa com hook e efeito criada")
        except Exception as e:
            print(f"❌ Erro na capa com hook: {e}")
            # Fallback capa estática
            try:
                fallback = temp_dir / "capa_estatica.mp4"
                criar_frame_estatico(capa_path, duracao_capa, fallback)
                clip_files.append(fallback)
                clip_durations.append(float(duracao_capa))
                print("✅ Fallback: capa estática criada")
            except Exception as e2:
                print(f"❌ Fallback da capa também falhou: {e2}")

        # ================== Geração de clipes restantes ==================
        tempo_restante = max(0.0, audio_duration - duracao_capa)
        imgs_restantes = imagens_selecionadas[1:] if len(imagens_selecionadas) > 1 else []

        print(f"📊 Tempo restante após capa: {tempo_restante:.3f}s")
        print(f"📊 Imagens restantes: {len(imgs_restantes)}")

        if imgs_restantes and tempo_restante > 0:
            n_total = len(imgs_restantes)
            duracao_por_imagem = tempo_restante / n_total
            full_on_min = float(config.get('min_full_on', 0.7))   
            step_alvo = max(tempo_restante / n_total, dur_fade + full_on_min)
            duracao_clip = max(step_alvo + dur_fade, 2*dur_fade + full_on_min)
            print(f"🧮 step_alvo={step_alvo:.3f}s | duracao_clip={duracao_clip:.3f}s (min full-on={full_on_min:.3f}s)")

            efeitos = ['camera_instavel', 'pan', 'zoom_invertido', 'panoramica_vertical', 'zoom_pulse']

            for i, img in enumerate(imgs_restantes):
                efeito = efeitos[i % len(efeitos)]
                try:
                    print(f"🎬 [{i+1}/{len(imgs_restantes)}] {Path(img).name} → {efeito} ({duracao_por_imagem:.2f}s)")
                    raw = aplicar_efeito(efeito, img, duracao_por_imagem)
                    if raw and hasattr(raw, 'filename') and Path(raw.filename).exists():
                        norm = normalizar_duracao(raw.filename, duracao_clip, fps=fps)
                        if norm and Path(norm).exists():
                            destino = temp_dir / f"clip_{i:03d}.mp4"
                            shutil.copy2(norm, destino)
                            clip_files.append(destino)
                            clip_durations.append(float(duracao_por_imagem))
                            Path(norm).unlink(missing_ok=True)
                            Path(raw.filename).unlink(missing_ok=True)
                except Exception as e:
                    print(f"   ❌ Erro no efeito {efeito}: {e}")
                    try:
                        destino = temp_dir / f"fallback_{i:03d}.mp4"
                        criar_frame_estatico(img, duracao_clip, destino)
                        clip_files.append(destino)
                        clip_durations.append(float(duracao_clip))
                        print(f"   ✅ Fallback estático criado")
                    except Exception as e2:
                        print(f"   ❌ Fallback também falhou: {e2}")

        if not clip_files:
            raise RuntimeError("Nenhum clipe foi gerado para montar o vídeo final.")

        total_video_sem_transicoes = sum(clip_durations)
        print(f"📊 Duração total dos clipes (sem sobreposição): {total_video_sem_transicoes:.3f}s")
        print(f"📊 Duração do áudio: {audio_duration:.3f}s")
        print(f"📊 Número de clipes: {len(clip_files)}")

        # ================== Render final com xfade ==================
        print("🎥 Montando com transições (xfade)...")

        # Áudio fixo no temp
        audio_temp = temp_dir / "audio_principal.mp3"
        if not audio_temp.exists():
            shutil.copy2(audio, audio_temp)
            print(f"✅ Áudio copiado: {audio_temp.name}")

        # Garante legenda no temp_dir
        if tem_legenda:
            ass_in_temp = temp_dir / "legenda.ass"
            if not ass_in_temp.exists():
                shutil.copy2(ass_path, ass_in_temp)
            tem_legenda = ass_in_temp.exists()
            print(f"📝 Legenda no temp_dir: {tem_legenda}")

        # ---------- Comando FFmpeg ----------
        cmd_final = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"]

        # Entradas de vídeo
        for cf in clip_files:
            cmd_final += ["-i", str(cf.name)]
        # Entrada de áudio (último input)
        cmd_final += ["-i", "audio_principal.mp3"]

        # ---------- Construção do filter_complex ----------
        fc_parts = []

        # 1) Pré-processamento (trim -> scale -> pad -> fps -> format) "Canva-style"
        for i, dur in enumerate(clip_durations):
            fc_parts.append(
                f"[{i}:v]trim=duration={dur:.3f},setpts=PTS-STARTPTS,"
                f"scale={width}:-1:force_original_aspect_ratio=decrease,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
                f"fps={fps},format=yuv420p[v{i}]"
            )

        # 2) Offsets corretos para xfade (modelo acumulado: começa em dur0 - dur_fade)
        offsets = []
        off = max(0.0, clip_durations[0] - dur_fade)  
        offsets.append(round(off, 3))
        for i in range(1, len(clip_durations)-1):
            off += clip_durations[i] - dur_fade
            offsets.append(round(off, 3))

        # 3) Encadeamento xfade
        current = "[v0]"
        for i in range(1, len(clip_files)):
            out = f"[x{i}]"
            fc_parts.append(
                f"{current}[v{i}]xfade=transition=fade:"
                f"duration={dur_fade:.3f}:offset={offsets[i-1]:.3f}{out}"
            )
            current = out

        # 4) Comprimento de vídeo resultante antes do tpad
        if len(clip_files) == 1:
            video_len = clip_durations[0]
        else:
            # fim real = último offset + duração do último clipe (porque o xfade começa em offset)
            video_len = offsets[-1] + clip_durations[-1]

        # 5) tpad (AQUI entra o tpad) para completar até o fim do áudio, se faltar vídeo
        delta_pad = audio_duration - video_len
        if delta_pad > 0.2:
            print(f"🧩 Aplicando tpad extra de {delta_pad:.3f}s para igualar ao áudio")
            fc_parts.append(f"{current}tpad=stop_duration={delta_pad:.3f}[vfinal]")
            current = "[vfinal]"

        # 6) Fade-out NO FINAL (calcular st_v e st_a AGORA, depois do tpad)
        #    Queremos que o fade aconteça nos últimos vfade/afade segundos do ÁUDIO.
        st_v = max(0.0, audio_duration - float(config.get('fade_out_video', 0.8)))
        st_a = max(0.0, audio_duration - float(config.get('fade_out_audio', 0.8)))

        # 7) Legendas + fade de VÍDEO (se quiser que a legenda NÃO fade, inverta a ordem: fade antes do ass)
        video_in = current.strip("[]")
        if tem_legenda:
            fc_parts.append(f"[{video_in}]ass=legenda.ass[vs]")
            fc_parts.append(f"[vs]fade=t=out:st={st_v:.3f}:d={float(config.get('fade_out_video', 0.8)):.3f},format=yuv420p[vout]")
        else:
            fc_parts.append(f"[{video_in}]fade=t=out:st={st_v:.3f}:d={float(config.get('fade_out_video', 0.8)):.3f},format=yuv420p[vout]")

        # 8) Fade-out de ÁUDIO (aplicado ao input de áudio que é o último input)
        fc_parts.append(f"[{len(clip_files)}:a]afade=t=out:st={st_a:.3f}:d={float(config.get('fade_out_audio', 0.8)):.3f}[aout]")

        filter_complex = "; ".join(fc_parts)

        # ---------- Mapeamento e codecs ----------
        cmd_final += [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path)
        ]


        print("🎬 Executando FFmpeg...")
        print(f"🔧 Filter complex: {filter_complex}")

        # Execução
        try:
            subprocess.run(cmd_final, check=True, cwd=temp_dir)
        except subprocess.CalledProcessError as e:
            print("❌ Erro no FFmpeg.")
            # Mostra um trecho do erro para debug rápido
            try:
                # Quando capture_output=False, stderr não está em e.stderr. Mantemos simples:
                pass
            except Exception:
                pass
            raise

        # Verificação final
        if output_path.exists():
            dur_out = get_media_duration(output_path)
            print(f"✅ Vídeo final gerado: {output_path}")
            print(f"⏱️ Duração (vídeo): {dur_out:.3f}s | ⏱️ Áudio (orig): {audio_duration:.3f}s")
            print(f"🔗 Clipes: {len(clip_files)} | ✨ Transições: {max(0, len(clip_files)-1)} xfade(s) de {dur_fade:.2f}s")
            if abs(dur_out - audio_duration) > 1.0:
                print("⚠️ Aviso: pequena diferença entre duração do áudio e do vídeo. Confira o tpad/fades.")
            return output_path
        else:
            raise RuntimeError("Vídeo final não foi criado.")

    except Exception as e:
        print(f"❌ Erro crítico no template: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        try:
            limpar_diretorio_temp(temp_dir)
        except Exception:
            pass
