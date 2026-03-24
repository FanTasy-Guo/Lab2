import taichi as ti
import math

WIN_WIDTH  = 700
WIN_HEIGHT = 700
WIN_TITLE  = "MVP Transform - CG Lab"

EYE_POS      = (0.0, 0.0, 5.0)
EYE_FOV      = 45.0
ASPECT_RATIO = WIN_WIDTH / WIN_HEIGHT
Z_NEAR       = 0.1
Z_FAR        = 50.0

EDGES = [(0, 1), (1, 2), (2, 0)]

EDGE_COLORS = [
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
]

ROTATE_STEP = 2.0
