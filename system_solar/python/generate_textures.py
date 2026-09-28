"""Gera texturas provisorias com PIL, para testar o projeto antes de ter
imagens reais. Rode uma vez: `python generate_textures.py`. Troque depois
os arquivos em assets/ pelas suas imagens (mesmos nomes, mesmo tamanho
nao e obrigatorio - Texture le o tamanho de cada imagem)."""

import math
import random

from PIL import Image, ImageDraw

random.seed(42)
OUT = "assets"


def sun () -> None:
  """Gradiente radial amarelo -> laranja."""
  n = 256
  img = Image.new("RGB", (n, n))
  px = img.load()
  cx, cy = n / 2, n / 2
  for y in range(n):
    for x in range(n):
      d = min(1.0, math.hypot(x - cx, y - cy) / (n / 2))
      r = int(255)
      g = int(230 - 80 * d)
      b = int(60 - 60 * d)
      px[x, y] = (r, max(g, 0), max(b, 0))
  img.save(f"{OUT}/sun.png")


def mottled (filename: str, base: tuple[int, int, int], variation: int, n: int = 256) -> None:
  """Textura ruidosa simples (cinza/marrom) - serve para Mercurio/Venus e
  para a Lua (superficie sem padrao obvio de rotacao, propositalmente)."""
  img = Image.new("RGB", (n, n))
  px = img.load()
  for y in range(n):
    for x in range(n):
      d = random.randint(-variation, variation)
      px[x, y] = tuple(max(0, min(255, c + d)) for c in base)
  img.save(f"{OUT}/{filename}")


def earth () -> None:
  """Faixas verticais (longitude) para deixar a rotacao propria bem visivel,
  mais uma faixa vermelha de referencia (um 'meridiano' marcado)."""
  n = 256
  img = Image.new("RGB", (n, n))
  draw = ImageDraw.Draw(img)
  stripes = 12
  colors = [(30, 90, 180), (40, 140, 70)]  # oceano / continente, alternando
  for i in range(stripes):
    x0 = i * n // stripes
    x1 = (i + 1) * n // stripes
    draw.rectangle([x0, 0, x1, n], fill=colors[i % 2])
  draw.rectangle([0, 0, max(1, n // 40), n], fill=(220, 30, 30))  # marca de referencia
  img.save(f"{OUT}/earth.png")


def starfield () -> None:
  """Fundo do espaco: azul bem escuro com estrelas de brilho/tamanho aleatorios."""
  n = 1024
  img = Image.new("RGB", (n, n), (4, 4, 12))
  draw = ImageDraw.Draw(img)
  for _ in range(900):
    x, y = random.randint(0, n - 1), random.randint(0, n - 1)
    b = random.randint(120, 255)
    r = random.choice([0, 0, 0, 1])  # a maioria e um pixel, algumas maiores
    draw.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, b))
  img.save(f"{OUT}/background.png")


if __name__ == "__main__":
  import os
  os.makedirs(OUT, exist_ok=True)
  sun()
  earth()
  mottled("moon.png", base=(150, 150, 150), variation=35)
  mottled("mercury.png", base=(140, 110, 90), variation=30)   # troque por venus.png se preferir
  starfield()
  print("Texturas geradas em", OUT)
