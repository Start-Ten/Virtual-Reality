import numpy as np

# 射线与球体的相交测试
def intersect_ray_sphere(origin, dir, center, radius):
    """
    判断一条射线是否与球体相交，并返回最近的交点参数 t。

    参数:
        origin (np.ndarray): 射线起点坐标，形如 (3,)。
        dir (np.ndarray): 射线方向向量，形如 (3,)。
        center (np.ndarray): 球心坐标，形如 (3,)。
        radius (float): 球体半径。

    返回:
        float 或 None: 若有交点，返回最近交点到摄像机的距离 t ；否则返回 None。
    """
    a=origin-center
    b=np.dot(a,dir)
    c=np.linalg.norm(dir)
    d=np.linalg.norm(a)
    if b**2<c**2*(d**2-radius**2):
        return None#derta小于0，直线与圆无交点
    else:
        t=(-b-np.sqrt(b**2-c**2*(d**2-radius**2)))/c
        if t<0:
            s=(-b+np.sqrt(b**2-c**2*(d**2-radius**2)))/c
            if s<0:
                return None#两交点在射线相反一侧
            else:
                return s#返回唯一的交点
        else:
            return t#返回最近的交点（有两个交点）
    pass


def compute_gaze(x, y, eyeball_model=None):
    if eyeball_model is None:
        from process.config import Config
        eyeball_model = Config.EYEBALL_MODEL
    """
    根据瞳孔在图像中的位置，计算视线在三维空间中的旋转角度和方向向量。

    参数:
        x (float): 瞳孔在图像中的 x 坐标。
        y (float): 瞳孔在图像中的 y 坐标。
        eyeball_model: 眼球模型参数(默认使用 Config.EYEBALL_MODEL)。

    返回:
        tuple 或 None: 
            - (x_rot, y_rot): 视线在 x 轴和 y 轴的旋转角度（单位：度）。
            - gaze_dir: 归一化后的三维视线方向向量 (dx, dy, dz)。
            如果无法计算则返回 None。
    """
    # 将坐标转换到眼球模型的坐标系
    x = (x-eyeball_model[0][0])/eyeball_model[1]
    y = (eyeball_model[0][1]-y)/eyeball_model[1]

    # 假定球心在原点
    sphere_center = np.array([0.0, 0.0, 0.0])
    from process.config import Config
    camera_position = np.array([0.0, 0.0, Config.CAMERA_OFFSET]) # 这个坐标可以微调
    pupil_proj = np.array([x, y, 0.0])#二维瞳孔位置

    ray_dir = pupil_proj - camera_position
    ray_dir /= np.linalg.norm(ray_dir)#归一化

    # 计算射线与球体的交点
    from process.config import Config
    t = intersect_ray_sphere(camera_position, ray_dir, sphere_center, Config.EYEBALL_RADIUS)
    if t is None:
        return None
    intersection_point = camera_position + t * ray_dir#三维瞳孔位置

    # 计算视线方向
    gaze_dir = intersection_point-sphere_center
    gaze_dir /= np.linalg.norm(intersection_point)
    dx=gaze_dir[0]
    dy=gaze_dir[1]
    dz=gaze_dir[2]
    # 计算旋转角度
    x_rot = np.arctan2(-dy, np.sqrt(dx**2 + dz**2))
    y_rot = np.arctan2(dx, dz)
    return (np.degrees(x_rot), np.degrees(y_rot)), gaze_dir
