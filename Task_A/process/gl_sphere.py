import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer
from OpenGL.GL import *
from OpenGL.GLU import *
import cv2

from process.config import Config

class SphereWidget(QOpenGLWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)

        self.sphere_radius = Config.EYEBALL_RADIUS # 眼球半径
        self.circle_radius = Config.PUPIL_RADIUS # 眼球上瞳孔的半径
        self.sphere_offset = Config.CAMERA_OFFSET # 眼球到相机的距离
        self.fov_angle_y = Config.FOV_ANGLE_Y # 垂直视野角度

        self.sphere_rot_x = 0 # 视线向量绕X轴的旋转角度
        self.sphere_rot_y = 0 # 视线向量绕Y轴的旋转角度

        # 生成球体的顶点和索引
        self.sphere_vertices, self.sphere_indices = self.generate_wireframe_sphere(lat_div=30, lon_div=30)
        # 生成眼球上圆的顶点
        self.circle_vertices = self.generate_circle_on_sphere(num_segments=100)

    # 绘制2d的圆形
    def draw_2d_circle(self, x, y, radius, segments):
        w = self.width()
        h = self.height()

        # 设置投影矩阵
        glMatrixMode(GL_PROJECTION)
        # 将当前矩阵保存到栈中
        glPushMatrix()
        # 设置正交投影
        glLoadIdentity()
        glOrtho(0, w, 0, h, -1, 1)

        # 设置模型视图矩阵
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # 翻转y因为OpenGL的(0,0)是左下角, 但PyQt使用的是左上角
        y_flipped = h - y

        # 绘制圆形
        glColor3f(1.0, 1.0, 0.0)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            cx = x + np.cos(angle) * radius
            cy = y_flipped + np.sin(angle) * radius
            glVertex2f(cx, cy)
        glEnd()

        # 恢复两个矩阵
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    # 为球体生成顶点和索引
    def generate_wireframe_sphere(self, lat_div, lon_div):
        vertices = []
        indices = []
        for i in range(lat_div + 1):
            lat = np.pi * (-0.5 + float(i) / lat_div)
            z = self.sphere_radius * np.sin(lat)
            zr = self.sphere_radius * np.cos(lat)
            for j in range(lon_div + 1):
                lon = 2 * np.pi * float(j) / lon_div
                x = np.cos(lon) * zr
                y = np.sin(lon) * zr
                vertices.append((x, y, z))
        for i in range(lat_div):
            for j in range(lon_div):
                p1 = i * (lon_div + 1) + j
                p2 = p1 + lon_div + 1
                indices.append((p1, p2))
                indices.append((p1, p1 + 1))
        return np.array(vertices, dtype=np.float32), np.array(indices, dtype=np.int32)

    # 为球体上的圆生成顶点
    def generate_circle_on_sphere(self, num_segments):
        circle_vertices = []

        plane_z = np.sqrt(self.sphere_radius**2 - self.circle_radius**2)

        for i in range(num_segments):
            angle = 2.0 * np.pi * i / num_segments
            x = np.cos(angle) * self.circle_radius
            y = np.sin(angle) * self.circle_radius
            z = plane_z  # z is constant
            circle_vertices.append((x, y, z))

        return np.array(circle_vertices, dtype=np.float32)

    # OpenGL初始化
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

    # 窗口大小变化时调用
    def resizeGL(self, w, h):
        # 设置视口
        glViewport(0, 0, w, h)
        # 设置投影矩阵
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # 设置透视投影
        gluPerspective(self.fov_angle_y, w / h, 0.1, 100)
        # 切换回模型视图矩阵
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        # 清除颜色和深度缓存
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # 移动绘制原点
        glTranslatef(0, 0, -self.sphere_offset)

        # 将当前矩阵保存到栈中
        glPushMatrix()
        
        # 根据视线向量旋转坐标系
        glRotatef(self.sphere_rot_x, 1, 0, 0)
        glRotatef(self.sphere_rot_y, 0, 1, 0)

        # 绘制眼球
        glColor3f(0.8, 0.3, 0.3)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for i1, i2 in self.sphere_indices:
            glVertex3fv(self.sphere_vertices[i1])
            glVertex3fv(self.sphere_vertices[i2])
        glEnd()

        # 绘制视线向量
        glColor3f(0.0, 0.0, 1.0)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 1.2)
        glEnd()

        # 绘制瞳孔
        glColor3f(0.0, 1.0, 0.0)
        glLineWidth(3.0)
        glBegin(GL_LINE_LOOP)
        for vertex in self.circle_vertices:
            glVertex3fv(vertex)
        glEnd()

        # 绘制眼球中心点
        self.draw_2d_circle(x=320, y=240, radius=5, segments=20)

        # 恢复矩阵
        glPopMatrix()

app = None
window = None
sphere_widget = None

# 启动OpenGL窗口
def start_gl_window():
    global app, window, sphere_widget
    app = QApplication(sys.argv)
    window = QMainWindow()
    sphere_widget = SphereWidget()

    window.setCentralWidget(sphere_widget)
    window.setWindowTitle("GL Sphere")
    window.resize(Config.W, Config.H)
    window.show()

    # 使用定时器定期刷新OpenGL窗口
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(16)


# 根据视线向量更新球体的旋转
def update_sphere_rotation(rot_x, rot_y):
    global sphere_widget
    
    if sphere_widget is None:
        return

    sphere_widget.sphere_rot_x = rot_x
    sphere_widget.sphere_rot_y = rot_y

    sphere_widget.update()

# 获取OpenGL渲染的图像
def get_gl_image():
    glFinish()
    w = sphere_widget.width()
    h = sphere_widget.height()
    glReadBuffer(GL_FRONT)
    pixels = glReadPixels(0, 0, w, h, GL_RGB, GL_UNSIGNED_BYTE)
    image = np.frombuffer(pixels, dtype=np.uint8).reshape((h, w, 3))
    image = np.flipud(image)
    return image

# 通过python -m process.gl_sphere运行gl_sphere测试，你会看到一个旋转的球体
if __name__ == "__main__":
    start_gl_window()
    i = 1
    while True:
        update_sphere_rotation(20, i)
        i = (i + 1) % 360
        cv2.waitKey(1)
