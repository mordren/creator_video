#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
maker.py - Template otimizado para vídeos longos - HORIZONTAL (1280x720)
Versão otimizada para performance
"""
import re
import argparse, random, subprocess, tempfile, os, sys
import time
import math
from pathlib import Path
import shutil

# Importações do sistema de templates
from video_maker.subtitle_tools import srt_to_ass_karaoke, srt_to_ass_simples
from video_maker.video_utils import (
    get_media_duration, listar_videos, preparar_diretorios_trabalho, 
    limpar_diretorio_temp
)

VIDEOS_DIR = {".mp4", ".mov", ".mkv", ".m4v", ".webm", ".avi"}

def run(cmd: list) -> None:
    """Executa comando com melhor tratamento de erro"""
    print(f"🔧 Executando: {' '.join(cmd[:4])}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erro FFmpeg (code {result.returncode})")
        print(f"   Detalhes: {result.stderr[:500]}...")
        raise subprocess.CalledProcessError(result.returncode, cmd)

def ffprobe_duration(path: Path) -> float:
    """Obtém duração de arquivo de mídia"""
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path)
        ], text=True, stderr=subprocess.DEVNULL)
        return float(out.strip())
    except Exception:
        return 0.0

def detect_hardware_acceleration():
    """Detecta a melhor aceleração de hardware disponível"""
    # Testa NVENC (NVIDIA)
    try:
        subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], 
                      capture_output=True, text=True, check=True)
        print("✅ NVENC disponível")
        return {
            'video_encoder': 'h264_nvenc',
            'preset': 'p4',  # Mais rápido que p5
            'quality': '-cq 23',  # Qualidade balanceada
            'pix_fmt': 'yuv420p'
        }
    except:
        pass
    
    # Testa QSV (Intel)
    try:
        subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], 
                      capture_output=True, text=True, check=True)
        print("✅ QSV disponível")
        return {
            'video_encoder': 'h264_qsv',
            'preset': 'fast',
            'quality': '-q 24',
            'pix_fmt': 'nv12'
        }
    except:
        pass
    
    # Fallback para CPU (mais lento)
    print("⚠️  Usando encoder de CPU (mais lento)")
    return {
        'video_encoder': 'libx264',
        'preset': 'medium',
        'quality': '-crf 23',
        'pix_fmt': 'yuv420p'
    }

def render(audio_path: str, config: dict, roteiro) -> Path:
    """
    Template OTIMIZADO para vídeos longos com vídeos pré-processados
    """
    inicio = time.time()
    audio = Path(audio_path)
    
    # Detectar aceleração de hardware
    hw_config = detect_hardware_acceleration()
    
    # ✅ CORREÇÃO CRÍTICA: Tratamento robusto para o diretório de vídeos
    videos_dir = config.get('VIDEOS_DIR')
    hook = config.get('hook', config.get('titulo', "CONTEÚDO RELIGIOSO"))        
    
    # Configurar diretórios
    output_dir, temp_dir = preparar_diretorios_trabalho(
        config.get('PASTA_VIDEOS') or config.get('output_dir', "./renders")
    )
    
    print(f"🎯 Hook: {hook}")
    print(f"📁 Vídeos: {videos_dir}")
    print(f"📁 Saída: {output_dir}")
    print(f"⚡ Aceleração: {hw_config['video_encoder']}")

    try:
        # 1. Validações
        if not audio.exists():
            raise FileNotFoundError(f"Áudio não encontrado: {audio}")
        
        # Obtém duração exata do áudio
        duracao_audio = ffprobe_duration(audio)
        print(f"🎵 Duração do áudio: {duracao_audio:.2f}s")

        # 2. Coleta vídeos pré-processados
        videos = [Path(v) for v in listar_videos(videos_dir)]
            
        if not videos:
            raise ValueError(f"❌ Nenhum vídeo encontrado em {videos_dir}")

        # 3. Seleção baseada em DURAÇÃO REAL (OTIMIZADA)
        print("📊 Calculando durações dos vídeos...")
        duracao_total = 0
        videos_selecionados = []
        
        # Embaralha os vídeos
        random.shuffle(videos)
        
        # Seleciona vídeos até ter duração suficiente + margem menor
        for video in videos:
            if duracao_total >= duracao_audio * 1.1:  # Reduzido para 10% de margem
                break
            duracao_video = ffprobe_duration(video)
            videos_selecionados.append(video)
            duracao_total += duracao_video
        
        # Se ainda não tem vídeos suficientes, recicla
        while duracao_total < duracao_audio:
            video = random.choice(videos)
            duracao_video = ffprobe_duration(video)
            videos_selecionados.append(video)
            duracao_total += duracao_video
            print(f"🔄 Reciclando vídeos... Duração atual: {duracao_total:.2f}s")

        print(f"🎬 Selecionados {len(videos_selecionados)} vídeos")
        print(f"📏 Duração total dos vídeos: {duracao_total:.2f}s (áudio: {duracao_audio:.2f}s)")

        # 4. Processar legendas ANTES da concatenação
        ass_path = temp_dir / "legenda.ass"
        tem_legenda = False
        
        srt_name = re.sub(r'^(.*?)(?:_com_musica)?\.[^.]+$', r'\1.srt', audio.name, flags=re.IGNORECASE)
        srt_path = audio.with_name(srt_name)
        if srt_path.exists():
            try:
                srt_to_ass_simples(str(srt_path), str(ass_path), "horizontal")
                tem_legenda = ass_path.exists() and ass_path.stat().st_size > 100
                print("✅ Legenda processada" if tem_legenda else "⚠️ Legenda vazia")
            except Exception as e:
                print(f"❌ Erro na legenda: {e}")

        # 5. Concatena vídeos COM legenda em UM ÚNICO PASSO (OTIMIZADO)
        def _ff_esc(p: Path) -> str:
            return str(p.resolve()).replace('\\', '/').replace(':', '\\:')

        lista_concat = temp_dir / "lista.txt"
        with open(lista_concat, "w", encoding="utf-8") as f:
            for video in videos_selecionados:
                caminho_absoluto = video.resolve().as_posix().replace("'", "'\\''")
                f.write(f"file '{caminho_absoluto}'\n")

        print("🎞️ Processamento único: concat + legenda + encode...")
        video_intermediario = temp_dir / "video_intermediario.mp4"

        # COMANDO ÚNICO OTIMIZADO: concat + legenda + encode acelerado
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(lista_concat),
        ]

        # Adiciona legenda se existir
        if tem_legenda and ass_path.exists():
            legenda_escaped = _ff_esc(ass_path)
            cmd += ["-vf", f"subtitles='{legenda_escaped}'"]

        # Parâmetros de encode OTIMIZADOS
        cmd += [
            "-an",  # Sem áudio por enquanto
            "-c:v", hw_config['video_encoder'],
            "-preset", hw_config['preset'],
        ]
        
        # Adiciona parâmetros de qualidade específicos
        if hw_config['video_encoder'] in ['h264_nvenc', 'h264_qsv']:
            cmd += ["-cq", "23", "-b:v", "0"]
        else:
            cmd += ["-crf", "23"]
            
        cmd += [
            "-pix_fmt", hw_config['pix_fmt'],
            "-movflags", "+faststart",
            "-t", str(duracao_audio),  # Corta no tempo exato
            str(video_intermediario)
        ]
        
        run(cmd)

        # 6. Verificação rápida
        duracao_concat = ffprobe_duration(video_intermediario)
        print(f"📹 Duração do vídeo processado: {duracao_concat:.2f}s")
        
        if duracao_concat < (duracao_audio - 1.0):
            print(f"❌ ERRO: Vídeo muito curto! ({duracao_concat:.2f}s < {duracao_audio:.2f}s)")
            return None

        # 7. MUX FINAL RÁPIDO (sem reencode)
        print("🔊 Mixando áudio final (mux rápido)...")
        video_id = audio.stem
        output_path = output_dir / f"{video_id}.mp4"

        # APENAS MUX - sem reencode de vídeo
        run([
            "ffmpeg", "-y",
            "-i", str(video_intermediario),
            "-i", str(audio),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",  # 🔥 CRÍTICO: Copia sem reencode
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path)
        ])
        
        # 8. Verificação final
        duracao_final = ffprobe_duration(output_path)
        
        # Cronometragem
        fim = time.time()
        duracao_total_processamento = fim - inicio
        minutos = int(duracao_total_processamento // 60)
        segundos = duracao_total_processamento % 60
        
        print(f"✅ Vídeo final: {output_path}")
        print(f"⏱️  Duração final: {duracao_final:.2f}s")
        print(f"⏱️  TEMPO TOTAL: {minutos}min {segundos:.1f}s")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Erro no template maker: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        limpar_diretorio_temp(temp_dir)

# Mantém a função main para uso direto se necessário
def main():
    inicio = time.time()
    print("⏰ Iniciando processamento...")
    
    ap = argparse.ArgumentParser(description="Cria vídeo longo com vídeos pré-processados")
    ap.add_argument("audio", help="Arquivo de áudio principal")
    ap.add_argument("--legenda", help="Arquivo de legenda .srt")
    args = ap.parse_args()

    # Configuração básica para uso direto
    config = {
        'VIDEOS_DIR': Path("C:/Users/mordren/Documents/creator/canais/religioso/assets/videos"),
        'MUSICA': None,
        'AUDIO_GAIN': '1.0',
        'BG_GAIN': '0.3',
        'PASTA_VIDEOS': "./renders"
    }
    
    resultado = render(args.audio, config, None)
    
    if resultado:
        print(f"🎉 Processamento concluído: {resultado}")
    else:
        print("❌ Falha no processamento")
        sys.exit(1)

if __name__ == "__main__":
    main()