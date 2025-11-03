import numpy as np


# 假设有一个球心在原点、半径为radius的球体，在(0, 0, offset)点处有一光源
# 该函数用于求解球在z=0平面的投影半径
def radius_projected(radius, offset):
    return radius * offset / np.sqrt(offset**2 - radius**2)


# 以下各种参数的配置选手可以自行调整
class Config:
    # 相机所拍摄图像的尺寸（单位：像素）
    # 该图像在OpenGL的世界坐标系下对应一块“屏幕”
    H = 480
    W = 640
    WH_RATIO = W / H # 宽高比

    CAMERA_OFFSET = 3.0 # 眼球到相机的距离（以下若无特别说明均处于OpenGL的世界坐标系下）
    FOV_ANGLE_Y = 45.0 # 相机的垂直视野角度
    SCREEN_HEIGHT = CAMERA_OFFSET * 2 * np.tan(np.radians(FOV_ANGLE_Y / 2)) # 屏幕高度
    SCREEN_WIDTH = SCREEN_HEIGHT * WH_RATIO # 屏幕宽度
    PIXEL_WORLD_RATIO = H / SCREEN_HEIGHT # 单位像素与世界坐标下单位长度的比例

    EYEBALL_RADIUS = 1.0 # 眼球半径
    PUPIL_RADIUS = 0.1 # 眼球上瞳孔的半径
    EYEBALL_RADIUS_PROJ = radius_projected(EYEBALL_RADIUS, CAMERA_OFFSET) # 眼球在z=0平面的投影半径
    R = EYEBALL_RADIUS_PROJ * PIXEL_WORLD_RATIO # 眼球在图像上显示的半径（单位：像素）

    # 图像中眼球模型=(中心点坐标, 半径)（单位：像素）
    EYEBALL_MODEL = ((W//2, H//2), R)
