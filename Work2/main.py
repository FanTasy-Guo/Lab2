import taichi as ti
import taichi.math as tm
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import config as cfg
from physics import (get_model_matrix, get_view_matrix,
                     get_projection_matrix, transform_vertex)

ti.init(arch=ti.cpu)

screen_verts = ti.Vector.field(2, dtype=ti.f32, shape=3)

@ti.kernel
def compute_mvp(angle: float, ex: float, ey: float, ez: float):
    eye_pos = tm.vec3(ex, ey, ez)
    M_model = get_model_matrix(angle)
    M_view  = get_view_matrix(eye_pos)
    M_proj  = get_projection_matrix(cfg.EYE_FOV, cfg.ASPECT_RATIO,
                                    cfg.Z_NEAR, cfg.Z_FAR)
    mvp = M_proj @ M_view @ M_model

    v0 = tm.vec4( 2.0, 0.0, -2.0, 1.0)
    v1 = tm.vec4( 0.0, 2.0, -2.0, 1.0)
    v2 = tm.vec4(-2.0, 0.0, -2.0, 1.0)

    screen_verts[0] = transform_vertex(v0, mvp)
    screen_verts[1] = transform_vertex(v1, mvp)
    screen_verts[2] = transform_vertex(v2, mvp)

def main():
    gui = ti.GUI(cfg.WIN_TITLE,
                 res=(cfg.WIN_WIDTH, cfg.WIN_HEIGHT),
                 background_color=0x1a1a2e)
    angle = 0.0
    eye   = cfg.EYE_POS

    while gui.running:
        for e in gui.get_events(ti.GUI.PRESS):
            if e.key == ti.GUI.ESCAPE:
                gui.running = False
            elif e.key == "a":
                angle += cfg.ROTATE_STEP
            elif e.key == "d":
                angle -= cfg.ROTATE_STEP

        compute_mvp(angle, eye[0], eye[1], eye[2])

        for idx, (i, j) in enumerate(cfg.EDGES):
            p0 = screen_verts[i].to_numpy()
            p1 = screen_verts[j].to_numpy()
            c  = cfg.EDGE_COLORS[idx]
            hex_color = (int(c[0]*255) << 16) | (int(c[1]*255) << 8) | int(c[2]*255)
            gui.line(begin=p0, end=p1, radius=1.5, color=hex_color)

        gui.text("A/D: rotate  |  ESC: quit",
                 pos=(0.01, 0.98), font_size=16, color=0xaaaaaa)
        gui.show()

if __name__ == "__main__":
    main()
