# 72segundos-video-pipeline

Pipeline em Python que monta vídeos curtos: narração, footage do Pexels e legenda por frase com FFmpeg.

Pipeline que monta vídeos curtos de curiosidade a partir de um roteiro em texto.

## Como funciona
1. Cada frase do roteiro vira um plano: o corte segue a fala.
2. Busca footage e fotos no Pexels (`buscar_*.py`).
3. `montar_video.py` junta narração, clipes e legenda por bloco com FFmpeg.
4. `montar_capa.py` gera a capa.

## Uso
```bash
python montar_video.py --roteiro roteiros/001-sinal-wow.txt --voz voz/001.mp3 --clipes footage/*.mp4 --out out/001.mp4
```
Requer Python 3 e FFmpeg, mais a chave do Pexels (`PEXELS_API_KEY` num arquivo .env).

---
Feito por [Gabriel Ferreira](https://github.com/GABRIELFERR9).
