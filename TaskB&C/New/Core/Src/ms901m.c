#include "ms901m.h"
#include <string.h>

// 静态数据存储
#if MS901M_ENABLE_ANGLE
float ms901m_angle[3] = {0};
#endif
#if MS901M_ENABLE_ACCEL
float ms901m_accel[3] = {0};
#endif
#if MS901M_ENABLE_GYRO
float ms901m_gyro[3]  = {0};
#endif

/** 初始化函数：配置 UART 接口（在 CubeMX 初始化UART后调用） */
void MS901M_Init(void) {
    // 确认UART配置了正确的波特率（MS901M_BAUDRATE）等参数，与模块通信参数匹配:contentReference[oaicite:5]{index=5}。
    // 此外，可根据需要在此处清空或复位接收缓冲区。
    #if MS901M_ENABLE_ANGLE
    ms901m_angle[0] = ms901m_angle[1] = ms901m_angle[2] = 0.0f;
    #endif
    #if MS901M_ENABLE_ACCEL
    ms901m_accel[0] = ms901m_accel[1] = ms901m_accel[2] = 0.0f;
    #endif
    #if MS901M_ENABLE_GYRO
    ms901m_gyro[0]  = ms901m_gyro[1]  = ms901m_gyro[2]  = 0.0f;
    #endif
}

/**
  * 轮询读取并解析模块数据帧
  * @return 返回1表示成功解析并更新数据，返回0表示当前无数据帧或解析失败
  */
uint8_t MS901M_Update(void) {
    // 缓存变量
    uint8_t header[2];
    uint8_t id, len;
    uint8_t data_buf[16];  // 最大数据段长度12字节，留一些裕度
    uint8_t checksum, sum_calc;
    HAL_StatusTypeDef status;

    // 阻塞等待第1个帧头字节 (0x55)，超时短等待避免卡死主循环
    status = HAL_UART_Receive(MS901M_UART, &header[0], 1, 10);
    if (status != HAL_OK) {
        return 0; // 未收到数据
    }
    if (header[0] != MS901M_HEADER_BYTE) {
        return 0; // 非帧起始字节，丢弃
    }
    // 等待第2个帧头字节 (0x55)
    status = HAL_UART_Receive(MS901M_UART, &header[1], 1, 2);
    if (status != HAL_OK || header[1] != MS901M_HEADER_BYTE) {
        return 0; // 第二字节不匹配帧头，帧同步失败
    }
    // 接收帧ID和数据长度
    uint8_t id_len[2];
    status = HAL_UART_Receive(MS901M_UART, id_len, 2, 2);
    if (status != HAL_OK) {
        return 0;
    }
    id = id_len[0];
    len = id_len[1];
    // 根据帧ID校验数据长度是否符合预期，以验证帧有效性
    uint8_t expected_len = 0;
    switch (id) {
        case MS901M_ID_ANGLE: expected_len = MS901M_LEN_ANGLE; break;
        case 0x02: expected_len = 8; break;   // 四元数数据帧
        case MS901M_ID_IMU:   expected_len = MS901M_LEN_IMU; break;
        case 0x04: expected_len = 8; break;   // 磁力计数据帧
        case 0x05: expected_len = 10; break;  // 气压计数据帧
        case 0x06: expected_len = 8; break;   // 扩展端口状态帧
        default: expected_len = 0; break;
    }
    if (expected_len == 0 || len != expected_len) {
        return 0; // 未知的帧ID或长度不匹配，丢弃
    }
    // 接收数据段
    status = HAL_UART_Receive(MS901M_UART, data_buf, len, 5);
    if (status != HAL_OK) {
        return 0;
    }
    // 接收校验和
    status = HAL_UART_Receive(MS901M_UART, &checksum, 1, 2);
    if (status != HAL_OK) {
        return 0;
    }
    // 计算校验和 (帧头和校验位之外所有字节相加)
    sum_calc = 0;
    sum_calc += MS901M_HEADER_BYTE + MS901M_HEADER_BYTE + id + len;
    for (uint8_t i = 0; i < len; ++i) {
        sum_calc += data_buf[i];
    }
    if (sum_calc != checksum) {
        return 0; // 校验和不匹配，丢弃该帧
    }
    // 根据帧 ID 解析数据
    if (id == MS901M_ID_ANGLE) {
        // 姿态角数据帧 0x01 [Roll, Pitch, Yaw] 各2字节:contentReference[oaicite:6]{index=6}
        #if MS901M_ENABLE_ANGLE
        int16_t roll_raw  = (int16_t)((data_buf[1] << 8) | data_buf[0]);
        int16_t pitch_raw = (int16_t)((data_buf[3] << 8) | data_buf[2]);
        int16_t yaw_raw   = (int16_t)((data_buf[5] << 8) | data_buf[4]);
        // 转换为浮点角度值： raw/32768 * 180°:contentReference[oaicite:7]{index=7}
        ms901m_angle[0] = (float)roll_raw  * 180.0f / 32768.0f;
        ms901m_angle[1] = (float)pitch_raw * 180.0f / 32768.0f;
        ms901m_angle[2] = (float)yaw_raw   * 180.0f / 32768.0f;
        #endif
    }
    else if (id == MS901M_ID_IMU) {
        // 陀螺仪+加速度数据帧 0x03 [Ax,Ay,Az,Gx,Gy,Gz] 各2字节:contentReference[oaicite:8]{index=8}
        int16_t ax_raw = (int16_t)((data_buf[1] << 8) | data_buf[0]);
        int16_t ay_raw = (int16_t)((data_buf[3] << 8) | data_buf[2]);
        int16_t az_raw = (int16_t)((data_buf[5] << 8) | data_buf[4]);
        int16_t gx_raw = (int16_t)((data_buf[7] << 8) | data_buf[6]);
        int16_t gy_raw = (int16_t)((data_buf[9] << 8) | data_buf[8]);
        int16_t gz_raw = (int16_t)((data_buf[11] << 8) | data_buf[10]);
        // 转换为物理量：加速度(G)和角速度(°/s)
        #if MS901M_ENABLE_ACCEL
        // 加速度 = raw/32768 * 加速度满量程 (单位:G):contentReference[oaicite:9]{index=9}
        ms901m_accel[0] = (float)ax_raw * MS901M_ACC_FSR / 32768.0f;
        ms901m_accel[1] = (float)ay_raw * MS901M_ACC_FSR / 32768.0f;
        ms901m_accel[2] = (float)az_raw * MS901M_ACC_FSR / 32768.0f;
        #endif
        #if MS901M_ENABLE_GYRO
        // 角速度 = raw/32768 * 陀螺仪满量程 (单位:°/s):contentReference[oaicite:10]{index=10}
        ms901m_gyro[0]  = (float)gx_raw * MS901M_GYRO_FSR / 32768.0f;
        ms901m_gyro[1]  = (float)gy_raw * MS901M_GYRO_FSR / 32768.0f;
        ms901m_gyro[2]  = (float)gz_raw * MS901M_GYRO_FSR / 32768.0f;
        #endif
    }
    else {
        // 其他帧 (如0x02四元数、0x04磁力计等)，当前未使用，已在上面读取数据，此处不作处理
    }
    return 1; // 数据已更新
}

/** 获取姿态角 (Roll,Pitch,Yaw)，单位：度(°) */
void MS901M_GetAngle(float angle[3]) {
    #if MS901M_ENABLE_ANGLE
    memcpy(angle, ms901m_angle, 3 * sizeof(float));
    #else
    angle[0] = angle[1] = angle[2] = 0.0f;
    #endif
}

/** 获取加速度 (X,Y,Z)，单位：G */
void MS901M_GetAccel(float accel[3]) {
    #if MS901M_ENABLE_ACCEL
    memcpy(accel, ms901m_accel, 3 * sizeof(float));
    #else
    accel[0] = accel[1] = accel[2] = 0.0f;
    #endif
}

/** 获取陀螺仪角速度 (X,Y,Z)，单位：度每秒(°/s) */
void MS901M_GetGyro(float gyro[3]) {
    #if MS901M_ENABLE_GYRO
    memcpy(gyro, ms901m_gyro, 3 * sizeof(float));
    #else
    gyro[0] = gyro[1] = gyro[2] = 0.0f;
    #endif
}
