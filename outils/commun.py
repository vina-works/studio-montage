"""Fonctions partagées par les outils : temps, mots horodatés, décodage audio, GPU, glossaire."""
import glob
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).parent
FILL = {"euh", "heu", "hum", "hmm", "mmh"}


def utf8():
    sys.stdout.reconfigure(encoding="utf-8")


def t(v):
    """Secondes depuis un nombre, « mm:ss.s » ou « hh:mm:ss.s »."""
    if isinstance(v, (int, float)) or v is None:
        return v
    s = 0.0
    for part in str(v).split(":"):
        s = s * 60 + float(part)
    return s


def fmt(x):
    return f"{int(x // 60):02d}:{x % 60:04.1f}"


def norm(s):
    return re.sub(r"[^\wàâäéèêëîïôöùûüç%]", "", s.lower())


def mots(transcript):
    """Mots de `.transcript.json`, avec l'identifiant du segment Whisper."""
    d = json.loads(Path(transcript).read_text(encoding="utf-8-sig"))
    return [dict(w, seg=s["id"]) for s in d["segments"] for w in s["words"]], d.get("duration")


def decode(media, sr=16000, canaux=1):
    """Piste audio complète en float32, `(n,)` en mono, `(n, canaux)` sinon."""
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(media), "-vn", "-ac", str(canaux), "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(pcm, dtype=np.float32)
    return x if canaux == 1 else x.reshape(-1, canaux)


def gpu():
    """Rend visibles les DLL CUDA installées par pip, à appeler avant d'importer faster_whisper."""
    for d in glob.glob(str(Path(sys.prefix) / "Lib" / "site-packages" / "nvidia" / "*" / "bin")):
        os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(d)


def whisper(modele="large-v3-turbo"):
    gpu()
    from faster_whisper import WhisperModel
    try:
        return WhisperModel(modele, device="cuda", compute_type="float16")
    except Exception as e:  # pas de carte, ou DLL absentes
        print(f"GPU indisponible ({e}), processeur utilisé.")
        return WhisperModel(modele, device="cpu", compute_type="int8")


def glossaire():
    return [(a, b) for a, b in json.loads((ICI / "glossaire.json").read_text(encoding="utf-8-sig"))["remplacements"]]


def appliquer_glossaire(s, regles=None):
    for a, b in regles or glossaire():
        s = re.sub(a, b, s)
    return s


def ffmpeg(*args, **kw):
    return subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True, **kw)


def sortie_vers_cible(edit, x):
    """Temps de sortie (montage) vers temps de la source cible."""
    T = 0.0
    for k in edit["keep"]:
        d = k["end"] - k["start"]
        if x < T + d:
            return k["start"] + x - T
        T += d
    return None


def cible_vers_sortie(edit, x, premier=True):
    """Temps de la source cible vers temps de sortie. `premier=False` prend la dernière occurrence (passage réutilisé)."""
    T, trouve = 0.0, None
    for k in edit["keep"]:
        if k["start"] - 0.2 <= x <= k["end"] + 0.2:
            v = T + min(max(0, x - k["start"]), k["end"] - k["start"])
            if premier:
                return v
            trouve = v
        T += k["end"] - k["start"]
    return trouve
