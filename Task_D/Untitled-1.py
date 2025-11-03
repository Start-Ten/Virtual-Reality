from ultralytics import YOLO
import cv2
# Load a model
model = YOLO("C:\\Users\\Richa\\Desktop\\YOLOv10x_gestures.pt")  # load a custom model

# Predict with the model
results = model("C:\\Users\\Richa\\Desktop\\043e9e222e835e6cb1dff9afdb17c356.jpg")  # predict on an image

# Access the results
for result in results:
    xywh = result.boxes.xywh  # center-x, center-y, width, height
    xywhn = result.boxes.xywhn  # normalized
    xyxy = result.boxes.xyxy  # top-left-x, top-left-y, bottom-right-x, bottom-right-y
    xyxyn = result.boxes.xyxyn  # normalized
    names = [result.names[cls.item()] for cls in result.boxes.cls.int()]  # class name of each box
    confs = result.boxes.conf  # confidence score of each box


#图片可视化
origin_img = cv2.imread("C:\\Users\\Richa\\Desktop\\043e9e222e835e6cb1dff9afdb17c356.jpg")
# 在结果处理循环中
for result in results:
    boxes = result.boxes.xyxy  # 获取边界框坐标
    for box in boxes:
        x1, y1, x2, y2 = map(int, box)  # 将坐标转换为整数
        cv2.rectangle(origin_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # 在每个边界框上添加标签
        label = f"{result.names[result.boxes.cls.item()]} {result.boxes.conf.item():.2f}"
        cv2.putText(origin_img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
cv2.imshow("result", origin_img)
cv2.waitKey(0)
cv2.destroyAllWindows()