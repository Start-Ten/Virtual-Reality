import cv2
import numpy as np

def get_area_and_ratioWH(contour):
    """
    计算轮廓的面积和宽高比。

    参数:
        contour (np.ndarray): 轮廓点集。

    返回:
        area (float): 轮廓面积。
        ratioWH (float): 轮廓外接矩形的宽高比（较大值/较小值）。
    """
    area = cv2.contourArea(contour) # 计算轮廓所围图形的面积
    _, _, w, h = cv2.boundingRect(contour) # 计算轮廓的外接矩形
    ratioWH = max(w / h, h / w) # 计算宽高比或高宽比，确保大于等于1
    return area, ratioWH

def filter_contours(contours, min_area, max_area, max_ratio):
    """
    从所有轮廓中筛选出面积和宽高比符合要求的最大轮廓。

    参数:
        contours (list): 轮廓列表。
        min_area (float): 最小面积阈值。
        max_area (float): 最大面积阈值。
        max_ratio (float): 最大宽高比阈值。

    返回:
        pupil_contour (np.ndarray): 满足条件的最大轮廓, 若无则返回None。
    """
    pupil_area = 0
    pupil_contour = None

    for contour in contours:
        area, ratioWH = get_area_and_ratioWH(contour) # 计算轮廓所围成的面积和宽高比
         # 筛选出面积和宽高比符合要求，且面积最大的轮廓
        if area >= min_area and area <= max_area and ratioWH <= max_ratio and area > pupil_area:
            print(area,' ',end='')
            pupil_area = area
            pupil_contour = contour
    print('')    
    return pupil_contour

def filter_contour_points(contour, gap_frac, angle_thresh, min_point):
    """
    对轮廓点进行筛选，去除异常点，只保留形状平滑且朝向中心的点。

    参数:
        contour (np.ndarray): 轮廓点集。
        gap_frac (int): 前后点采样间隔分母，决定采样间隔。
        angle_thresh (float): 夹角阈值（度），用于判断点是否平滑。
        min_point (int): 最小保留点数, 少于该值返回None。

    返回:
        np.ndarray: 筛选后的轮廓点集, 格式为OpenCV轮廓格式; 若点数不足则返回None。
    """
    contour = np.concatenate(contour, axis=0) # 将轮廓点列表转成一个numpy矩阵
    point_num = len(contour)
    if point_num < min_point: return None # 点数太少不足以在后续步骤中拟合椭圆

    gap = point_num // gap_frac + 1 # 计算采样间隔
    
    filtered_points = []

    center_point = np.mean(contour, axis=0) # 计算轮廓点的中心点

    cos_thresh = np.cos(np.radians(angle_thresh))
    
    for i in range(0, point_num):
        # 采样三个轮廓点
        current_point = contour[i]
        prev_point = contour[(i - gap + point_num) % point_num]
        next_point = contour[(i + gap) % point_num]
        
        # 计算两个关键的向量
        vec1 = (prev_point - current_point + next_point - current_point) / 2
        vec2 = center_point - current_point
        
        # 判断这两个关键向量之间的夹角是否小于阈值
        if np.dot(vec1, vec2) >= cos_thresh * np.linalg.norm(vec1) * np.linalg.norm(vec2):
            filtered_points.append(current_point)
    
    # 点数太少不足以在后续步骤中拟合椭圆
    if len(filtered_points) < min_point: return None
    
    # 将过滤完的轮廓点列表转成OpenCV轮廓格式
    return np.array(filtered_points, dtype=np.int32).reshape((-1, 1, 2))