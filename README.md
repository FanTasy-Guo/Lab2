
# Work2
本项目完成计算机图形学实验二
# CG-Lab2 · MVP 变换实验

## 项目框架

```
CG-Lab2/
├── src/
│   └── Work2/
│       ├── config.py       # 参数配置中心
│       ├── physics.py      # GPU 核心逻辑（MVP 矩阵推导）
│       ├── main.py         # 程序入口与视图层
│       ├── test.py         # 单元测试
│       └── __init__.py
└── README.md
```

`config.py` 集中管理所有超参数（窗口尺寸、相机位置、视场角、近远截面等），修改参数只需改这一个文件。`physics.py` 包含全部矩阵推导逻辑，以 `@ti.func` 装饰，运行在 Taichi 编译器管辖的 GPU/CPU 并行环境中。`main.py` 负责初始化 Taichi、驱动每帧渲染循环、响应键盘输入。

---

## 理论基础

三维场景渲染的核心问题是：如何把空间中的一个点映射到二维屏幕上。这个过程由三个依次作用的变换矩阵完成，合称 MVP 变换：
vclip=Mproj⋅Mview⋅Mmodel⋅vlocal\mathbf{v}_{clip} = M_{proj} \cdot M_{view} \cdot M_{model} \cdot \mathbf{v}_{local}vclip​=Mproj​⋅Mview​⋅Mmodel​⋅vlocal​
齐次坐标：为了把平移、旋转、缩放统一成矩阵乘法，三维坐标 (x,y,z)(x, y, z)
(x,y,z) 被扩展为四维齐次坐标 (x,y,z,1)(x, y, z, 1)
(x,y,z,1)，变换矩阵相应地扩展为 4×44 \times 4
4×4。

Model 变换：将物体从局部空间变换到世界空间。本实验实现绕 Z 轴旋转，旋转矩阵由二维旋转公式推广而来：
Mmodel=[cos⁡θ−sin⁡θ00sin⁡θcos⁡θ0000100001]M_{model} = \begin{bmatrix}\cos\theta & -\sin\theta & 0 & 0\\ \sin\theta & \cos\theta & 0 & 0\\ 0 & 0 & 1 & 0\\ 0 & 0 & 0 & 1\end{bmatrix}Mmodel​=​cosθsinθ00​−sinθcosθ00​0010​0001​​
View 变换：将世界坐标系变换到以相机为原点的观察空间。等价于把整个世界反向平移 −eye_pos-\mathbf{eye\_pos}
−eye_pos：

Mview=[100−ex010−ey001−ez0001]M_{view} = \begin{bmatrix}1&0&0&-e_x\\0&1&0&-e_y\\0&0&1&-e_z\\0&0&0&1\end{bmatrix}Mview​=​1000​0100​0010​−ex​−ey​−ez​1​​
Projection 变换：将三维观察空间投影到二维裁剪空间，分两步完成。
第一步，透视挤压矩阵 Mpersp→orthoM_{persp \to ortho}
Mpersp→ortho​，将视锥棱台压缩为长方体。近平面不变，远平面的 XY 坐标被压缩到与近平面相同大小。第三行系数 A,BA, B
A,B 由两个约束联立推导：近平面点 z=nz=n
z=n 变换后不变，远平面点 z=fz=f
z=f 变换后不变，解方程组得 A=n+fA = n+f
A=n+f，B=−nfB = -nf
B=−nf：

Mpersp→ortho=[n0000n0000n+f−nf0010]M_{persp \to ortho} = \begin{bmatrix}n&0&0&0\\0&n&0&0\\0&0&n+f&-nf\\0&0&1&0\end{bmatrix}Mpersp→ortho​=​n000​0n00​00n+f1​00−nf0​​
第二步，正交投影矩阵 MorthoM_{ortho}
Mortho​，将长方体 [l,r]×[b,t]×[f,n][l,r]\times[b,t]\times[f,n]
[l,r]×[b,t]×[f,n] 线性映射到标准设备坐标系 [−1,1]3[-1,1]^3
[−1,1]3，先平移中心到原点，再缩放边长到 2：

Mortho=[2r−l00−r+lr−l02t−b0−t+bt−b002n−f−n+fn−f0001]M_{ortho} = \begin{bmatrix}\frac{2}{r-l}&0&0&-\frac{r+l}{r-l}\\0&\frac{2}{t-b}&0&-\frac{t+b}{t-b}\\0&0&\frac{2}{n-f}&-\frac{n+f}{n-f}\\0&0&0&1\end{bmatrix}Mortho​=​r−l2​000​0t−b2​00​00n−f2​0​−r−lr+l​−t−bt+b​−n−fn+f​1​​
视锥体边界由视场角和近截面距离推导：t=tan⁡(fov/2)⋅∣n∣t = \tan(fov/2) \cdot |n|
t=tan(fov/2)⋅∣n∣，b=−tb=-t
b=−t，r=aspect⋅tr=\text{aspect} \cdot t
r=aspect⋅t，l=−rl=-r
l=−r。注意相机朝向 −Z-Z
−Z，因此 n=−znearn=-z_{near}
n=−znear​，f=−zfarf=-z_{far}
f=−zfar​。

最后经过透视除法，将齐次坐标 (x,y,z,w)(x, y, z, w)
(x,y,z,w) 除以 ww
w，得到 NDC 坐标，再线性映射到屏幕坐标 [0,1][0,1]
[0,1]。
---

## 代码逻辑

```
main() 每帧执行：
│
├── 键盘事件检测
│   ├── gui.is_pressed("a")  →  angle += ROTATE_STEP
│   ├── gui.is_pressed("d")  →  angle -= ROTATE_STEP
│   └── ESC                  →  退出
│
├── compute_mvp(angle, eye)          @ti.kernel
│   ├── get_model_matrix(angle)      →  绕 Z 轴旋转矩阵
│   ├── get_view_matrix(eye_pos)     →  相机平移到原点
│   ├── get_projection_matrix(...)   →  透视投影矩阵
│   ├── mvp = M_proj @ M_view @ M_model
│   └── transform_vertex × 3        →  写入 screen_verts field
│       ├── clip = mvp @ v
│       ├── 透视除法 ÷ w  →  NDC
│       └── NDC  →  屏幕坐标 [0, 1]
│
└── gui.line × 3 条边               →  绘制线框三角形
```

矩阵乘法顺序严格遵循右乘规则（列向量），变换从右向左依次执行：先 Model，再 View，最后 Projection。顶点数据直接在 `@ti.kernel` 内定义，避免 `ti.static` 访问 Python list 的兼容性问题。

---

## 实现功能

程序启动后弹出 700×700 的窗口，显示一个彩色线框三角形，三条边分别为红、绿、蓝三色。三角形初始顶点为 `(2,0,-2)`、`(0,2,-2)`、`(-2,0,-2)`，相机位于 `(0,0,5)` 朝向 -Z 方向。

| 按键 | 功能 |
|------|------|
| `A` | 绕 Z 轴逆时针旋转（每帧 2°） |
| `D` | 绕 Z 轴顺时针旋转（每帧 2°） |
| `ESC` | 退出程序 |

---

## 效果演示
<div align="center">
  <img src="gif/v1.gif" width="400">
  <img src="gif/v2.gif" width="400">
</div>
