"""Plan éditorial (segments à garder) -> edit.json, avec le rythme : hésitations, faux départs, pauses.

Usage :
  python rythme.py plan.json -o edit.json [--rapport rapport.md]

Le plan donne les segments en temps de la transcription (le MP3 par exemple) ; `offset` les convertit
en temps de la source vidéo. Voir wiki/02-plan-editorial-et-rythme.md.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from commun import FILL, cible_vers_sortie, decode, fmt, mots, norm, t, utf8

REGLAGES = {  # V2, validée sur l'épisode 1
    "marge": 0.15, "pause_phrase": 0.50, "pause_idee": 0.80, "pause_hesitation": 0.40,
    "depassement_min": 0.25, "trou_hesitation_min": 0.65, "idee_si_pause_de": 1.2, "trou_bruite_garde": 1.0,
    "seuil_silence_db": -35, "fps": 30,
}


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("-o", "--sortie", default="edit.json")
    ap.add_argument("--rapport")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8-sig"))
    base = Path(args.plan).parent
    R = {**REGLAGES, **plan.get("reglages", {})}
    W, _ = mots(base / plan["transcription"])
    for c in plan.get("mots_corriges", []):  # Whisper étire parfois un mot sur ses voisins
        w = min(W, key=lambda w: abs(w["start"] - t(c["pres_de"])))
        w["start"], w["end"] = t(c.get("debut", w["start"])), t(c.get("fin", w["end"]))
    W2 = json.loads((base / plan["hesitations"]).read_text(encoding="utf-8-sig")) if plan.get("hesitations") else []
    audio = decode(base / plan["audio_transcription"]) if plan.get("audio_transcription") else None
    offset, fps = plan.get("offset", 0.0), R["fps"]

    def word_at(x):
        return min(range(len(W)), key=lambda i: abs(W[i]["start"] - x))

    removed, flags, dead = [], [], set()
    stats = dict(pauses=0, hesitations_trou=0, reactions=0, bruits=0)
    for f in plan.get("faux_departs", []):
        i, j = word_at(t(f["debut"])), word_at(t(f["reprise"]))
        dead.update(range(i, j))
        removed.append(("faux départ", W[i]["start"], W[j]["start"], " ".join(w["w"] for w in W[i:j]) + " : " + f.get("pourquoi", "")))
    garder = [t(x) for x in plan.get("garder_mots", [])]  # « bah » ou « ben » qui portent la phrase
    for i, w in enumerate(W):
        if norm(w["w"]) in FILL and i not in dead and not any(abs(w["start"] - g) < 0.15 for g in garder):
            dead.add(i)
            removed.append(("hésitation", w["start"], w["end"], w["w"]))
    for c in plan.get("couper_mots", []):
        i = word_at(t(c))
        dead.add(i)
        removed.append(("hésitation", W[i]["start"], W[i]["end"], W[i]["w"]))

    def in_gap(x, y):
        return [w for w in W2 if x + 0.02 <= (w["start"] + w["end"]) / 2 < y - 0.02]

    def bruite(x, y):
        if audio is None or y - x < 0.1:
            return False
        seg = audio[int(x * 16000): int(y * 16000)]
        fr = seg[: len(seg) // 400 * 400].reshape(-1, 400)
        db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
        return float((db < R["seuil_silence_db"]).mean()) < 0.3

    out = []
    for s in plan["segments"]:
        bloc, a, z = s["bloc"], t(s["debut"]), t(s["fin"])
        if s.get("brut"):  # générique, musique : on garde tel quel
            out.append({"bloc": bloc, "start": a, "end": z})
            continue
        lw = [(i, W[i]) for i in range(len(W)) if a - 0.06 <= W[i]["start"] < z - 0.05 and i not in dead]
        if not lw:
            continue
        pieces, cur = [], [lw[0][1]["start"], lw[0][1]["end"]]
        for (ip, p), (iq, q) in zip(lw, lw[1:]):
            between = in_gap(p["end"], q["start"]) if iq == ip + 1 else []
            names = [norm(w["w"]) for w in between if norm(w["w"])]
            has_fill = any(n in FILL for n in names)
            real = [n for n in names if n not in FILL and n not in (norm(p["w"]), norm(q["w"]))]
            dup = [w for w in between if norm(w["w"]) == norm(q["w"])]
            qstart = min(q["start"], dup[0]["start"]) if dup else q["start"]
            g = qstart - p["end"]
            if iq != ip + 1:  # une prise ou un « euh » retiré entre les deux
                pieces.append((cur[0], p["end"] + min(R["marge"], max(g, 0) / 2)))
                cur = [qstart - min(R["marge"], max(g, 0) / 2), q["end"]]
                continue
            if real and not has_fill:  # relance, réaction d'un autre : on ne touche pas
                stats["reactions"] += g >= 0.4
                cur[1] = q["end"]
                continue
            question = p["w"].endswith("?") or any("?" in w["w"] for w in between)
            if has_fill and g >= R["trou_hesitation_min"]:
                stats["hesitations_trou"] += 1
                removed.append(("hésitation", p["end"], qstart, " ".join(w["w"] for w in between)))
                cible = R["pause_hesitation"]
            elif not names and g >= R["trou_bruite_garde"] and bruite(p["end"], qstart):
                stats["bruits"] += 1
                flags.append((p["end"], f"trou de {g:.1f} s non silencieux gardé après « {p['w']} » (rire ou chevauchement probable)"))
                cur[1] = q["end"]
                continue
            else:
                cible = R["pause_idee"] if (question or g >= R["idee_si_pause_de"]) else R["pause_phrase"]
            if g > cible + R["depassement_min"]:
                stats["pauses"] += cible != R["pause_hesitation"]
                pieces.append((cur[0], p["end"] + cible / 2))
                cur = [qstart - cible / 2, q["end"]]
            else:
                cur[1] = q["end"]
        pieces.append((cur[0], cur[1]))
        fi, li = lw[0][0], lw[-1][0]
        prev_end = W[fi - 1]["end"] if fi else 0
        next_start = W[li + 1]["start"] if li + 1 < len(W) else 1e9
        s0 = max(lw[0][1]["start"] - R["marge"], (prev_end + lw[0][1]["start"]) / 2)
        e0 = min(lw[-1][1]["end"] + R["marge"], (next_start + lw[-1][1]["end"]) / 2)
        pieces[0] = (t(s.get("debut_force")) or s0, pieces[0][1])
        pieces[-1] = (pieces[-1][0], t(s.get("fin_force")) or e0)
        for x, y in pieces:
            out.append({"bloc": bloc, "start": x, "end": y})

    for c in plan.get("coupes", []):  # coupes à la main, en temps transcription
        ca, cz, nxt = t(c["debut"]), t(c["fin"]), []
        for s in out:
            if cz <= s["start"] or ca >= s["end"]:
                nxt.append(s)
            else:
                if ca > s["start"]:
                    nxt.append({**s, "end": ca})
                if cz < s["end"]:
                    nxt.append({**s, "start": cz})
        out = nxt
        removed.append(("coupe", ca, cz, c.get("pourquoi", "")))

    keep = []
    for s in out:
        A, Z = round((s["start"] + offset) * fps) / fps, round((s["end"] + offset) * fps) / fps
        if keep and keep[-1]["why"] == s["bloc"] and abs(keep[-1]["end"] - A) < 0.02:
            keep[-1]["end"] = round(Z, 3)
        elif Z > A:
            keep.append({"start": round(A, 3), "end": round(Z, 3), "why": s["bloc"]})
    if plan.get("fin_cible"):  # la source cible continue (rire, cartes de fin) au-delà du dernier mot
        keep[-1]["sous_titres_jusqu_a"] = keep[-1]["end"]
        keep[-1]["end"] = t(plan["fin_cible"])
    edit = {"source": plan["source"], "offset": offset, "keep": keep}
    Path(args.sortie).write_text(json.dumps(edit, ensure_ascii=False, indent=1), encoding="utf-8")

    total = sum(k["end"] - k["start"] for k in keep)
    brut = sum(t(s["fin"]) - t(s["debut"]) for s in plan["segments"])
    hes = [r for r in removed if r[0] == "hésitation" and r[2] > r[1]]
    fs = [r for r in removed if r[0] == "faux départ"]
    lignes = [
        f"# Bilan de rythme : {Path(args.sortie).name}", "",
        f"- Segments : {len(keep)}",
        f"- Durée du plan éditorial : {fmt(brut)}, après rythme : {fmt(total)}",
        f"- Hésitations coupées : {len(hes)} (dont {stats['hesitations_trou']} trouvées par la seconde passe)",
        f"- Faux départs retirés : {len(fs)}",
        f"- Pauses raccourcies : {stats['pauses']}",
        f"- Réactions gardées telles quelles : {stats['reactions']}",
        f"- Trous bruités gardés : {stats['bruits']}", "",
        "## Faux départs", "",
    ]
    lignes += [f"- {fmt(cible_vers_sortie(edit, r[1] + offset) or 0)} (source {fmt(r[1])}) : {r[3]}" for r in fs]
    lignes += ["", "## À écouter", ""]
    for x, msg in flags:
        o = cible_vers_sortie(edit, x + offset, premier=False)
        lignes.append(f"- {fmt(o) if o is not None else '?'} : {msg}")
    lignes += ["", "## Début de chaque bloc", ""]
    T, last = 0.0, None
    for k in keep:
        if k["why"] != last:
            lignes.append(f"- {fmt(T)} {k['why']}")
            last = k["why"]
        T += k["end"] - k["start"]
    txt = "\n".join(lignes) + "\n"
    if args.rapport:
        Path(args.rapport).write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
