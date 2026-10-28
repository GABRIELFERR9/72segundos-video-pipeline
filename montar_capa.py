# -*- coding: utf-8 -*-
"""
Capa do 72 Segundos: frame do vídeo + título + assinatura.
Identidade: branco sobre escuro, vermelho só no número (a caneta do Ehman).

Uso:
    python montar_capa.py --video out/001-sinal-wow.mp4 --t 57 \
        --out out/001-capa.jpg --linha "UM SINAL DO ESPAÇO" --linha "QUE DUROU 72 SEGUNDOS"
"""
import argparse, os, subprocess, sys, tempfile, shutil

FONTE = r"C:\Windows\Fonts\bahnschrift.ttf"
LARG, ALT = 1080, 1920


def esc(p):
    return p.replace("\\", "/").replace(":", "\\:")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--t", type=float, default=2)
    ap.add_argument("--out", required=True)
    ap.add_argument("--linha", action="append", required=True)
    ap.add_argument("--y", type=float, default=0.09)
    ap.add_argument("--tam", type=int, default=92)
    ap.add_argument("--marca", default="72 SEGUNDOS")
    a = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="capa72_")
    try:
        # escurece um pouco e puxa contraste, pro texto dominar
        f = (f"[0:v]scale={LARG}:{ALT}:force_original_aspect_ratio=increase,"
             f"crop={LARG}:{ALT},eq=brightness=-0.06:contrast=1.12,setsar=1[bg];")
        atual = "bg"

        for i, linha in enumerate(a.linha):
            arq = os.path.join(tmp, f"t{i}.txt")
            open(arq, "w", encoding="utf-8").write(linha.upper())
            y = int(a.y * ALT + i * (a.tam * 1.22))
            prox = f"t{i}"
            f += (f"[{atual}]drawtext=fontfile='{esc(FONTE)}':textfile='{esc(arq)}':"
                  f"fontcolor=white:fontsize={a.tam}:"
                  f"borderw=4:bordercolor=black@0.8:"
                  f"shadowcolor=black@0.6:shadowx=3:shadowy=4:"
                  f"x=(w-text_w)/2:y={y}[{prox}];")
            atual = prox

        # traço vermelho — a caneta que circulou o sinal
        y_traco = int(a.y * ALT + len(a.linha) * (a.tam * 1.22) + 26)
        f += (f"[{atual}]drawbox=x=(iw-190)/2:y={y_traco}:w=190:h=7:"
              f"color=#e63329@0.95:t=fill[traco];")

        arq_m = os.path.join(tmp, "m.txt")
        open(arq_m, "w", encoding="utf-8").write(a.marca)
        f += (f"[traco]drawtext=fontfile='{esc(FONTE)}':textfile='{esc(arq_m)}':"
              f"fontcolor=white@0.75:fontsize=40:borderw=3:bordercolor=black@0.6:"
              f"x=(w-text_w)/2:y=h*0.915[vout]")

        cmd = ["ffmpeg", "-y", "-ss", str(a.t), "-i", a.video,
               "-filter_complex", f, "-map", "[vout]",
               "-frames:v", "1", "-q:v", "2", a.out]

        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-2500:]); sys.exit("ERRO no ffmpeg")
        print(f"OK -> {a.out}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
