#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
maker.py - Template para vídeos longos usando vídeos pré-processados
Agora funciona como template para o sistema video.py
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

def render(audio_path: str, config: dict) -> Path:
    """
    Template para vídeos longos com vídeos pré-processados - HORIZONTAL (1280x720)
    
    Args:
        audio_path: Caminho para o arquivo de áudio
        config: Dicionário de configuração
    
    Returns:
        Path: Caminho do vídeo gerado
    """
    inicio = time.time()
    audio = Path(audio_path)
    
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
    

    print(f"📂 Conteúdo do diretório de vídeos:")
    try:
        for item in videos_dir.iterdir():
            print(f"   - {item.name}")
    except Exception as e:
        print(f"❌ Erro ao listar diretório: {e}")
    
    try:
        # 1. Validações
        if not audio.exists():
            raise FileNotFoundError(f"Áudio não encontrado: {audio}")
        
        # Obtém duração exata do áudio
        duracao_audio = ffprobe_duration(audio)
        print(f"🎵 Duração do áudio: {duracao_audio:.2f}s")

        # 2. Coleta vídeos pré-processados
        videos = [Path(v) for v in listar_videos(videos_dir)]

        
        # ✅ DEBUG: Mostra vídeos encontrados
        print(f"🎬 Vídeos encontrados: {len(videos)}")
        for video in videos:
            print(f"   - {video.name}")
            
        if not videos:
            raise ValueError(f"❌ Nenhum vídeo encontrado em {videos_dir}")

        # 3. Seleção baseada em DURAÇÃO REAL
        print("📊 Calculando durações dos vídeos...")
        duracao_total = 0
        videos_selecionados = []
        
        # Embaralha os vídeos
        random.shuffle(videos)
        
        # Seleciona vídeos até ter duração suficiente + margem de segurança
        for video in videos:
            if duracao_total >= duracao_audio * 1.2:  # 20% a mais como margem
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

        # 5. Processar legendas
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

        # 6. Concatena vídeos
        def _ff_esc(p: Path) -> str:
            return str(p.resolve()).replace('\\', '/').replace(':', '\\:')

        lista_concat = temp_dir / "lista.txt"
        with open(lista_concat, "w", encoding="utf-8") as f:
            for video in videos_selecionados:
                caminho_absoluto = video.resolve().as_posix().replace("'", "'\\''")
                f.write(f"file '{caminho_absoluto}'\n")

        print("🎞️ Concat + legenda (1 só ffmpeg)...")
        video_intermediario = temp_dir / "video_intermediario.mp4"

        # Monta comando único: concat demuxer + subtitles (se houver) + corte no tamanho do áudio
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(lista_concat),
        ]

        if tem_legenda and ass_path.exists():
            legenda_escaped = _ff_esc(ass_path)
            cmd += ["-vf", f"subtitles='{legenda_escaped}'"]

        # Reencode sempre (há filtro e corte), sem áudio agora; áudio entra no mux final
        cmd += [
            "-an",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-movflags", "+faststart",
            "-t", str(duracao_audio),
            str(video_intermediario)
        ]
        run(cmd)

        # 7. Verificação crítica (agora sobre o intermediário já legendado)
        duracao_concat = ffprobe_duration(video_intermediario)
        print(f"📹 Duração do vídeo intermediário (com legenda): {duracao_concat:.2f}s")
        if duracao_concat < (duracao_audio - 0.5):  # tolerância pequena
            print(f"❌ ERRO: Vídeo muito curto! ({duracao_concat:.2f}s < {duracao_audio:.2f}s)")
            return None

        # 8. Mux final com o áudio do job (voz já mixada ou não, conforme você passou em `audio`)
        print("🔊 Mixando áudio final (mux)...")
        video_id = audio.stem
        output_path = output_dir / f"{video_id}.mp4"

        run([
            "ffmpeg", "-y",
            "-i", str(video_intermediario),
            "-i", str(audio),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_path)
        ])
        
        # 10. Verificação final
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
        'MUSICA': None,  # Definir se quiser música de fundo
        'AUDIO_GAIN': '1.0',
        'BG_GAIN': '0.3',
        'PASTA_VIDEOS': "./renders"
    }
    
    resultado = render(args.audio, config)
    
    if resultado:
        print(f"🎉 Processamento concluído: {resultado}")
    else:
        print("❌ Falha no processamento")
        sys.exit(1)

if __name__ == "__main__":
    main()