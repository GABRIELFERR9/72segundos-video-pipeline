# -*- coding: utf-8 -*-
"""Busca VIDEO (nao foto) no Pexels e salva frame pra conferencia visual."""
import os, subprocess, sys, requests

BASE = os.path.dirname(os.path.abspath(__file__))

def chave():
    for linha in open(r"C:\Users\CBRO\Desktop\stoic\.env", encoding="utf-8"):
        if linha.startswith("PEXELS_API_KEY="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("PEXELS_API_KEY nao encontrada")

def main():
    termo, qtd, tag, dest = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    os.makedirs(dest, exist_ok=True)
    frames = os.path.join(dest, "_frames")
    os.makedirs(frames, exist_ok=True)

    r = requests.get("https://api.pexels.com/videos/search",
                     headers={"Authorization": chave(), "User-Agent": "Mozilla/5.0"},
                     params={"query": termo, "per_page": qtd, "orientation": "portrait", "size": "medium"},
                     timeout=60)
    if r.status_code != 200:
        sys.exit(f"ERRO {r.status_code}: {r.text[:200]}")

    for v in r.json().get("videos", []):
        arqs = sorted(v["video_files"], key=lambda f: abs((f.get("height") or 0) - 1920))
        if not arqs: continue
        url = arqs[0]["link"]
        nome = f"{tag}_{v['id']}.mp4"
        caminho = os.path.join(dest, nome)
        if not os.path.exists(caminho):
            open(caminho, "wb").write(requests.get(url, timeout=180).content)
        subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", caminho, "-frames:v", "1",
                        "-vf", "scale=280:-1", os.path.join(frames, nome.replace(".mp4", ".jpg"))],
                       capture_output=True)
        print(f"{nome}  {arqs[0].get('width')}x{arqs[0].get('height')}  {v.get('duration')}s")

if __name__ == "__main__":
    main()
