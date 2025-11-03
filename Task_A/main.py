import cv2
import tkinter as tk
from tkinter import ttk, filedialog
from process.gl_sphere import start_gl_window, get_gl_image
from process.process import process
import os
# 调试模式
DEBUG_MODE = 2
# 模式-1：调参
# 模式0：仅显示摄像头或视频画面的处理结果
# 模式1：在模式0的基础上叠加OpenGL渲染的结果
# 模式2：在模式1的基础上增加视线落点的测试窗口

# 从摄像头获取视频流并处理
def process_camera():
    global selected_camera
    cam_index = int(selected_camera.get())
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW) # 使用Windows系统中的DirectShow作为视频捕获接口
    cap.set(cv2.CAP_PROP_EXPOSURE, -6) # 设置摄像头曝光度

    if not cap.isOpened():
        print("无法打开摄像头")
        return

    while True:
        ret, frame = cap.read() # 从摄像头读取一帧，其中frame为BGR格式
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # 将图片转为灰度图
        frame = cv2.flip(frame, 0) # 上下翻转图像

        frame_final = process(frame.copy(), DEBUG_MODE) # 处理图像
        cv2.imshow("Eye Tracker", frame_final) # 显示处理后的图像

        if DEBUG_MODE >= 1: # 调试模式为1或2时显示OpenGL窗口
            gl_image = get_gl_image() # 获取OpenGL渲染的图像
            blended = cv2.addWeighted(frame_final, 0.6, gl_image, 0.4, 0) # 将摄像头的图像与OpenGL的图像叠加
            cv2.imshow("Eye Tracker + GL Sphere", blended) # 显示叠加后的图像

        key = cv2.waitKey(1) & 0xFF # 读取键盘输入
        if key == ord('q'): # 按'q'键退出
            break
        elif key == ord(' '): # 按空格键暂停
            cv2.waitKey(0)
        elif key == 13: # 按回车键保存当前帧为capture.jpg
            cv2.imwrite("capture.jpg", frame)

    cap.release() # 释放摄像头
    cv2.destroyAllWindows() # 关闭所有OpenCV窗口


# 从视频文件获取视频流并处理
def process_video():
    # 选择视频文件
    video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4;*.avi")])

    if not video_path:
        print("视频文件路径无效")
        return

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("无法打开视频文件")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.flip(frame, 0)

        frame_final = process(frame.copy(), DEBUG_MODE)
        cv2.imshow("Eye Tracker", frame_final)
        """ cv2.waitKey(0)
        cv2.destroyAllWindows() """

        if DEBUG_MODE >= 1:
            gl_image = get_gl_image()
            blended = cv2.addWeighted(frame_final, 0.6, gl_image, 0.4, 0)
            cv2.imshow("Eye Tracker + GL Sphere", blended)

        key = cv2.waitKey() & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            cv2.waitKey(0)
        elif key == 13:
            i=0
            file_name=f"capture{i}.jpg"
            while os.path.exists(file_name):
                i+=1
                file_name=f"capture{i}.jpg"
            print(f"保存当前帧为{file_name}")
            cv2.imwrite(file_name, frame)

    cap.release()
    cv2.destroyAllWindows()


# 检查编号从0到max_cams-1中哪些摄像头可用，返回可用摄像头列表
def detect_cameras(max_cams=5):
    available_cameras = []
    for i in range(max_cams):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) # 尝试打开编号为i的摄像头
        if cap.isOpened(): # 如果摄像头成功打开，则认为该摄像头可用
            available_cameras.append(i)
            cap.release() # 释放摄像头资源
    return available_cameras


# 选择相机和视频的GUI界面
def selection_gui():
    global selected_camera
    cameras = detect_cameras() # 获取可用的摄像头列表

    # 创建tkinter窗口
    root = tk.Tk()
    root.title("选择输入源")
    tk.Label(root, text="眼动追踪", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(root, text="选择摄像头:").pack(pady=5)

    # 选择摄像头的下拉框，并将用户选择的摄像头保存在全局的selected_camera变量中
    selected_camera = tk.StringVar()
    selected_camera.set(str(cameras[0]) if cameras else "未找到摄像头")

    camera_dropdown = ttk.Combobox(root, textvariable=selected_camera, values=[str(cam) for cam in cameras])
    camera_dropdown.pack(pady=5)

    # 用户选择摄像时，执行process_camera函数
    tk.Button(root, text="开始摄像", command=lambda: [root.destroy(), process_camera()]).pack(pady=5)
    # 用户选择视频时，执行process_video函数
    tk.Button(root, text="浏览视频", command=lambda: [root.destroy(), process_video()]).pack(pady=5)

    # 如果调试模式为1或2，启动OpenGL窗口
    if DEBUG_MODE >= 1:
        start_gl_window() 

    # 运行tkinter窗口主循环
    root.mainloop()


if __name__ == "__main__":
    selection_gui()
