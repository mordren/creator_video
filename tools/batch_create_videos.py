#!/usr/bin/env python3
"""
Cria multiplos videos para um canal existente usando as classes internas.

Uso:
  python tools/batch_create_videos.py --canal "Terror" --count 10 --tipo short --provider claude
  python tools/batch_create_videos.py --canal "Terror" --count 5 --tipo long --duracao 4
"""

import argparse
import random
import sys
from pathlib import Path
from typing import Optional, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from crud.manager import DatabaseManager  # type: ignore
from read_config import carregar_config_canal  # type: ignore
from texto import TextGenerator  # type: ignore
from audio import AudioSystem  # type: ignore
from video import VideoGenerator  # type: ignore


def carregar_temas(pasta_canal: Path) -> List[str]:
    possiveis = ["temas.txt", "topicos.txt", "assuntos.txt"]
    for nome in possiveis:
        arq = pasta_canal / nome
        if arq.exists():
            linhas = [l.strip() for l in arq.read_text(encoding="utf-8").splitlines()]
            return [l for l in linhas if l]
    return []


def criar_video(canal_nome: str, provider: Optional[str], tipo: str, duracao: Optional[int], tema: Optional[str]) -> bool:
    db = DatabaseManager()
    canal = db.canais.buscar_por_nome(canal_nome)
    if not canal:
        print(f"[ERRO] Canal '{canal_nome}' nao encontrado no banco.")
        return False

    config = carregar_config_canal(str(Path(canal.config_path) / "config.py"))
    gen = TextGenerator()

    if not tema:
        temas = carregar_temas(Path(canal.config_path))
        if temas:
            tema = random.choice(temas)
            print(f"[tema] {tema}")

    print(f"[GERAR] canal={canal_nome} provider={provider or config.get('TEXT_PROVIDER','gemini')} tipo={tipo} duracao={duracao or '-'}")

    roteiro = gen.gerar_roteiro(canal.config_path, tema, provider, tipo, duracao)
    if not roteiro:
        print("[ERRO] geracao de roteiro falhou.")
        return False

    salvo = gen.salvar_roteiro_completo(roteiro, config, tipo)
    roteiro_id = salvo.get('db_result', {}).get('id_banco')
    if not roteiro_id:
        print(f"[ERRO] nao consegui obter id do roteiro salvo: {salvo}")
        return False

    print(f"[OK] Roteiro salvo id={roteiro_id} id_video={salvo.get('id_roteiro')}")

    audio_ok = AudioSystem().generate_audio(int(roteiro_id))
    print(f"[AUDIO] {'ok' if audio_ok else 'falhou'}")
    if not audio_ok:
        return False

    #video_ok = VideoGenerator().gerar_video(int(roteiro_id))
    #print(f"[VIDEO] {'ok' if video_ok else 'falhou'}")
    #return bool(video_ok)


def main():
    p = argparse.ArgumentParser(description="Cria N videos para um canal")
    p.add_argument("--canal", required=True, help="Nome do canal ja cadastrado no banco")
    p.add_argument("--count", type=int, default=10, help="Quantidade de videos a criar (default: 10)")
    p.add_argument("--tipo", choices=["short", "long"], default="short", help="Tipo de video")
    p.add_argument("--provider", help="Provider de texto (ex.: claude, gemini, grok)")
    p.add_argument("--duracao", type=int, help="Duracao alvo (minutos) para ajustar tamanho de texto")
    p.add_argument("--tema", help="Tema fixo; se nao informado, escolhe aleatorio de temas.txt")
    args = p.parse_args()

    ok = 0
    for i in range(1, args.count + 1):
        print(f"\n===== [{i}/{args.count}] =====")
        try:
            if criar_video(args.canal, args.provider, args.tipo, args.duracao, args.tema):
                ok += 1
        except KeyboardInterrupt:
            print("[STOP] cancelado pelo usuario")
            break
        except Exception as e:
            print(f"[ERRO] {e}")

    print(f"\n[RESUMO] {ok}/{args.count} videos gerados com sucesso")


if __name__ == "__main__":
    main()