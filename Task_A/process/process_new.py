import cv2
import numpy as np
from process.visualize import to_bgr
from process.contours import filter_contours, filter_contour_points
from process.gaze import compute_gaze
from process.gl_sphere import update_sphere_rotation
from process.config import Config
from process.test import test_landing_point

#参数调整
manual_threshold = 48 #手动二值化阈值，越高黑越多
kernal_size = (3, 3) #膨胀核大小，越高黑越少
dilate_iter = 1 #膨胀迭代次数，越高黑越少
#选手自行调整轮廓筛选参数
min_area=3632
max_area=100000
max_ratio=9#越小越严格
#选手自行调整选点参数
gap_frac=14#越大越严格？
angle_thresh=10#越小越严格
min_point=10#越大越严格

def process(frame, debug_mode=0):
    # TODO 二值化图像，选手自行调整二值化阈值
    _, frame_binary = cv2.threshold(frame, manual_threshold, 255, cv2.THRESH_BINARY)

    # TODO 膨胀操作，去除噪点，选手自行调整膨胀核大小和迭代次数
    kernel = kernal_size
    frame_dilated = cv2.dilate(frame_binary, kernel, iterations=dilate_iter)

    # TODO 获取图像中所有轮廓
    contours, _ = cv2.findContours(frame_dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # TODO 通过面积与宽高比筛选出瞳孔轮廓，选手自行调整面积的上下限，以及宽高比上限
    pupil_contour = filter_contours(contours,min_area, max_area, max_ratio)
    
    if pupil_contour is None:
        return to_bgr(frame)
    # print(get_area_and_ratioWH(pupil_contour))
     
    # TODO 通过检测角度过滤掉非椭圆上的点，选手自行调整选点的间隔、角度的下限以及最少点数
    # 注意这里的gap_frac与间隔的倒数成正比，如gap_frac=9时表示gap=轮廓点总数//9+1，对应的是360/9=40度的角度间隔
    filtered_pupil_contour=filter_contour_points(pupil_contour,gap_frac,angle_thresh,min_point)

    # print(len(filtered_pupil_contour))

    # TODO 拟合椭圆
    try:
        ellipse =cv2.fitEllipse(filtered_pupil_contour)
        if debug_mode==-1:
            cv2.imshow("origin", frame)
            cv2.imshow("binary", frame_binary)
            cv2.imshow("dilated", frame_dilated)
            cv2.imshow("precontours", to_bgr(frame, contours=contours))
            cv2.imshow("contours", to_bgr(frame, contours=pupil_contour))
            cv2.imshow("filtered", to_bgr(frame, contours=filtered_pupil_contour))
            cv2.imshow("ellipse", to_bgr(frame, ellipse=ellipse)) 
    except Exception:
        if debug_mode==-1:
            cv2.imshow("origin", frame)
            cv2.imshow("binary", frame_binary)
            cv2.imshow("dilated", frame_dilated)
            cv2.imshow("precontours", to_bgr(frame, contours=contours))
            cv2.imshow("contours", to_bgr(frame, contours=pupil_contour))
            cv2.imshow("filtered", to_bgr(frame, contours=filtered_pupil_contour))
            return to_bgr(frame)

    #并排展示
    
    # 当调试模式为1或2时，计算视线并更新球体旋转
    if debug_mode >= 1:
        gaze = compute_gaze(ellipse[0][0], ellipse[0][1])
        if gaze is not None:
            update_sphere_rotation(gaze[0][0], gaze[0][1])
            # 当调试模式为2时，显示视线落点测试窗口
            if debug_mode >= 2:
                test_landing_point(gaze[1])

    return to_bgr(frame, ellipse=ellipse, circle=Config.EYEBALL_MODEL)