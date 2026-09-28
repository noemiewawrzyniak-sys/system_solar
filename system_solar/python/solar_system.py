from __future__ import annotations

import time

import wgpu
from rendercanvas.glfw import RenderCanvas, loop

import graphics_math as gm
from camera2d import Camera2D 
from disk import Disk
from engine import Engine
from material import Material
from node import Node
from pipeline import Pipeline
from renderer import Renderer
from sampler import Sampler
from scene import Scene
from shader import Shader
from square import Square
from transform import Transform
from texture import Texture
from textureset import TextureSet

SHADER_PATH = "../shaders/2d/texture.wgsl"
ASSETS_DIR = "../images"

class OrbitEngine (Engine):
  def __init__ (self, trf: Transform, deg_per_sec: float) -> None:
    self.trf = trf
    self.deg_per_sec = deg_per_sec

  def update (self, dt: float) -> None:
    self.trf.rotate(self.deg_per_sec * dt, 0, 0, 1)

def make_texture_set (device: wgpu.GPUDevice, sampler: Sampler, filename: str) -> TextureSet:
  tex = Texture(device, "tex", f"{ASSETS_DIR}/{filename}")
  return TextureSet([tex, sampler])

def main () -> None:
  canvas = RenderCanvas(size=(700, 700), title="Mini Sistema Solar", update_mode="continuous")
  context = canvas.get_context("wgpu")
  adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance", canvas=context)
  device = adapter.request_device_sync()
  texture_format = context.get_preferred_format(adapter)
  context.configure(device=device, format=texture_format, alpha_mode="opaque")

  shader = Shader(device, SHADER_PATH)
  shader.set_vertex_buffers([
    {"array_stride": 2 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x2", "offset": 0, "shader_location": 0}]},
    {"array_stride": 2 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x2", "offset": 0, "shader_location": 1}]},
  ])
  pipeline = Pipeline(shader, texture_format, depth_stencil=None)

  disk = Disk(device, n=64)
  square = Square(device)

  neutral_material = Material(color=gm.vec3(1.0, 1.0, 1.0), opacity=1.0)
  shader.add_material(neutral_material)

  sampler = Sampler(device, "smp")
  sun_ts = make_texture_set(device, sampler, "sun.png")
  mercury_ts = make_texture_set(device, sampler, "mercury.png")
  earth_ts = make_texture_set(device, sampler, "earth.png")
  moon_ts = make_texture_set(device, sampler, "moon.png")
  background_ts = make_texture_set(device, sampler, "background.png")
  for ts in (sun_ts, mercury_ts, earth_ts, moon_ts, background_ts):
    shader.add_texture_set(ts)

  SUN_RADIUS, EARTH_RADIUS, MOON_RADIUS, MERCURY_RADIUS = 1.2, 0.4, 0.15, 0.22
  EARTH_ORBIT_RADIUS, MOON_ORBIT_RADIUS, MERCURY_ORBIT_RADIUS = 4.5, 1.0, 2.3
  EARTH_DEG_PER_SEC, MOON_DEG_PER_SEC, MERCURY_DEG_PER_SEC = 25.0, 140.0, 55.0
  EARTH_SPIN_DEG_PER_SEC = 200.0

  view_extent = EARTH_ORBIT_RADIUS + MOON_ORBIT_RADIUS + EARTH_RADIUS + 1.0
  bg_trf = Transform()
  bg_trf.scale(view_extent, view_extent, 1.0)
  background_node = Node(trf=bg_trf, apps=[neutral_material, background_ts], shps=[square])

  sun_trf = Transform()
  sun_trf.scale(SUN_RADIUS, SUN_RADIUS, 1.0)
  sun_node = Node(trf=sun_trf, apps=[neutral_material, sun_ts], shps=[disk])

  mercury_pivot_trf = Transform()
  mercury_offset_trf = Transform()
  mercury_offset_trf.translate(MERCURY_ORBIT_RADIUS, 0.0, 0.0)
  mercury_scale_trf = Transform()
  mercury_scale_trf.scale(MERCURY_RADIUS, MERCURY_RADIUS, 1.0)
  mercury_node = Node(trf=mercury_scale_trf, apps=[neutral_material, mercury_ts], shps=[disk])
  mercury_offset_node = Node(trf=mercury_offset_trf, nodes=[mercury_node])
  mercury_pivot_node = Node(trf=mercury_pivot_trf, nodes=[mercury_offset_node])

  moon_pivot_trf = Transform()
  moon_offset_trf = Transform()
  moon_offset_trf.translate(MOON_ORBIT_RADIUS, 0.0, 0.0)
  moon_scale_trf = Transform()
  moon_scale_trf.scale(MOON_RADIUS, MOON_RADIUS, 1.0)
  moon_node = Node(trf=moon_scale_trf, apps=[neutral_material, moon_ts], shps=[disk])
  moon_offset_node = Node(trf=moon_offset_trf, nodes=[moon_node])
  moon_pivot_node = Node(trf=moon_pivot_trf, nodes=[moon_offset_node])

  earth_pivot_trf = Transform()
  earth_offset_trf = Transform()
  earth_offset_trf.translate(EARTH_ORBIT_RADIUS, 0.0, 0.0)
  earth_spin_trf = Transform()
  earth_scale_trf = Transform()
  earth_scale_trf.scale(EARTH_RADIUS, EARTH_RADIUS, 1.0)
  earth_node = Node(trf=earth_scale_trf, apps=[neutral_material, earth_ts], shps=[disk])
  earth_spin_node = Node(trf=earth_spin_trf, nodes=[earth_node])
  earth_offset_node = Node(trf=earth_offset_trf, nodes=[earth_spin_node, moon_pivot_node])
  earth_pivot_node = Node(trf=earth_pivot_trf, nodes=[earth_offset_node])

  root = Node(pipeline=pipeline, nodes=[background_node, sun_node, mercury_pivot_node, earth_pivot_node])
  scene = Scene(root)
  scene.add_engine(OrbitEngine(earth_pivot_trf, EARTH_DEG_PER_SEC))
  scene.add_engine(OrbitEngine(earth_spin_trf, EARTH_SPIN_DEG_PER_SEC))
  scene.add_engine(OrbitEngine(moon_pivot_trf, MOON_DEG_PER_SEC))
  scene.add_engine(OrbitEngine(mercury_pivot_trf, MERCURY_DEG_PER_SEC))

  camera = Camera2D(-view_extent, view_extent, -view_extent, view_extent)
  renderer = Renderer(device, depth_test=False, clear_value=(0.0, 0.0, 0.0, 1.0))

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