import matplotlib.pyplot as plt
import cv2

def to_bgr(image, contours=None, ellipse=None, circle=None):
    """
    将灰度图像转换为BGR格式，并在图像上绘制轮廓、椭圆和圆形。

    Args:
        image (numpy.ndarray): 输入的灰度图像。
        contours (list, optional): 要绘制的轮廓列表。默认为 None。
        ellipse (tuple, optional): 要绘制的椭圆。格式应为OpenCV的ellipse参数。默认为 None。
        circle (tuple, optional): 要绘制的圆形。格式为 ((center_x, center_y), radius)。默认为 None。

    Returns:
        numpy.ndarray: 绘制了指定形状的BGR格式图像。
    """
    # 将灰度图转换为BGR彩色图，以便绘制彩色线条
    image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    
    # 如果提供了轮廓，用红色绘制
    if contours is not None:
        cv2.drawContours(image_bgr, contours, -1, (0, 0, 255), 2)
    
    # 如果提供了椭圆（代表眼球），用绿色绘制
    if ellipse is not None:
        cv2.ellipse(image_bgr, ellipse, (0, 255, 0), 2)
        # 绘制椭圆中心点
        cv2.circle(image_bgr, (int(ellipse[0][0]), int(ellipse[0][1])), 3, (0, 255, 0), -1)
        
    # 如果提供了圆形（代表瞳孔），用蓝色绘制
    if circle is not None:
        cv2.circle(image_bgr, (int(circle[0][0]), int(circle[0][1])), int(circle[1]), (255, 0, 0), 2)
        # 绘制圆形中心点
        cv2.circle(image_bgr, (int(circle[0][0]), int(circle[0][1])), 3, (255, 0, 0), -1)
        
    # 如果同时提供了椭圆和圆形，绘制一条从眼球中心指向瞳孔中心的向量延长线
    if ellipse is not None and circle is not None:
        # 计算延长线的终点坐标
        extended_x = 2 * ellipse[0][0] - circle[0][0]
        extended_y = 2 * ellipse[0][1] - circle[0][1]
        # 绘制视线方向向量
        cv2.line(image_bgr, (int(ellipse[0][0]), int(ellipse[0][1])), (int(extended_x), int(extended_y)), (0, 0, 255), 2)
        
    return image_bgr

def visualize(image, contours=None, ellipse=None, circle=None):
    """
    使用matplotlib可视化处理后的图像。

    Args:
        image (numpy.ndarray): 输入的灰度图像。
        contours (list, optional): 要绘制的轮廓列表。默认为 None。
        ellipse (tuple, optional): 要绘制的椭圆。默认为 None。
        circle (tuple, optional): 要绘制的圆形。默认为 None。
    """
    # 调用 to_bgr 函数获取带标记的彩色图像
    image_bgr = to_bgr(image, contours, ellipse, circle)
    # 使用matplotlib显示图像
    plt.imshow(image_bgr)
    # 关闭坐标轴显示
    plt.axis('off')
    # 显示图像窗口
    plt.show()