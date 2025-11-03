# receive_image_resync.py
import serial
import struct
import time

PORT = "COM6"  # 改为你的端口
BAUD = 115200
TIMEOUT = 10

def read_n(ser, n):
    data = b''
    while len(data) < n:
        chunk = ser.read(n - len(data))
        if not chunk:
            raise IOError("串口读取超时或断开")
        data += chunk
    return data

def find_header(ser, header=b'IMG', timeout=5.0):
    """扫描串口直到找到 header，返回 True/False"""
    end_time = time.time() + timeout
    buf = bytearray()
    hlen = len(header)
    while time.time() < end_time:
        b = ser.read(1)
        if not b:
            continue
        buf += b
        # 只保留最近 hlen 字节
        if len(buf) > hlen:
            buf = buf[-hlen:]
        if bytes(buf) == header:
            return True
    return False

with serial.Serial(PORT, BAUD, timeout=0.5) as ser:
    print("打开串口，发送 capture 命令 'C' ...")
    ser.write(b'C')

    # 等待并扫描头（这里 timeout 可按需调整）
    if not find_header(ser, header=b'IMG', timeout=10.0):
        print("未找到 IMG 头（超时）")
    else:
        # 找到头，接收 4 字节长度（大端）
        raw_len = read_n(ser, 4)
        (length,) = struct.unpack(">I", raw_len)
        print("将接收图片大小：", length, "bytes")

        # 读取图片数据
        img = read_n(ser, length)
        with open("esp32_image.jpg", "wb") as f:
            f.write(img)
        print("图片保存为 esp32_image.jpg")
