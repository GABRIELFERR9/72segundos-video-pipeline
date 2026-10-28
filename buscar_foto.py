# -*- coding: utf-8 -*-
"""
Busca FOTOS no Pexels e salva miniatura pra conferência visual.
Nunca aceitar por palavra-chave — sempre olhar o frame.

Uso: python buscar_foto.py "cat window" 6 janela
"""
import os, sys, requests

BASE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(BASE, "fotos")

def chave():
    for linha in open(r"C:\Users\CBRO\Desktop\stoic\.env", encoding="utf-8"):
        if linha.startswith("PEXELS_API_KEY="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("PEXELS_API_KEY nao encontrada")

def main():
    termo, qtd, tag = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    os.makedirs(DEST, exist_ok=True)
    r = requests.get("https://api.pexels.com/v1/search",
                     headers={"Authorization": chave(), "User-Agent": "Mozilla/5.0"},
                     params={"query": termo, "per_page": qtd, "orientation": "landscape"},
                     timeout=60)
    if r.status_code != 200:
        sys.exit(f"ERRO {r.status_code}: {r.text[:200]}")
    for f in r.json().get("photos", []):
        nome = f"{tag}_{f['id']}.jpg"
        img = requests.get(f["src"]["large"], timeout=90).content
        open(os.path.join(DEST, nome), "wb").write(img)
        print(f"{nome}  {f['width']}x{f['height']}  por {f['photographer']}")

if __name__ == "__main__":
    main()
