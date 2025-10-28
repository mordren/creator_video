#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uso super simples:
    python gerar_plano.py caminho/do/video.srt

Fluxo:
  1. Lê videos.json (fixo)
  2. Gera plano inicial com SBERT + FAISS
  3. Diversifica (sem repetição)
  4. Salva plano_final.json + plano_final.csv
"""

import json, re, faiss, numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# ---------- Config ----------
VIDEOS_JSON = Path("assets/videos.json")  # fixo
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOPK = 3
COOLDOWN = 3
MAX_USAGE = 1

# ---------- Utils ----------
def time_to_ms(t: str) -> int:
    hh, mm, ss, ms = map(int, re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", t).groups())
    return ((hh*60+mm)*60+ss)*1000+ms

def parse_srt(path: Path):
    raw = path.read_text(encoding="utf-8", errors="ignore").strip()
    blocks = re.split(r"\n\s*\n", raw)
    segs = []
    for b in blocks:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        if len(lines) < 2: continue
        if re.fullmatch(r"\d+", lines[0]): lines = lines[1:]
        if "-->" not in lines[0]: continue
        t1, t2 = [t.strip() for t in lines[0].split("-->")]
        text = " ".join(lines[1:])
        segs.append({"start_ms": time_to_ms(t1), "end_ms": time_to_ms(t2), "caption": text})
    return segs

def load_catalog():
    data = json.loads(VIDEOS_JSON.read_text(encoding="utf-8"))
    items = data["videos"] if "videos" in data else data
    texts, meta = [], []
    for r in items:
        txt = (r.get("imagem","") + " " + " ".join(r.get("palavras",[]))).strip()
        texts.append(txt)
        meta.append({"arquivo": r["arquivo"], "imagem": r["imagem"]})
    return texts, meta

# ---------- Diversificador simples ----------
def diversify(plan, cooldown=COOLDOWN, max_usage=MAX_USAGE):
    used, recent = {}, []
    result = []
    for seg in plan:
        for m in seg["matches"]:
            arq = m["arquivo"]
            if used.get(arq,0) < max_usage and arq not in recent[-cooldown:]:
                result.append({**seg, **m})
                used[arq] = used.get(arq,0)+1
                recent.append(arq)
                break
        else:
            m = seg["matches"][0]
            result.append({**seg, **m})
    return result

# ---------- Pipeline ----------
def gerar_plano(srt_path: Path):
    print(f"🎬 Lendo: {srt_path}")
    segs = parse_srt(srt_path)
    texts, meta = load_catalog()
    print(f"🧠 Carregando modelo {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    X = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    index = faiss.IndexFlatIP(X.shape[1])
    index.add(X)

    q_emb = model.encode([s["caption"] for s in segs], convert_to_numpy=True, normalize_embeddings=True)
    scores, idxs = index.search(q_emb, TOPK)

    plano = []
    for i, seg in enumerate(segs):
        matches = []
        for j, score in zip(idxs[i], scores[i]):
            matches.append({
                "arquivo": meta[j]["arquivo"],
                "imagem": meta[j]["imagem"],
                "score": float(score)
            })
        plano.append({"segment_index": i+1, "caption": seg["caption"], "matches": matches})

    plano_final = diversify(plano)

    Path("plano_final.json").write_text(json.dumps(plano_final, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ plano_final.json gerado!")

    import csv
    with open("plano_final.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["segment_index","caption","arquivo","imagem","score"])
        for p in plano_final:
            w.writerow([p["segment_index"], p["caption"], p["arquivo"], p["imagem"], p["score"]])
    print("✅ plano_final.csv gerado!")

# ---------- Main ----------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("❗Uso: python gerar_plano.py caminho/do/video.srt")
        sys.exit(1)
    gerar_plano(Path(sys.argv[1]))
