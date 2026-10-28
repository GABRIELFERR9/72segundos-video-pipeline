# -*- coding: utf-8 -*-
"""
Busca clipes verticais no Pexels e salva um frame de cada pra conferência visual.
Nunca aceitar clipe sem olhar o frame — palavra-chave erra muito.

Uso: python buscar_footage.py "radio telescope" 4 tag
"""
import os, subprocess, sys, requests

BASE = os.path.dirname(os.path.abspath(__file__))
FOOTAGE = os.path.join(BASE, "footage")
FRAMES  = os.path.join(BASE, "footage", "_frames")

def chave():
    env = r"C:\Users\CBRO\Desktop\stoic\.env"
    for linha in open(env, encoding="utf-8"):
        if linha.startswith("PEXELS_API_KEY="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("PEXELS_API_KEY não encontrada")

def main():
    termo, qtd, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    os.makedirs(FOOTAGE, exist_ok=True)
    os.makedirs(FRAMES, exist_ok=True)

    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": chave(), "User-Agent": "Mozilla/5.0"},
        params={"query": termo, "per_page": qtd * 3,
                "orientation": "portrait", "size": "medium"},
        timeout=60)
    if r.status_code != 200:
        sys.exit(f"ERRO {r.status_code}: {r.text[:200]}")

    salvos = 0
    for v in r.json().get("videos", []):
        if salvos >= qtd:
            break
        # pega o arquivo com altura mais próxima de 1920
        arquivos = sorted(v["video_files"],
                          key=lambda f: abs((f.get("height") or 0) - 1920))
        if not arquivos:
            continue
        url = arquivos[0]["link"]
        nome = f"{tag}_{v['id']}.mp4"
        destino = os.path.join(FOOTAGE, nome)
        if not os.path.exists(destino):
            dados = requests.get(url, timeout=180).content
            open(destino, "wb").write(dados)
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "1.5", "-i", destino, "-frames:v", "1",
             "-vf", "scale=260:-1", os.path.join(FRAMES, nome.replace(".mp4", ".jpg"))],
            capture_output=True)
        dur = arquivos[0].get("fps") and v.get("duration")
        print(f"{nome}  {arquivos[0].get('width')}x{arquivos[0].get('height')}  {v.get('duration')}s")
        salvos += 1

if __name__ == "__main__":
    main()
