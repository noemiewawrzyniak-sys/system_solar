from __future__ import annotations

import time

import wgpu
from rendercanvas.glfw import RenderCanvas, loop

import graphics_math as gm
from camera3d import Camera3D
from cube import Cube
from light import PointLight
from material import PhongMaterial
from node import Node
from pipeline import Pipeline
from renderer import Renderer
from scene import Scene
from shader import Shader
from sphere import Sphere
from transform import Transform

SHADER_PATH = "../shaders/ilum_frag/lit.wgsl"


def main () -> None:
  canvas = RenderCanvas(size=(900, 700), title="Cena 3D - mesa com esferas", update_mode="continuous")
  context = canvas.get_context("wgpu")
  adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance", canvas=context)
  device = adapter.request_device_sync()
  texture_format = context.get_preferred_format(adapter)
  context.configure(device=device, format=texture_format, alpha_mode="opaque")

  light = PointLight(3.0, 5.0, 4.0, space="world")

  shader = Shader(device, SHADER_PATH, light=light, space="world")
  shader.set_vertex_buffers([
    {"array_stride": 3 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x3", "offset": 0, "shader_location": 0}]},  # coord
    {"array_stride": 3 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x3", "offset": 0, "shader_location": 1}]},  # normal
  ])

  pipeline = Pipeline(shader, texture_format, primitive={"cull_mode": "back"})

  cube = Cube(device)
  sphere = Sphere(device, nstack=48, nslice=48)

  table_material = PhongMaterial(0.55, 0.35, 0.20)
  red_material = PhongMaterial(0.80, 0.10, 0.10)
  yellow_material = PhongMaterial(0.90, 0.80, 0.10)
  green_material = PhongMaterial(0.15, 0.65, 0.20)
  for mat in (table_material, red_material, yellow_material, green_material):
    shader.add_material(mat)

  TABLE_WIDTH, TABLE_HEIGHT, TABLE_DEPTH = 6.0, 1.0, 4.0
  table_trf = Transform()
  table_trf.scale(TABLE_WIDTH, TABLE_HEIGHT, TABLE_DEPTH)
  table_node = Node(trf=table_trf, apps=[table_material], shps=[cube])

  RED_RADIUS = 0.5
  red_trf = Transform()
  red_trf.translate(-1.4, TABLE_HEIGHT + RED_RADIUS, 0.0)
  red_trf.scale(RED_RADIUS, RED_RADIUS, RED_RADIUS)
  red_node = Node(trf=red_trf, apps=[red_material], shps=[sphere])

  BLOCK_W, BLOCK_H, BLOCK_D = 1.2, 1.0, 1.2
  yellow_trf = Transform()
  yellow_trf.translate(1.3, TABLE_HEIGHT, 0.0)
  yellow_trf.scale(BLOCK_W, BLOCK_H, BLOCK_D)
  yellow_node = Node(trf=yellow_trf, apps=[yellow_material], shps=[cube])

  GREEN_RADIUS = 0.35
  green_trf = Transform()
  green_trf.translate(1.3, TABLE_HEIGHT + BLOCK_H + GREEN_RADIUS, 0.0)
  green_trf.scale(GREEN_RADIUS, GREEN_RADIUS, GREEN_RADIUS)
  green_node = Node(trf=green_trf, apps=[green_material], shps=[sphere])

  root = Node(pipeline=pipeline, nodes=[table_node, red_node, yellow_node, green_node])
  scene = Scene(root)

  camera = Camera3D(5.0, 4.0, 7.0)
  camera.set_center(0.0, 1.2, 0.0)
  arcball = camera.create_arcball()
  arcball.attach(canvas)

  renderer = Renderer(device, depth_test=True, clear_value=(0.85, 0.87, 0.92, 1.0))

  last_t = time.perf_counter()

  def draw_frame () -> None:
    nonlocal last_t
    t = time.perf_counter()
    dt = t - last_t
    last_t = t

    scene.update(dt)
    target_texture = context.get_current_texture()
    renderer.render(target_texture, scene, camera)
    canvas.request_draw()

  canvas.request_draw(draw_frame)
  loop.run()


if __name__ == "__main__":
  main()