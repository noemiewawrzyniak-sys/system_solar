"""Projeto final - Opcao 1: cena com mesa e objetos.

Requisitos: cubos e esferas instanciados num grafo de cena; iluminacao por
fragmento; luz de spot; mais de um objeto com textura de padronagem (decal);
arcball. Opcionais: fog, plano de corte, segunda fonte de luz.

Teclas:  F = liga/desliga fog   C = liga/desliga plano de corte
         L = liga/desliga a luz 2
"""

from __future__ import annotations

import time

import graphics_math as gm
import wgpu
from rendercanvas.glfw import RenderCanvas, loop

from camera3d import Camera3D
from cube import Cube
from light import SpotLight
from material import PhongMaterial
from node import Node
from pipeline import Pipeline
from renderer import Renderer
from sampler import Sampler
from scene import Scene
from shader import Shader
from sphere import Sphere
from texture import Texture
from textureset import TextureSet
from transform import Transform

SHADER_PATH = "../shaders/ilum_frag/final.wgsl"
IMAGES = "../images/"

BACKGROUND = (0.18, 0.19, 0.24)

# luz 1: spot (posicao no mundo, ponto alvo, abertura, expoente)
SPOT_POSITION = (3.0, 5.5, 2.5)
SPOT_TARGET = (0.0, 1.6, 0.0)
SPOT_ANGLE = 18.0
SPOT_EXPONENT = 20.0

# luz 2: pontual, de preenchimento (mundo)
LIGHT2_POSITION = gm.vec3(-3.5, 4.0, 3.0)
LIGHT2_COLOR = gm.vec3(0.30, 0.34, 0.55)

# fog (densidade) e plano de corte (a*x + b*y + c*z + d >= 0 permanece):
# aqui y <= 2.35, que corta a esfera verde ao meio
FOG_DENSITY = 0.05
CLIP_PLANE = gm.vec4(0.0, -1.0, 0.0, 2.35)
NO_CLIP = gm.vec4(0.0, 1.0, 0.0, 1000.0)


def main () -> None:
  canvas = RenderCanvas(size=(1000, 700), title="Projeto final - mesa e objetos", update_mode="continuous")
  context = canvas.get_context("wgpu")
  adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance", canvas=context)
  device = adapter.request_device_sync()
  texture_format = context.get_preferred_format(adapter)
  context.configure(device=device, format=texture_format, alpha_mode="opaque")

  direction = tuple(t - p for t, p in zip(SPOT_TARGET, SPOT_POSITION))
  light = SpotLight(*SPOT_POSITION, *direction, angle=SPOT_ANGLE, exponent=SPOT_EXPONENT, space="world")

  # espaco "world": luz 2, fog e plano de corte ficam fixos no mundo
  # enquanto o arcball gira a camera
  shader = Shader(device, SHADER_PATH, light=light, space="world")
  shader.set_vertex_buffers([
    {"array_stride": 12, "step_mode": "vertex", "attributes": [{"format": "float32x3", "offset": 0, "shader_location": 0}]},  # coord
    {"array_stride": 12, "step_mode": "vertex", "attributes": [{"format": "float32x3", "offset": 0, "shader_location": 1}]},  # normal
    {"array_stride": 12, "step_mode": "vertex", "attributes": [{"format": "float32x3", "offset": 0, "shader_location": 2}]},  # tangente (nao usada)
    {"array_stride": 8,  "step_mode": "vertex", "attributes": [{"format": "float32x2", "offset": 0, "shader_location": 3}]},  # texcoord
  ])
  pipeline = Pipeline(shader, texture_format, primitive={"cull_mode": "back"})

  shader.set_value("light2_position", LIGHT2_POSITION)
  shader.set_value("light2_color", LIGHT2_COLOR)
  shader.set_value("fog_color", gm.vec3(*BACKGROUND))
  shader.set_value("fog_density", FOG_DENSITY)
  shader.set_value("clip_plane", CLIP_PLANE)

  cube = Cube(device)
  sphere = Sphere(device, nstack=64, nslice=64)

  # texturas (decal); objeto sem imagem usa um texel branco 1x1
  sampler = Sampler(device, "decal_sampler")
  def decal (filename: str | None) -> TextureSet:
    if filename:
      tex = Texture(device, "decal_texture", IMAGES + filename)
    else:
      tex = Texture(device, "decal_texture", None, texel=gm.vec3(1.0, 1.0, 1.0))
    ts = TextureSet([tex, sampler])
    shader.add_texture_set(ts)
    return ts

  wood, bricks, stripes, plain = decal("madeira.png"), decal("tijolos.png"), decal("listras.png"), decal(None)

  white = PhongMaterial(1.0, 1.0, 1.0)      # cor do material = branco: o decal define a cor
  green = PhongMaterial(0.15, 0.65, 0.20)
  shader.add_material(white)
  shader.add_material(green)

  # --- cena (a mesma da Tarefa 2.1) ---
  TABLE_HEIGHT = 1.0
  table_trf = Transform()
  table_trf.scale(6.0, TABLE_HEIGHT, 4.0)
  table = Node(trf=table_trf, apps=[white, wood], shps=[cube])

  red_trf = Transform()
  red_trf.translate(-1.4, TABLE_HEIGHT + 0.5, 0.0)
  red_trf.scale(0.5, 0.5, 0.5)
  red = Node(trf=red_trf, apps=[white, stripes], shps=[sphere])

  block_trf = Transform()
  block_trf.translate(1.3, TABLE_HEIGHT, 0.0)
  block_trf.scale(1.2, 1.0, 1.2)
  block = Node(trf=block_trf, apps=[white, bricks], shps=[cube])

  ball_trf = Transform()
  ball_trf.translate(1.3, TABLE_HEIGHT + 1.0 + 0.35, 0.0)
  ball_trf.scale(0.35, 0.35, 0.35)
  ball = Node(trf=ball_trf, apps=[green, plain], shps=[sphere])

  root = Node(pipeline=pipeline, nodes=[table, red, block, ball])
  scene = Scene(root)

  camera = Camera3D(5.0, 4.0, 7.0)
  camera.set_center(0.0, 1.2, 0.0)
  arcball = camera.create_arcball()
  arcball.attach(canvas)

  renderer = Renderer(device, depth_test=True, clear_value=(*BACKGROUND, 1.0))

  # F / C / L: liga e desliga fog, plano de corte e luz 2
  state = {"fog": True, "clip": True, "light2": True}
  def on_key (event) -> None:
    key = str(event.get("key", "")).lower()
    if key == "f":
      state["fog"] = not state["fog"]
      shader.set_value("fog_density", FOG_DENSITY if state["fog"] else 0.0)
    elif key == "c":
      state["clip"] = not state["clip"]
      shader.set_value("clip_plane", CLIP_PLANE if state["clip"] else NO_CLIP)
    elif key == "l":
      state["light2"] = not state["light2"]
      shader.set_value("light2_color", LIGHT2_COLOR if state["light2"] else gm.vec3(0.0, 0.0, 0.0))
  canvas.add_event_handler(on_key, "key_down")

  last_t = time.perf_counter()

  def draw_frame () -> None:
    nonlocal last_t
    t = time.perf_counter()
    dt = t - last_t
    last_t = t
    scene.update(dt)
    renderer.render(context.get_current_texture(), scene, camera)
    canvas.request_draw()

  canvas.request_draw(draw_frame)
  loop.run()


if __name__ == "__main__":
  main()
