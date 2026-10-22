import os
import numpy as np
from PIL import Image

OUT = "../images"
os.makedirs(OUT, exist_ok=True)
N = 256

def save(name, arr):
  Image.fromarray(arr.astype("uint8")).save(os.path.join(OUT, name))

y, x = np.mgrid[0:N, 0:N]
tab = (y // 64)
veio = 0.5 + 0.5 * np.sin(x * 0.05 + tab * 2.0 + 6 * np.sin(y * 0.03))
base = np.array([150, 95, 55])
wood = base[None, None, :] * (0.75 + 0.25 * veio[..., None])
wood[(y % 64) < 2] = [60, 35, 20]
save("madeira.png", wood)

# tijolos
brick = np.zeros((N, N, 3)); brick[:] = [200, 195, 185]
for r in range(8):
  off = 32 if r % 2 else 0
  for c in range(-1, 5):
    x0 = c * 64 + off + 2; y0 = r * 32 + 2
    brick[max(y0,0):y0+28, max(x0,0):max(x0+60,0)] = [165, 60, 45]
save("tijolos.png", brick)

# listras diagonais
st = ((x + y) // 32) % 2
stripes = np.where(st[..., None] == 0, [240, 240, 240], [200, 40, 40])
save("listras.png", stripes)
print("texturas geradas em", OUT)
