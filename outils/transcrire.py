"""Transcrit une vidéo/audio avec timestamps au mot.

Usage : transcrire video.mp4 [--lang fr] [--model large-v3-turbo] [--cpu]
Par défaut : carte NVIDIA si dispo (rapide), sinon bascule automatiquement sur le processeur.
Sorties à côté de la vidéo :
  video.transcript.json  -> segments + mots horodatés (ce que Claude lit pour monter)
  video.transcript.md    -> transcription lisible (paragraphes horodatés), à ouvrir/relire
  video.srt              -> sous-titres
"""
import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path


def add_nvidia_dlls() -> None:
    """Windows : rend visibles les DLL CUDA installées via pip (nvidia-cublas-cu12, nvidia-cudnn-cu12)."""
    site = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    for d in glob.glob(str(site / "*" / "bin")):
        os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(d)


def patch_av_open() -> None:
    """faster-whisper passe metadata_errors à av.open, argument refusé par les versions récentes de PyAV."""
    import av

    original = av.open

    def open_compat(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return original(*args, **kwargs)

    av.open = open_compat


def ts(t: float, srt: bool = False) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    if srt:
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    return f"{int(h):02d}:{int(m):02d}:{s:04.1f}"


def to_markdown(name: str, duration: float, segs: list, pause: float = 2.0) -> str:
    """Paragraphe nouveau à chaque pause > `pause` s ; chaque phrase garde son horodatage."""
    md = [f"# Transcription — {name}", "", f"Durée : {ts(duration)} · {len(segs)} segments", "", "---", ""]
    para, prev_end = [], None
    for s in segs:
        if para and prev_end is not None and s["start"] - prev_end > pause:
            md += [" ".join(para), ""]
            para = []
        para.append(f"`[{ts(s['start'])}]` {s['text']}")
        prev_end = s["end"]
    if para:
        md += [" ".join(para), ""]
    return "\n".join(md)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("media")
    p.add_argument("--lang", default="fr")
    p.add_argument("--model", default="large-v3-turbo")
    p.add_argument("--cpu", action="store_true", help="forcer le processeur (sans carte graphique)")
    a = p.parse_args()

    src = Path(a.media).expanduser().resolve()
    if not src.exists():
        sys.exit(f"Fichier introuvable : {src}")

    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    add_nvidia_dlls()
    patch_av_open()
    from faster_whisper import WhisperModel

    def run(device: str, compute: str):
        model = WhisperModel(a.model, device=device, compute_type=compute)
        segments, info = model.transcribe(
            str(src), language=a.lang, word_timestamps=True, vad_filter=True
        )
        out, srt = [], []
        for i, seg in enumerate(segments, 1):
            words = [
                {"w": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2)}
                for w in (seg.words or [])
            ]
            text = seg.text.strip()
            out.append({"id": i, "start": round(seg.start, 2), "end": round(seg.end, 2), "text": text, "words": words})
            srt.append(f"{i}\n{ts(seg.start, True)} --> {ts(seg.end, True)}\n{text}\n")
            print(f"\r[{device}] {ts(seg.end)} / {ts(info.duration)}", end="", flush=True)
        return out, srt, info

    t0 = time.time()
    if a.cpu:
        out, srt, info = run("cpu", "int8")
    else:
        try:
            out, srt, info = run("cuda", "float16")
        except Exception as e:  # pas de GPU, DLL CUDA manquantes, archi non supportée...
            print(f"\nGPU indisponible ({e}). Bascule sur le processeur.")
            out, srt, info = run("cpu", "int8")

    base = src.with_suffix("")
    Path(f"{base}.transcript.json").write_text(
        json.dumps({"source": src.name, "duration": round(info.duration, 2), "segments": out}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    Path(f"{base}.transcript.md").write_text(to_markdown(src.name, info.duration, out), encoding="utf-8")
    Path(f"{base}.srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"\nOK en {time.time() - t0:.0f} s -> {base}.transcript.md / .json / .srt")


if __name__ == "__main__":
    main()
