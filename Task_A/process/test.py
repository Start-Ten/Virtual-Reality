import cv2
import numpy as np

# 窗口的尺寸（单位像素）
H = 1200
W = 1920
parameter_mode=1
# 下面的参数需要根据你的设备的物理尺寸进行调整
if parameter_mode==0:
# 像素与物理尺寸的比例（推荐在最大化窗口后测量并计算）
    PIXEL_WORLD_RATIO = 59.8

    # 窗口的物理尺寸（单位：厘米）
    WINDOW_HEIGHT = H / PIXEL_WORLD_RATIO # 18.39cm
    WINDOW_WIDTH = W / PIXEL_WORLD_RATIO # 30.10cm
else:
    WINDOW_HEIGHT = 33.6
    WINDOW_WIDTH = 59.8
    PIXEL_WORLD_RATIO = H / WINDOW_HEIGHT
# 窗口距离眼睛的距离（单位：厘米）
WINDOW_OFFSET = 30.0

# 测试视线落点
def test_landing_point(gaze_dir):
    #gaze_dir: 归一化后的三维视线方向向量 (dx, dy, dz), 无返回值
    
    #TODO 你需要自行完成这部分逻辑，计算出视线落点(x,y)，落点按照常规二维坐标系定义，左上角为原点，向下为x正方向
    x = -(WINDOW_OFFSET/gaze_dir[2])*gaze_dir[1] + WINDOW_HEIGHT/2
    y = -(WINDOW_OFFSET/gaze_dir[2])*gaze_dir[0] + WINDOW_WIDTH/2#默认眼睛正对屏幕中心

    # 创建一个与屏幕大小相当的窗口
    cv2.namedWindow("Landing Point Demo", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Landing Point Demo", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # 创建空白图像并绘制圆点
    image = np.zeros((H, W, 3), dtype=np.uint8)  # 创建一次并保存
    cv2.circle(image, (int(y*PIXEL_WORLD_RATIO),int(x*PIXEL_WORLD_RATIO)), 10, (0, 255, 0), -1)  # 修正坐标顺序

    # 显示图像
    cv2.imshow("Landing Point Demo", image)
    cv2.waitKey(1)



# 通过python -m process.test运行test测试，最大化黑色窗口，然后用尺子测量它的尺寸
if __name__ == "__main__":
    while True:
        cv2.namedWindow("Landing Point Test", cv2.WINDOW_NORMAL)
        cv2.imshow("Landing Point Test", np.zeros((H, W, 3), dtype=np.uint8))
        cv2.waitKey(1)
    