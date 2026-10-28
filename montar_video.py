# -*- coding: utf-8 -*-
"""
Monta um vídeo do canal 72 Segundos: narração + footage real + legenda por bloco.

Cada frase da narração vira um plano. O corte segue a fala, não o contrário.

Uso:
    python montar_video.py --roteiro roteiros/001-sinal-wow.txt \
                           --voz voz/001.mp3 \
                           --clipes footage/antena_18308552.mp4 footage/papel_9655666.mp4 ... \
                           --out out/001-sinal-wow.mp4
"""
import argparse, os, subprocess, sys, tempfile, shutil

BASE   = os.path.dirname(os.path.abspath(__file__))
FONTE  = r"C:\Windows\Fonts\bahnschrift.ttf"
LARG, ALT, FPS = 1080, 1920, 30
FIM_FRASE = (".", "?", "!", ":")


def esc(p):
    return p.replace("\\", "/").replace(":", "\\:")


def dur(caminho):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", caminho],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def transcrever(voz):
    from faster_whisper import WhisperModel
    print("  transcrevendo (pt)...")
    m = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(voz, language="pt", word_timestamps=True)
    frases, palavras = [], []
    for s in segs:
        frases.append({"i": s.start, "f": s.end})
        for w in s.words:
            palavras.append({"t": w.word.strip(), "i": w.start, "f": w.end})
    return frases, palavras


def blocos(roteiro, palavras, max_p=4):
    """
    Legenda sai do ROTEIRO, nunca da transcrição — o Whisper erra nome próprio
    e sigla (ele ouviu "qual?" no lugar de "Wow"). Do Whisper vem só o tempo:
    a k-ésima palavra do roteiro herda o tempo da palavra equivalente no áudio.
    """
    texto = " ".join(open(roteiro, encoding="utf-8").read().split())
    palavras_r = texto.split(" ")
    W, M = len(palavras_r), len(palavras)
    if M == 0:
        sys.exit("ERRO: transcrição vazia")

    def tempo(k):
        j = min(M - 1, max(0, round(k * (M - 1) / max(1, W - 1))))
        return palavras[j]

    saida, atual = [], []
    for k, p in enumerate(palavras_r):
        atual.append((k, p))
        if len(atual) >= max_p or p.endswith(FIM_FRASE) or p.endswith(":"):
            saida.append(atual); atual = []
    if atual:
        saida.append(atual)

    b = [{"texto": " ".join(x[1] for x in g),
          "i": tempo(g[0][0])["i"],
          "f": tempo(g[-1][0])["f"]} for g in saida]
    if len(b) > 1 and (b[-1]["f"] - b[-1]["i"]) < 0.3:
        b[-2]["texto"] += " " + b[-1]["texto"]; b[-2]["f"] = b[-1]["f"]; b.pop()
    # whisper às vezes cruza os tempos: trava o fim antes do início do próximo
    for a, c in zip(b, b[1:]):
        if a["f"] >= c["i"]:
            a["f"] = max(a["i"] + 0.05, c["i"] - 0.02)
    return b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roteiro", required=True)
    ap.add_argument("--voz", required=True)
    ap.add_argument("--clipes", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--marca", default="72 SEGUNDOS")
    ap.add_argument("--legenda-y", type=float, default=0.755)
    ap.add_argument("--fonte-tam", type=int, default=58)
    a = ap.parse_args()

    total = dur(a.voz) + 0.6
    frases, palavras = transcrever(a.voz)
    caps = blocos(a.roteiro, palavras)
    print(f"  {len(frases)} planos · {len(caps)} blocos de legenda · {total:.1f}s")

    # um plano por frase; se faltar clipe, cicla sem repetir em seguida
    planos = []
    for i, fr in enumerate(frases):
        fim = frases[i + 1]["i"] if i + 1 < len(frases) else total
        planos.append({"clipe": a.clipes[i % len(a.clipes)],
                       "d": max(0.8, fim - fr["i"])})

    tmp = tempfile.mkdtemp(prefix="s72_")
    try:
        entradas, filtro, rotulos = [], "", []
        for i, p in enumerate(planos):
            entradas += ["-i", p["clipe"]]
            fonte_d = dur(p["clipe"])
            # começa em 0.5s (evita fade-in do stock) e corta no tamanho da frase;
            # se o clipe for curto, segura o último frame em vez de acelerar
            ini = 0.5 if fonte_d > p["d"] + 1 else 0
            filtro += (
                f"[{i}:v]trim=start={ini:.2f}:duration={p['d']:.2f},setpts=PTS-STARTPTS,"
                f"fps={FPS},scale={LARG}:{ALT}:force_original_aspect_ratio=increase,"
                f"crop={LARG}:{ALT},setsar=1,"
                # tpad só cobre clipe curto demais; o trim seguinte devolve a
                # duração exata, senão cada plano ganhava 2s e os cortes
                # desalinhavam da narração acumulando erro
                f"tpad=stop_mode=clone:stop_duration=2,"
                f"trim=duration={p['d']:.2f},setpts=PTS-STARTPTS[p{i}];"
            )
            rotulos.append(f"[p{i}]")

        filtro += "".join(rotulos) + f"concat=n={len(planos)}:v=1:a=0[corte];"

        # véu escuro na base, pra legenda ler sobre qualquer imagem
        idx_veu = len(planos)
        entradas += ["-f", "lavfi", "-i", f"color=black:s={LARG}x760:d={total:.2f}"]
        filtro += (
            f"[{idx_veu}:v]format=rgba,"
            f"geq=r=0:g=0:b=0:a='210*pow(Y/H,1.7)'[veu];"
            f"[corte][veu]overlay=0:{ALT-760}[base];"
        )

        atual = "base"
        for i, c in enumerate(caps):
            arq = os.path.join(tmp, f"c{i}.txt")
            open(arq, "w", encoding="utf-8").write(c["texto"])
            prox = f"t{i}"
            filtro += (
                f"[{atual}]drawtext=fontfile='{esc(FONTE)}':textfile='{esc(arq)}':"
                f"fontcolor=white:fontsize={a.fonte_tam}:"
                f"borderw=3:bordercolor=black@0.75:"
                f"shadowcolor=black@0.5:shadowx=2:shadowy=3:"
                f"x=(w-text_w)/2:y=h*{a.legenda_y}:"
                f"enable='between(t,{c['i']:.3f},{c['f']:.3f})'[{prox}];"
            )
            atual = prox

        # assinatura discreta do canal
        arq_marca = os.path.join(tmp, "marca.txt")
        open(arq_marca, "w", encoding="utf-8").write(a.marca)
        filtro += (
            f"[{atual}]drawtext=fontfile='{esc(FONTE)}':textfile='{esc(arq_marca)}':"
            f"fontcolor=white@0.55:fontsize=30:borderw=2:bordercolor=black@0.5:"
            f"x=w-text_w-46:y=76[vout]"
        )

        idx_voz = idx_veu + 1
        entradas += ["-i", a.voz]

        cmd = ["ffmpeg", "-y"] + entradas + [
            "-filter_complex", filtro,
            "-map", "[vout]", "-map", f"{idx_voz}:a",
            "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            a.out]

        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        print("  renderizando...")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-3500:]); sys.exit("ERRO no ffmpeg")
        print(f"OK -> {a.out}  ({os.path.getsize(a.out)/1024/1024:.1f} MB)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
