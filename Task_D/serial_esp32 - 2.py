# live_camera_optimized.py
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
TIMEOUT = 0.1  # 减小超时时间
BUFFER_SIZE = 8192  # 增大缓冲区

# Load a model
model = YOLO("C:\\Users\\Richa\\Desktop\\YOLOv10x_gestures.pt")  # load a custom model

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

def process_frame(img_data):
    """优化的图像处理函数"""
    try:
        frame = np.frombuffer(img_data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        return frame
    except Exception as e:
        print(f"图像处理错误: {e}")
        return None

def main():
    # 配置串口
    ser = serial.Serial(
        port=PORT,
        baudrate=BAUD,
        timeout=TIMEOUT,
        write_timeout=TIMEOUT,
        inter_byte_timeout=None,  # 禁用字节间超时
        xonxoff=False,
        rtscts=False,
        dsrdtr=False
    )
    
    # 设置较大的串口缓冲区
    ser.set_buffer_size(rx_size=BUFFER_SIZE, tx_size=BUFFER_SIZE)
    
    # 创建窗口
    cv2.namedWindow('Camera', cv2.WINDOW_AUTOSIZE)
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
                
                # 处理并显示图像
                frame = process_frame(img_data)
                if frame is not None:
                    cv2.imshow('Camera', frame)
                    
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
