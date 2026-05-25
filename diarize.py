#!/usr/bin/env python3
"""
Diarización de Speakers
Detecta cuántas personas hablan en un vídeo/audio y cuándo habla cada una.

Uso:
  python diarize.py video.mp4
  python diarize.py https://youtube.com/watch?v=xxx
  python diarize.py audio.wav --num-speakers 2 --output resultado.json

Requisitos previos:
  1. pip install -r requirements.txt
  2. Crear cuenta en https://huggingface.co (gratis)
  3. Aceptar términos en https://huggingface.co/pyannote/speaker-diarization-3.1
  4. Obtener token en https://huggingface.co/settings/tokens
  5. export HF_TOKEN=hf_xxxx   (o usar --token hf_xxxx)
"""

import json
import sys
import os
import argparse
import subprocess
from pathlib import Path


def fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ds = int((seconds % 1) * 10)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}.{ds}"
    return f"{m:02d}:{s:02d}.{ds}"


def download_youtube(url: str) -> str:
    out_template = "audio_yt_temp.%(ext)s"
    cmd = [
        "yt-dlp", "-x",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "--no-playlist",
        "-o", out_template,
        url,
    ]
    print("[1/3] Descargando audio de YouTube...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp falló:\n{r.stderr}")

    for ext in ["wav", "webm", "m4a", "mp3", "ogg", "opus"]:
        path = f"audio_yt_temp.{ext}"
        if os.path.exists(path):
            return path
    raise RuntimeError("No se encontró el archivo de audio descargado.")


def convert_to_wav(input_path: str) -> str:
    out = "audio_converted_16k.wav"
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ar", "16000",
        "-ac", "1",
        "-f", "wav",
        out,
    ]
    print("[2/3] Convirtiendo a WAV 16 kHz mono...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg falló:\n{r.stderr}")
    return out


def run_diarization(wav_path: str, hf_token: str, num_speakers: int | None) -> list:
    print("[3/3] Ejecutando diarización de speakers...")
    print("      (Puede tardar varios minutos según la duración del vídeo)")

    from pyannote.audio import Pipeline
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"      Dispositivo: {device.upper()}")

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token,
    )
    pipeline.to(torch.device(device))

    kwargs = {}
    if num_speakers:
        kwargs["num_speakers"] = num_speakers

    diarization = pipeline(wav_path, **kwargs)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        duration = turn.end - turn.start
        if duration < 0.3:
            continue
        segments.append({
            "speaker": speaker,
            "start": round(turn.start, 3),
            "end": round(turn.end, 3),
            "duration": round(duration, 3),
        })

    return segments


def print_summary(segments: list, speakers: list):
    width = 65
    print("\n" + "═" * width)
    print("  RESULTADO — DIARIZACIÓN DE SPEAKERS")
    print("═" * width)
    print(f"\n  Personas detectadas: {len(speakers)}")

    for sp in speakers:
        sp_segs = [s for s in segments if s["speaker"] == sp]
        total = sum(s["duration"] for s in sp_segs)
        print(f"    → {sp}:  {len(sp_segs)} segmentos  ·  {fmt_time(total)} hablando")

    print(f"\n  Segmentos cronológicos ({len(segments)} total):")
    print("  " + "─" * (width - 2))

    for seg in segments:
        bar_len = min(int(seg["duration"] * 2.5), 28)
        bar = "█" * bar_len
        print(
            f"  {seg['speaker']:<15}  "
            f"{fmt_time(seg['start'])} → {fmt_time(seg['end'])}  "
            f"{bar}"
        )

    print("═" * width + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Detecta cuántas personas hablan en un vídeo y cuándo habla cada una.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python diarize.py video.mp4
  python diarize.py https://youtube.com/watch?v=XXXX
  python diarize.py audio.wav --num-speakers 2
  python diarize.py video.mp4 --token hf_xxxx --output mis_speakers.json
        """,
    )
    parser.add_argument("input", help="URL de YouTube o ruta a archivo de vídeo/audio")
    parser.add_argument(
        "--token",
        help="Token de HuggingFace (alternativa: variable de entorno HF_TOKEN)",
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        metavar="N",
        help="Número exacto de speakers si ya lo sabes (mejora la precisión)",
    )
    parser.add_argument(
        "--output",
        default="speakers.json",
        metavar="ARCHIVO",
        help="Ruta del JSON de salida (default: speakers.json)",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="No eliminar archivos de audio temporales",
    )
    args = parser.parse_args()

    hf_token = args.token or os.environ.get("HF_TOKEN")
    if not hf_token:
        print("\n❌  Token de HuggingFace no encontrado.\n")
        print("  Pasos para obtenerlo GRATIS:")
        print("  1. Crea cuenta en https://huggingface.co")
        print("  2. Acepta los términos del modelo en:")
        print("     https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("  3. Crea tu token en: https://huggingface.co/settings/tokens")
        print("  4. Úsalo así:")
        print("       export HF_TOKEN=hf_xxxx")
        print("     o bien:")
        print("       python diarize.py video.mp4 --token hf_xxxx\n")
        sys.exit(1)

    temp_files = []

    try:
        is_url = args.input.startswith(("http://", "https://"))

        if is_url:
            raw_path = download_youtube(args.input)
            temp_files.append(raw_path)
            audio_path = raw_path
        else:
            if not os.path.exists(args.input):
                print(f"❌  Archivo no encontrado: {args.input}")
                sys.exit(1)
            audio_path = args.input

        if not audio_path.lower().endswith(".wav"):
            wav_path = convert_to_wav(audio_path)
            temp_files.append(wav_path)
        else:
            wav_path = convert_to_wav(audio_path)
            temp_files.append(wav_path)

        segments = run_diarization(wav_path, hf_token, args.num_speakers)

        if not segments:
            print("\n⚠️  No se detectaron segmentos de voz. Revisa el archivo de audio.")
            sys.exit(1)

        speakers = sorted(set(s["speaker"] for s in segments))

        result = {
            "num_speakers": len(speakers),
            "speakers": speakers,
            "total_segments": len(segments),
            "duration": round(max(s["end"] for s in segments), 3),
            "segments": segments,
        }

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print_summary(segments, speakers)
        print(f"  ✅  Resultados guardados en: {args.output}")
        print(f"  →  Abre equalizador_speakers.html y carga este JSON + tu vídeo.\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso cancelado.")
    except Exception as exc:
        print(f"\n❌  Error: {exc}")
        sys.exit(1)
    finally:
        if not args.keep_temp:
            for f in temp_files:
                if os.path.exists(f):
                    os.remove(f)


if __name__ == "__main__":
    main()
