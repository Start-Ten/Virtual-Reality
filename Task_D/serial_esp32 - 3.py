# live_camera_with_gesture.py
import serial
import struct
import time
import cv2
import numpy as np
from collections import deque
from ultralytics import YOLO

# 串口配置
PORT = "COM6"
BAUD = 921600
TIMEOUT = 0.1
BUFFER_SIZE = 8192

# 加载手势识别模型
model = YOLO("C:\\Users\\Richa\\Desktop\\YOLOv10x_gestures.pt")

def read_n(ser, n):
    """优化的读取函数"""
    data = bytearray()
    while len(data) < n:
        remaining = n - len(data)
        chunk = ser.read(remaining)
        if not chunk:
            continue
        data.extend(chunk)
    return bytes(data)

def find_header(ser, header=b'IMG', timeout=0.1):
    """优化的帧头查找函数"""
    buf = deque(maxlen=len(header))
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        chunk = ser.read(1)
        if not chunk:
            continue
            
        buf.append(chunk[0])
        if len(buf) == len(header) and bytes(buf) == header:
            return True
    return False

def process_gesture(frame):
    """处理手势识别"""
    try:
        # 使用模型进行预测
        results = model(frame)
        
        # 复制原始帧用于绘制
        annotated_frame = frame.copy()
        
        # 处理检测结果
        for result in results:
            boxes = result.boxes.xyxy  # 获取边界框坐标
            confs = result.boxes.conf  # 获取置信度
            classes = result.boxes.cls  # 获取类别
            
            for box, conf, cls in zip(boxes, confs, classes):
                x1, y1, x2, y2 = map(int, box)
                # 绘制边界框
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # 添加标签
                label = f"{model.names[int(cls)]} {conf:.2f}"
                cv2.putText(annotated_frame, label, (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        return annotated_frame
    except Exception as e:
        print(f"手势识别错误: {e}")
        return frame

def main():
    # 配置串口
    ser = serial.Serial(
        port=PORT,
        baudrate=BAUD,
        timeout=TIMEOUT,
        write_timeout=TIMEOUT,
        inter_byte_timeout=None,
        xonxoff=False,
        rtscts=False,
        dsrdtr=False
    )
    
    # 设置串口缓冲区
    ser.set_buffer_size(rx_size=BUFFER_SIZE, tx_size=BUFFER_SIZE)
    
    # 创建窗口
    cv2.namedWindow('Original Camera', cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow('Gesture Recognition', cv2.WINDOW_AUTOSIZE)
    
    print("按 'q' 键退出")
    last_capture_time = 0
    capture_interval = 0.033  # 约30fps
    
    try:
        while True:
            current_time = time.time()
            
            # 控制采集频率
            if current_time - last_capture_time < capture_interval:
                continue
                
            # 发送采集命令
            ser.write(b'C')
            last_capture_time = current_time

            # 等待帧头
            if not find_header(ser, timeout=0.1):
                continue

            try:
                # 读取长度
                raw_len = read_n(ser, 4)
                (length,) = struct.unpack(">I", raw_len)
                
                # 读取图像数据
                img_data = read_n(ser, length)
                
                # 解码图像
                frame = np.frombuffer(img_data, dtype=np.uint8)
                frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # 显示原始图像
                    cv2.imshow('Original Camera', frame)
                    
                    # 处理手势识别
                    gesture_frame = process_gesture(frame)
                    cv2.imshow('Gesture Recognition', gesture_frame)
                    
                    # 检查退出键
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                        
            except Exception as e:
                print(f"处理错误: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        
    except Exception as e:
        print(f"发生错误: {e}")
        
    finally:
        cv2.destroyAllWindows()
        ser.close()
        print("程序结束")

if __name__ == "__main__":
    main()
