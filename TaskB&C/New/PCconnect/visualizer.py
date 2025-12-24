import sys
import time
import threading
import serial
import serial.tools.list_ports

# 尝试导入图形库
try:
    import pygame
    from pygame.locals import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
except ImportError:
    print("错误: 缺少必要的图形库。")
    print("请运行以下命令安装: pip install pygame PyOpenGL PyOpenGL_accelerate")
    input("按回车键退出...")
    sys.exit(1)

# 全局变量
roll, pitch, yaw = 0.0, 0.0, 0.0
serial_port = None
running = True

def serial_thread_func(port_name, baud_rate):
    """
    后台线程：负责读取串口数据并更新全局变量
    """
    global roll, pitch, yaw, running, serial_port
    try:
        serial_port = serial.Serial(port_name, baud_rate, timeout=1)
        print(f"已连接到 {port_name}")
        
        while running:
            if serial_port.in_waiting:
                try:
                    # 读取一行数据
                    line = serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if not line: continue
                    
                    # 解析 CSV: Roll, Pitch, Yaw, Ax, Ay, Az
                    parts = line.split(',')
                    if len(parts) >= 3:
                        # 提取角度 (假设前三个是 Roll, Pitch, Yaw)
                        r = float(parts[0])
                        p = float(parts[1])
                        y = float(parts[2])
                        
                        # 更新全局变量
                        roll, pitch, yaw = r, p, y
                        
                except ValueError:
                    pass
                except Exception as e:
                    print(f"数据解析错误: {e}")
            else:
                time.sleep(0.002)
                
    except Exception as e:
        print(f"串口连接失败: {e}")
        running = False

def draw_board():
    """
    绘制一个扁平的长方体代表开发板/模块
    """
    # 顶点坐标 (x, y, z)
    vertices = (
        ( 1.0, -0.1, -0.6), # 右下后
        ( 1.0,  0.1, -0.6), # 右上后
        (-1.0,  0.1, -0.6), # 左上后
        (-1.0, -0.1, -0.6), # 左下后
        ( 1.0, -0.1,  0.6), # 右下前
        ( 1.0,  0.1,  0.6), # 右上前
        (-1.0, -0.1,  0.6), # 左下前
        (-1.0,  0.1,  0.6)  # 左上前
    )
    
    # 面索引 (逆时针)
    surfaces = (
        (0,1,2,3), (3,2,7,6), (6,7,5,4),
        (4,5,1,0), (1,5,7,2), (4,0,3,6)
    )
    
    # 颜色 (RGB)
    colors = (
        (0.8, 0.2, 0.2), # 红
        (0.2, 0.8, 0.2), # 绿
        (0.2, 0.2, 0.8), # 蓝
        (0.8, 0.8, 0.2), # 黄
        (0.8, 0.2, 0.8), # 紫
        (0.2, 0.8, 0.8)  # 青
    )

    glBegin(GL_QUADS)
    for i, surface in enumerate(surfaces):
        glColor3fv(colors[i])
        for vertex in surface:
            glVertex3fv(vertices[vertex])
    glEnd()

    # 绘制黑色边框线
    edges = (
        (0,1), (0,3), (0,4), (2,1), (2,3), (2,7),
        (6,3), (6,4), (6,7), (5,1), (5,4), (5,7)
    )
    glBegin(GL_LINES)
    glColor3fv((0,0,0))
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()
    
    # 绘制坐标轴指示
    glBegin(GL_LINES)
    # X轴 (红)
    glColor3fv((1,0,0)); glVertex3f(0,0,0); glVertex3f(2,0,0)
    # Y轴 (绿)
    glColor3fv((0,1,0)); glVertex3f(0,0,0); glVertex3f(0,2,0)
    # Z轴 (蓝)
    glColor3fv((0,0,1)); glVertex3f(0,0,0); glVertex3f(0,0,2)
    glEnd()

def main():
    global running
    
    # 1. 查找并选择串口
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("未发现串口设备！")
        return
    
    print("可用串口:")
    target_port = "COM4"
    selected_port_name = None

    for i, p in enumerate(ports):
        print(f"[{i}] {p.device} - {p.description}")
        if p.device.upper() == target_port:
            selected_port_name = p.device

    if selected_port_name:
        print(f"\n自动选择目标端口: {selected_port_name}")
        port_name = selected_port_name
    else:
        idx_str = input("请输入串口序号 (默认 0): ")
        try:
            idx = int(idx_str)
        except:
            idx = 0
            
        if idx < 0 or idx >= len(ports):
            print("无效序号")
            return

        port_name = ports[idx].device
    
    # 2. 启动串口读取线程
    t = threading.Thread(target=serial_thread_func, args=(port_name, 115200))
    t.daemon = True
    t.start()
    
    # 3. 初始化 Pygame 和 OpenGL
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    pygame.display.set_caption("STM32 IMU 3D Visualizer")

    # 设置透视投影
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5) # 摄像机后退 5 单位

    # 启用深度测试 (防止透视错误)
    glEnable(GL_DEPTH_TEST)

    print("按 ESC 键退出...")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # 清除屏幕和深度缓存
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        
        # 保存当前矩阵状态
        glPushMatrix()
        
        # --- 应用旋转 ---
        # 注意：OpenGL 的旋转顺序和坐标系可能需要根据实际情况调整
        # 这里假设：
        # Roll (翻滚) -> 绕 X 轴
        # Pitch (俯仰) -> 绕 Z 轴 (屏幕平面旋转? 不，通常是绕水平轴)
        # Yaw (偏航) -> 绕 Y 轴 (垂直轴)
        
        # 尝试调整顺序以匹配常见的 IMU 定义：
        # 1. Yaw (Z轴)
        # 2. Pitch (X轴)
        # 3. Roll (Y轴) 
        # 具体轴向取决于模块安装方向和 OpenGL 坐标系差异
        # OpenGL: Y向上, X向右, Z向外(屏幕外)
        
        # 简单映射尝试：
        glRotatef(pitch, 1, 0, 0)  # Pitch 绕 X 轴
        glRotatef(yaw,   0, 1, 0)  # Yaw 绕 Y 轴
        glRotatef(roll,  0, 0, 1)  # Roll 绕 Z 轴
        
        # 绘制物体
        draw_board()
        
        # 恢复矩阵状态
        glPopMatrix()

        # 更新窗口标题显示数值
        pygame.display.set_caption(f"Roll: {roll:.2f} | Pitch: {pitch:.2f} | Yaw: {yaw:.2f}")

        # 刷新屏幕
        pygame.display.flip()
        pygame.time.wait(10) # 限制帧率

    # 退出清理
    if serial_port:
        serial_port.close()
    pygame.quit()

if __name__ == "__main__":
    main()
