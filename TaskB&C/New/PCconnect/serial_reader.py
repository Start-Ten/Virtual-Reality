import serial
import serial.tools.list_ports
import time

def find_stm32_port():
    """
    尝试自动查找 STM32 串口 (仅作简单示例，通常需要用户指定)
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # 这里可以根据 VID:PID 或描述来过滤
        # 例如: if "STM32" in port.description:
        print(f"Found port: {port.device} - {port.description}")
    return ports

def main():
    print("Available ports:")
    ports = find_stm32_port()
    
    if not ports:
        print("No serial ports found.")
        return

    # 让用户选择或者默认第一个
    port_name = input(f"Enter COM port (default {ports[0].device}): ")
    if not port_name:
        port_name = ports[0].device

    baud_rate = 115200
    
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=1)
        print(f"Connected to {port_name} at {baud_rate} baud.")
        
        print("Waiting for data...")
        print("Format: Roll, Pitch, Yaw, Ax, Ay, Az")
        
        while True:
            if ser.in_waiting > 0:
                try:
                    # 读取一行并解码
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"Received: {line}")
                        
                        # 简单的解析示例
                        # parts = line.split(',')
                        # if len(parts) == 6:
                        #     roll, pitch, yaw, ax, ay, az = map(float, parts)
                        #     print(f" -> Roll: {roll:.2f}, Pitch: {pitch:.2f}, Yaw: {yaw:.2f}")
                        
                except Exception as e:
                    print(f"Error reading line: {e}")
            
            time.sleep(0.001) # 稍微休眠避免 CPU 占用过高

    except serial.SerialException as e:
        print(f"Could not open serial port {port_name}: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()
