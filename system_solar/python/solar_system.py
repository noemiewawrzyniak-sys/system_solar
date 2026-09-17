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
from scene import Scene
from shader import Shader
from transform import Transform

class OrbitEngine (Engine):
  def __init__ (self, trf: Transform, deg_per_sec: float) -> None:
    self.trf = trf
    self.deg_per_sec = deg_per_sec

  def update (self, dt: float) -> None:
    self.trf.rotate(self.deg_per_sec * dt, 0, 0, 1)


def main () -> None:
  canvas = RenderCanvas(size=(700, 700), title="Mini Sistema Solar", update_mode="continuous")
  context = canvas.get_context("wgpu")
  adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance", canvas=context)
  device = adapter.request_device_sync()
  texture_format = context.get_preferred_format(adapter)
  context.configure(device=device, format=texture_format, alpha_mode="opaque")

  shader = Shader(device, "../shaders/2d/shader.wgsl")
  shader.set_vertex_buffers([
    {"array_stride": 2 * 4, "step_mode": "vertex",
     "attributes": [{"format": "float32x2", "offset": 0, "shader_location": 0}]},
  ])
  pipeline = Pipeline(shader, texture_format, depth_stencil=None)

  disk = Disk(device, n=64)

  sun_material = Material(color=gm.vec3(1.0, 0.85, 0.2), opacity=1.0)
  earth_material = Material(color=gm.vec3(0.25, 0.45, 1.0), opacity=1.0)
  moon_material = Material(color=gm.vec3(0.75, 0.75, 0.75), opacity=1.0)
  shader.add_material(sun_material)
  shader.add_material(earth_material)
  shader.add_material(moon_material)

  SUN_RADIUS, EARTH_RADIUS, MOON_RADIUS = 1.2, 0.4, 0.15
  EARTH_ORBIT_RADIUS, MOON_ORBIT_RADIUS = 4.5, 1.0
  EARTH_DEG_PER_SEC, MOON_DEG_PER_SEC = 25.0, 140.0

  sun_trf = Transform()
  sun_trf.scale(SUN_RADIUS, SUN_RADIUS, 1.0)
  sun_node = Node(trf=sun_trf, apps=[sun_material], shps=[disk])

  moon_pivot_trf = Transform()
  moon_offset_trf = Transform()
  moon_offset_trf.translate(MOON_ORBIT_RADIUS, 0.0, 0.0)
  moon_scale_trf = Transform()
  moon_scale_trf.scale(MOON_RADIUS, MOON_RADIUS, 1.0)

  moon_node = Node(trf=moon_scale_trf, apps=[moon_material], shps=[disk])
  moon_offset_node = Node(trf=moon_offset_trf, nodes=[moon_node])
  moon_pivot_node = Node(trf=moon_pivot_trf, nodes=[moon_offset_node])

  earth_pivot_trf = Transform()
  earth_offset_trf = Transform()
  earth_offset_trf.translate(EARTH_ORBIT_RADIUS, 0.0, 0.0)
  earth_scale_trf = Transform()
  earth_scale_trf.scale(EARTH_RADIUS, EARTH_RADIUS, 1.0)

  earth_node = Node(trf=earth_scale_trf, apps=[earth_material], shps=[disk])
  earth_offset_node = Node(trf=earth_offset_trf, nodes=[earth_node, moon_pivot_node])
  earth_pivot_node = Node(trf=earth_pivot_trf, nodes=[earth_offset_node])

  root = Node(pipeline=pipeline, nodes=[sun_node, earth_pivot_node])
  scene = Scene(root)
  scene.add_engine(OrbitEngine(earth_pivot_trf, EARTH_DEG_PER_SEC))
  scene.add_engine(OrbitEngine(moon_pivot_trf, MOON_DEG_PER_SEC))

  view_extent = EARTH_ORBIT_RADIUS + MOON_ORBIT_RADIUS + EARTH_RADIUS + 1.0
  camera = Camera2D(-view_extent, view_extent, -view_extent, view_extent)

  renderer = Renderer(device, depth_test=False, clear_value=(0.02, 0.02, 0.06, 1.0))

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