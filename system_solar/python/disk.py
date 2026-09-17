from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import wgpu
from shape import Shape

if TYPE_CHECKING:
  from state import State


class Disk (Shape):

  def __init__ (self, device: wgpu.GPUDevice, n: int = 64) -> None:

    coord = [(0.0, 0.0)] # centro do disco
    texcoord = [(0.5, 0.5)]
    for i in range(n + 1):
      th = 2 * math.pi * i / n
      x, y = math.cos(th), math.sin(th)
      coord.append((x, y))
      texcoord.append((0.5 + 0.5 * x, 0.5 - 0.5 * y))

    indices: list[int] = []
    for i in range(1, n + 1):
      indices.extend([0, i, i + 1])

    bcoord = np.array(coord, dtype='float32')
    btexcoord = np.array(texcoord, dtype='float32')
    bindex = np.array(indices, dtype='uint32')

    self.vbo: wgpu.GPUBuffer = device.create_buffer_with_data(data=bcoord, usage=wgpu.BufferUsage.VERTEX)
    self.tbo: wgpu.GPUBuffer = device.create_buffer_with_data(data=btexcoord, usage=wgpu.BufferUsage.VERTEX)
    self.ibo: wgpu.GPUBuffer = device.create_buffer_with_data(data=bindex, usage=wgpu.BufferUsage.INDEX)
    self.n_indices: int = len(indices)

  def draw (self, st: State) -> None:
    first_instance = st.get_shader().commit_matrix(st)
    st.render_pass.set_vertex_buffer(0, self.vbo)
    st.render_pass.set_vertex_buffer(1, self.tbo)
    st.render_pass.set_index_buffer(self.ibo, wgpu.IndexFormat.uint32)
    st.render_pass.draw_indexed(self.n_indices, 1, 0, 0, first_instance)