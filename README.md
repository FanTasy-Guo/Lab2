# CG-Lab2：MVP变换实验
姓名：郭亚楠

学号：202411081032

专业：计算机科学与技术（师范）

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

三维场景渲染的核心问题是：如何把空间中的一个点映射到二维屏幕上。这个过程由三个依次作用的变换矩阵完成，合称 **MVP 变换**：

$$\mathbf{v}_{clip} = M_{proj} \cdot M_{view} \cdot M_{model} \cdot \mathbf{v}_{local}$$

**齐次坐标**：为了把平移、旋转、缩放统一成矩阵乘法，三维坐标  $(x, y, z)$  被扩展为四维齐次坐标  $(x, y, z, 1)$ ，变换矩阵相应地扩展为  $4 \times 4$ 。

### Model 变换

将物体从局部空间变换到世界空间。本实验实现绕 Z 轴旋转。

### View 变换

将世界坐标系变换到以相机为原点的观察空间，等价于把整个世界反向平移  $-\mathbf{eye\_pos}$ 。

### Projection 变换

**第一步** 透视挤压矩阵，将棱台压缩为长方体。由约束 $An+B=n^2$ ， $Af+B=f^2$  解得 $A=n+f$ ， $B=-nf$ 。

**第二步** 正交投影矩阵，将长方体  $[l,r]\times[b,t]\times[f,n]$ 映射到  $[-1,1]^3$ 。

视锥体边界由视场角推导，其中 $n=-z_{near}$ ， $f=-z_{far}$  。

最终经**透视除法**  $(x,y,z,w)\div w$  得到 NDC 坐标，再映射到屏幕坐标 $[0,1]$ 。

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

矩阵乘法顺序严格遵循右乘规则（列向量），变换从右向左依次执行：先 Model，再 View，最后 Projection。

---

## 实现功能

程序启动后弹出700×700的窗口，显示一个彩色线框三角形，三条边分别为红、绿、蓝三色。三角形初始顶点为  $(2,0,-2)$ 、 $(0,2,-2)$ 、 $(-2,0,-2)$ ，相机位于 $(0,0,5)$  朝向 $-Z$ 方向。

| 按键 | 功能 |
|------|------|
| `A` | 绕 Z 轴逆时针旋转（每帧 2°） |
| `D` | 绕 Z 轴顺时针旋转（每帧 2°） |
| `ESC` | 退出程序 |

---

## 效果演示
<div align="center">
  <img src="gif/v1.gif" width="600">
</div>

<div align="center">
  <img src="gif/v2.gif" width="600">
</div>

