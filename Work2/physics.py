import taichi as ti
import taichi.math as tm
from config import EYE_FOV, ASPECT_RATIO, Z_NEAR, Z_FAR

# ─────────────────────────────────────────────
# 1. Model 矩阵：绕 Z 轴旋转
#    推导：2D旋转矩阵扩展到4x4齐次坐标
#    R_Z = [[cos,-sin,0,0],[sin,cos,0,0],[0,0,1,0],[0,0,0,1]]
# ─────────────────────────────────────────────
@ti.func
def get_model_matrix(angle: float) -> ti.Matrix:
    rad = angle * (tm.pi / 180.0)          # 角度 → 弧度
    c   = tm.cos(rad)
    s   = tm.sin(rad)
    return ti.Matrix([
        [c,  -s,  0.0, 0.0],
        [s,   c,  0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])


# ─────────────────────────────────────────────
# 2. View 矩阵：把相机平移到原点
#    把世界坐标反向平移 -eye_pos
#    M_view = [[1,0,0,-ex],[0,1,0,-ey],[0,0,1,-ez],[0,0,0,1]]
# ─────────────────────────────────────────────
@ti.func
def get_view_matrix(eye_pos: tm.vec3) -> ti.Matrix:
    return ti.Matrix([
        [1.0, 0.0, 0.0, -eye_pos[0]],
        [0.0, 1.0, 0.0, -eye_pos[1]],
        [0.0, 0.0, 1.0, -eye_pos[2]],
        [0.0, 0.0, 0.0,  1.0       ],
    ])


# ─────────────────────────────────────────────
# 3. Projection 矩阵：透视投影
#    分两步：
#    Step1: M_persp2ortho —— 把棱台挤压成长方体
#           近平面不变，远平面 XY 压缩到近平面大小
#           第三行系数：A=n+f, B=-nf（由两个约束推导）
#    Step2: M_ortho       —— 正交投影，长方体→[-1,1]^3
#           对角线：2/(r-l), 2/(t-b), 2/(n-f)
#           平移列：-(r+l)/(r-l), -(t+b)/(t-b), -(n+f)/(n-f)
#    M_proj = M_ortho @ M_persp2ortho
# ─────────────────────────────────────────────
@ti.func
def get_projection_matrix(eye_fov:     float,
                           aspect:      float,
                           z_near:      float,
                           z_far:       float) -> ti.Matrix:
    # 注意：相机看向 -Z，所以实际坐标取负
    n = -z_near
    f = -z_far

    # 视锥体边界（由 fov 和近截面推导）
    half_fov = eye_fov * (tm.pi / 180.0) / 2.0
    t =  tm.tan(half_fov) * ti.abs(n)   # top
    b = -t                               # bottom
    r =  aspect * t                      # right
    l = -r                               # left

    # Step 1: 透视 → 正交 挤压矩阵
    # 由约束 An+B=n², Af+B=f² 解得 A=n+f, B=-nf
    A = n + f
    B = -n * f
    m_p2o = ti.Matrix([
        [n,   0.0, 0.0, 0.0],
        [0.0, n,   0.0, 0.0],
        [0.0, 0.0, A,   B  ],
        [0.0, 0.0, 1.0, 0.0],
    ])

    # Step 2: 正交投影矩阵
    # 把 [l,r]x[b,t]x[f,n] 线性映射到 [-1,1]^3
    # 先平移中心到原点，再缩放到边长2
    sx = 2.0 / (r - l)
    sy = 2.0 / (t - b)
    sz = 2.0 / (n - f)
    tx = -(r + l) / (r - l)
    ty = -(t + b) / (t - b)
    tz = -(n + f) / (n - f)
    m_ortho = ti.Matrix([
        [sx,  0.0, 0.0, tx ],
        [0.0, sy,  0.0, ty ],
        [0.0, 0.0, sz,  tz ],
        [0.0, 0.0, 0.0, 1.0],
    ])

    return m_ortho @ m_p2o


# ─────────────────────────────────────────────
# 4. 顶点变换：局部空间 → 屏幕空间
#    流程：MVP变换 → 透视除法(NDC) → 屏幕映射
# ─────────────────────────────────────────────
@ti.func
def transform_vertex(v: tm.vec4,
                     mvp: ti.template()) -> tm.vec2:
    # MVP 变换（列向量右乘）
    clip = mvp @ v

    # 透视除法：齐次坐标 → NDC [-1,1]
    ndc_x = clip[0] / clip[3]
    ndc_y = clip[1] / clip[3]

    # NDC → 屏幕坐标 [0,1]
    # NDC 的 (-1,-1) 对应屏幕左下，(1,1) 对应右上
    screen_x = (ndc_x + 1.0) * 0.5
    screen_y = (ndc_y + 1.0) * 0.5

    return tm.vec2(screen_x, screen_y)