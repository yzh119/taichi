import sys

import taichi_lang as ti
import math
import numpy as np
import cv2
import os
import matplotlib.pyplot as plt
import time
from matplotlib.pyplot import cm
import taichi as tc

real = ti.f32
ti.set_default_fp(real)

max_steps = 4096
vis_interval = 1
output_vis_interval = 1
steps = 200
assert steps * 2 <= max_steps

vis_resolution = 1024

scalar = lambda: ti.var(dt=real)
vec = lambda: ti.Vector(2, dt=real)

loss = scalar()

x = vec()
v = vec()

goal = [0.9, 0.15]

n_objects = 1
ground_height = 0.1

@ti.layout
def place():
  ti.root.dense(ti.l, max_steps).dense(ti.i, n_objects).place(x, v)
  ti.root.place(loss)
  ti.root.lazy_grad()

dt = 0.35 / steps
learning_rate = 1.0

use_toi = False

@ti.kernel
def advance_toi(t: ti.i32):
  for i in range(n_objects):
    old_v = v[t - 1, i]
    new_v = old_v
    old_x = x[t - 1, i]
    new_x = old_x + dt * new_v
    toi = 0.0
    if new_x[1] < ground_height and new_v[1] < 0:
      new_v[1] = -new_v[1]
      toi = -(old_x[1] - ground_height) / old_v[1]
    v[t, i] = new_v
    x[t, i] = x[t - 1, i] + toi * old_v + (dt - toi) * new_v
    
@ti.kernel
def advance_no_toi(t: ti.i32):
  for i in range(n_objects):
    new_v = v[t - 1, i]
    if x[t - 1, i][1] < ground_height and new_v[1] < 0:
      new_v[1] = -new_v[1]
    v[t, i] = new_v
    x[t, i] = x[t - 1, i] + dt * new_v

gui = tc.core.GUI("Rigid Body", tc.Vectori(1024, 1024))
canvas = gui.get_canvas()

def forward(output=None, visualize=True):
  x[0, 0] = [0.8, 0.4]
  v[0, 0] = [-2, -2]
  
  interval = vis_interval
  total_steps = steps
  if output:
    interval = output_vis_interval
    os.makedirs('rigid_body/{}/'.format(output), exist_ok=True)
    total_steps *= 2

  canvas.clear(0xFFFFFF)
  for t in range(1, total_steps):
    if use_toi:
      advance_toi(t)
    else:
      advance_no_toi(t)
    
    if (t + 1) % interval == 0 and visualize:
      canvas.circle(tc.Vector(x[t, 0][0], x[t, 0][1])).radius(20).color(0x0).finish()
      offset = 0.003
      canvas.path(tc.Vector(0.05, ground_height - offset), tc.Vector(0.95, ground_height - offset)).radius(2).color(0x000000).finish()

  if output:
    gui.screenshot('rigid_body/{}/{:04d}.png'.format(output, t))
  gui.update()


def main():
 forward(visualize=True)
 
if __name__ == '__main__':
  main()
