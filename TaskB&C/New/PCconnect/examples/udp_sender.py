import serial
import serial.tools.list_ports
import socket
import time

# --- 配置 ---
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
BAUD_RATE = 115200

def find_ch340_port():
    """查找描述中包含 CH340 的串口"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "CH340" in port.description:
            return port.device
    return None

def main():
    # 1. 初始化 UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"UDP 目标: {UDP_IP}:{UDP_PORT}")

    # 2. 搜索并连接串口
    target_com_port = find_ch340_port()
    
    if not target_com_port:
        print("错误: 未找到带有 'CH340' 字样的串口。")
        print("当前可用串口:")
        for p in serial.tools.list_ports.comports():
            print(f" - {p.device}: {p.description}")
        return

    try:
        ser = serial.Serial(target_com_port, BAUD_RATE, timeout=1)
        print(f"已连接到串口 {target_com_port}")
    except serial.SerialException as e:
        print(f"无法打开串口 {target_com_port}: {e}")
        print("请检查串口是否被占用或名称是否正确。")
        return

    print("开始转发数据... 按 Ctrl+C 停止")

    try:
        while True:
            if ser.in_waiting:
                try:
                    # 读取一行数据 (例如: "-120.20,50.53,161.03,-0.785,-0.555,-0.324")
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if not line:
                        continue

                    # 简单的校验：确保包含逗号
                    if ',' in line:
                        # 直接将原始字符串通过 UDP 发送给 Unity
                        # Unity 端解析字符串通常比解析二进制结构体更灵活
                        data_bytes = line.encode('utf-8')
                        sock.sendto(data_bytes, (UDP_IP, UDP_PORT))
                        
                        # 可选：打印发送的数据用于调试
                        # print(f"Sent: {line}")

                except Exception as e:
                    print(f"读取/发送错误: {e}")
            else:
                # 避免 CPU 占用过高，稍微休眠
                time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n停止发送。")
    finally:
        ser.close()
        sock.close()
        print("资源已释放。")

if __name__ == "__main__":
    main()
