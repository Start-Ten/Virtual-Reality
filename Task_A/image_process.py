import cv2
import numpy as np
from process.contours import filter_contour_points,filter_contours
from process.visualize import visualize

def erode_image(image,kernal_size=(10,10)):
    kernal = np.ones(kernal_size,np.uint8)
    return cv2.erode(image, kernal, iterations=1)
def dilate_image(image,kernal_size=(10,10)):
    kernal = np.ones(kernal_size,np.uint8)
    return cv2.dilate(image, kernal, iterations=1)

def open_image(image):
    if image is None:
        raise FileNotFoundError("Image not found, please check the path.")
    else:
        print("Image get successfully.")
        return dilate_image(erode_image(image))

def close_image(image):
    if image is None:
        raise FileNotFoundError("Image not found, please check the path.")
    else:
        print("Image get successfully.")
        return erode_image(dilate_image(image))
    
def Binary_image(image,manual_threshold=127):
    if image is None:
        print("Image not found, please check the path.")
        exit()
    else:
        print("Image found successfully.")
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 应用阈值化
        # 函数返回两个值：一个是计算/使用的阈值，另一个是处理后的二值图像
        # 对于手动阈值，返回的第一个值就是我们传入的 manual_threshold
        _, binary_manual = cv2.threshold(gray_image, manual_threshold, 255, cv2.THRESH_BINARY)
        return binary_manual, gray_image

def extract_contours(image):
    # 确保输入是二值图像
    if len(image.shape) != 2:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 查找轮廓
    contours, hierarchy = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # 将轮廓转换为numpy数组列表
    contour_list = [np.array(contour) for contour in contours]
    return contour_list


if __name__ == "__main__":
    #二值化阈值
    manual_threshold = 40

    #erode&dilate kernel size
    kernal_size=(3,3)
    # --- 读取图像 ---
    image1 = cv2.imread("capture_test.jpg")
    if image1 is None:
        print("Image not found, please check the path.")
        exit()

    binary_image1,gray_image1=Binary_image(image1, manual_threshold)

    # --- 显示结果 ---
    # 创建一个窗口来并排显示所有图像，方便对比
    """ cv2.imshow("Original Gray Image", gray_image1)
    cv2.imshow(f"Manual Threshold (T={manual_threshold})", binary_image1)

    # 等待按键后关闭所有窗口
    cv2.waitKey(0)
    cv2.destroyAllWindows()  """

    #dilate
    dilate_image1=dilate_image(binary_image1,kernal_size)
    """ cv2.imshow(f"Manual Threshold (T={manual_threshold})", binary_image1)
    cv2.imshow("dilate",dilate_image1)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
 """
    #extract contours
    contours=extract_contours(dilate_image1)
    #筛选轮廓调参
    min_area=100
    max_area=100000
    max_ratio=10
    prefiltered_contour=filter_contours(contours,min_area, max_area, max_ratio)
    print("filtering OK")
    visualize(dilate_image1,prefiltered_contour)
    #筛选轮廓点调参
    gap_frac=15
    angle_thresh=10
    min_point=10
    filtered_contour=filter_contour_points(prefiltered_contour,gap_frac,angle_thresh,min_point)
    if filtered_contour is None:
        print("No contour found.")
        exit()

    #可视化
    visualize(dilate_image1,filtered_contour)
    #椭圆拟合
    ellipse = cv2.fitEllipse(filtered_contour)
    ellipse_center = ellipse[0]
    ellipse_axis = ellipse[1]
    ellipse_angle = ellipse[2]
    #圆形参数
    center_x, center_y ,radius= 320,240,205
    #绘制
    # 绘制椭圆
    cv2.ellipse(image1, ellipse, (0, 255, 0), 2)
    # 绘制圆形
    cv2.circle(image1, (center_x, center_y), radius, (0, 0, 255), 2)
    #绘制椭圆中心点
    cv2.circle(image1, (int(ellipse_center[0]), int(ellipse_center[1])), 5, (0, 0, 255), -1)
    #绘制圆形中心点
    cv2.circle(image1, (center_x, center_y), 5, (255, 0, 0), -1)
    #绘制椭圆与圆形中心点连线
    end_x=2*int(ellipse_center[0])-center_x
    end_y=2*int(ellipse_center[1])-center_y
    cv2.line(image1, (int(ellipse_center[0]), int(ellipse_center[1])), (end_x, end_y), (0, 255, 255), 2)

    cv2.imshow("image1",image1)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


    


    

#(已注释)任务3
    """     image2=cv2.imread("pic1.png")
    image3=cv2.imread("pic2.png")
    if image2 is None or image3 is None:
        print("Image not found, please check the path.")
        exit()
    binary_image2,gray_image2=Binary_image(image2, manual_threshold)
    binary_image3,gray_image3=Binary_image(image3, manual_threshold)
    open_image2=open_image(binary_image2)
    close_image3=close_image(binary_image3)
    cv2.imshow("Original pic1",image2)
    cv2.imshow("binary pic1",binary_image2)
    cv2.imshow("open pic1",open_image2)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

    cv2.imshow("Original pic2",image3)
    cv2.imshow("binary pic2",binary_image3)
    cv2.imshow("close pic2",close_image3)

    cv2.waitKey(0)
    cv2.destroyAllWindows() """

