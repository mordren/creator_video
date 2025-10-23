# audio_joiner.py
from __future__ import annotations
import shutil, subprocess, json
from pathlib import Path
from typing import Optional

class FFmpegAudioJoiner:
    """
    Juntar trilha ao FINAL do áudio principal (concatenação), com opção de crossfade.
    Também expõe utilitários de checagem e duração via ffprobe.

    Requisitos: ffmpeg e ffprobe no PATH.
    """

    def __init__(self, ffmpeg_bin: str = "ffmpeg", ffprobe_bin: str = "ffprobe"):
        self.ffmpeg_bin = ffmpeg_bin
        self.ffprobe_bin = ffprobe_bin
        self._check_bins()

    # ---------- utilidades ----------
    def _check_bins(self) -> None:
        for b in (self.ffmpeg_bin, self.ffprobe_bin):
            if not shutil.which(b):
                raise EnvironmentError(f"'{b}' não encontrado no PATH.")

    @staticmethod
    def _db_to_linear(db: float) -> float:
        # volume=lin (FFmpeg): lin = 10^(dB/20)
        return 10 ** (db / 20.0)

    def get_duration_seconds(self, audio_path: Path) -> float:
        """Retorna duração em segundos usando ffprobe."""
        cmd = [
            self.ffprobe_bin, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(audio_path)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        return float(data["format"]["duration"])

    # ---------- operações ----------
    def append_track_after_voice(
        self,
        voice_path: Path,
        track_path: Path,
        out_path: Path,
        *,
        track_gain_db: float = 0.0,
        crossfade_sec: float = 0.0,
        sample_rate: int = 48000,
        channels: int = 2,
        codec: str = "mp3",
        bitrate: str = "192k",
    ) -> Path:
        """
        Junta a trilha ao FINAL do áudio de voz.
        - crossfade_sec = 0.0 => concat "seco"
        - crossfade_sec > 0   => usa acrossfade no encontro (suaviza a emenda)
        """
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        vol_lin = f"{self._db_to_linear(track_gain_db):.6f}"

        # Normaliza formatos para evitar problemas de concat (sr/chan/fmt)
        aformat = (
            f"aformat=sample_fmts=s16:channel_layouts="
            f"{'stereo' if channels == 2 else 'mono'}:sample_rates={sample_rate}"
        )

        if crossfade_sec and crossfade_sec > 0:
            # Crossfade sobre os últimos N segundos da voz com o começo da trilha
            # Saída ≈ len(voz) + len(trilha) - N
            filter_complex = (
                f"[0:a]{aformat},aresample=async=1:first_pts=0[v0];"
                f"[1:a]volume={vol_lin},{aformat},aresample=async=1:first_pts=0[m0];"
                f"[v0][m0]acrossfade=d={crossfade_sec}:c1=tri:c2=tri[out]"
            )
        else:
            # Concatenação direta (fim da voz -> início da trilha)
            # Exige mesmíssima taxa/canais — garantimos com aformat/aresample
            filter_complex = (
                f"[0:a]{aformat},aresample=async=1:first_pts=0[v0];"
                f"[1:a]volume={vol_lin},{aformat},aresample=async=1:first_pts=0[m0];"
                f"[v0][m0]concat=n=2:v=0:a=1[out]"
            )

        cmd = [
            self.ffmpeg_bin, "-y",
            "-i", str(voice_path),
            "-i", str(track_path),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", codec, "-b:a", bitrate,
            str(out_path),
        ]
        subprocess.run(cmd, check=True)
        return out_path

    def append_with_voice_fadeout(
        self,
        voice_path: Path,
        track_path: Path,
        out_path: Path,
        *,
        voice_fadeout_sec: float = 1.0,
        track_gain_db: float = 0.0,
        sample_rate: int = 48000,
        channels: int = 2,
        codec: str = "mp3",
        bitrate: str = "192k",
    ) -> Path:
        """
        Variante: faz um fade-out curto no fim da VOZ, depois concatena a trilha (sem crossfade).
        Útil para evitar "click" no ponto de emenda.
        """
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        dur = self.get_duration_seconds(voice_path)
        start_fade = max(dur - voice_fadeout_sec, 0.0)
        vol_lin = f"{self._db_to_linear(track_gain_db):.6f}"
        aformat = (
            f"aformat=sample_fmts=s16:channel_layouts="
            f"{'stereo' if channels == 2 else 'mono'}:sample_rates={sample_rate}"
        )

        filter_complex = (
            f"[0:a]{aformat},aresample=async=1:first_pts=0,"
            f"afade=t=out:st={start_fade:.3f}:d={voice_fadeout_sec:.3f}[v0];"
            f"[1:a]volume={vol_lin},{aformat},aresample=async=1:first_pts=0[m0];"
            f"[v0][m0]concat=n=2:v=0:a=1[out]"
        )

        cmd = [
            self.ffmpeg_bin, "-y",
            "-i", str(voice_path),
            "-i", str(track_path),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", codec, "-b:a", bitrate,
            str(out_path),
        ]
        subprocess.run(cmd, check=True)
        return out_path
