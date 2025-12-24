#ifndef __MS901M_H
#define __MS901M_H

#ifdef __cplusplus
extern "C" {
#endif

#include "stm32f1xx_hal.h"


/* === 用户配置区：选择使用哪个 UART 句柄 === */
extern UART_HandleTypeDef huart2;
#ifndef MS901M_UART
#define MS901M_UART  (&huart2)
#endif

#ifndef MS901M_BAUDRATE
#define MS901M_BAUDRATE   115200               // 默认波特率 115200bps（模块默认波特率）:contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
#endif

/* 用户配置区：传感器数据上报使能（1=使能，0=禁用） */
#define MS901M_ENABLE_ANGLE   1   // 姿态角 (Roll,Pitch,Yaw，帧ID=0x01)
#define MS901M_ENABLE_ACCEL   1   // 加速度 (Ax,Ay,Az，帧ID=0x03 包含在IMU帧)
#define MS901M_ENABLE_GYRO    1   // 陀螺仪 (Gx,Gy,Gz，帧ID=0x03 包含在IMU帧)

/* 用户配置区：加速度计和陀螺仪满量程范围设置
   （应与模块实际配置一致，默认为 ±4G 加速度，±2000dps 角速度）:contentReference[oaicite:2]{index=2} */
#ifndef MS901M_ACC_FSR
#define MS901M_ACC_FSR    4.0f    // 加速度计量程 ±4G 默认值，可修改为 ±2/±8/±16 对应 2.0f/8.0f/16.0f
#endif
#ifndef MS901M_GYRO_FSR
#define MS901M_GYRO_FSR   2000.0f // 陀螺仪量程 ±2000 dps 默认值，可修改为 250/500/1000 对应 250.0f/500.0f/1000.0f
#endif

/* 数据帧协议常量定义 */
#define MS901M_HEADER_BYTE    0x55    // 帧头字节固定为0x55
#define MS901M_ID_ANGLE       0x01    // 姿态角度帧ID
#define MS901M_ID_IMU         0x03    // 陀螺仪+加速度帧ID (IMU数据帧)
#define MS901M_LEN_ANGLE      6       // 姿态角数据段长度（字节）:contentReference[oaicite:3]{index=3}
#define MS901M_LEN_IMU        12      // IMU数据段长度（字节）:contentReference[oaicite:4]{index=4}

/* 导出数据缓存：姿态角 (roll, pitch, yaw) 和加速度 (x, y, z) */
#if MS901M_ENABLE_ANGLE
extern float ms901m_angle[3];   // 单位：度 (°)，顺序为 Roll, Pitch, Yaw
#endif
#if MS901M_ENABLE_ACCEL
extern float ms901m_accel[3];   // 单位：G，顺序为 Ax, Ay, Az (1G≈9.8m/s^2)
#endif
#if MS901M_ENABLE_GYRO
extern float ms901m_gyro[3];    // 单位：°/s，顺序为 Gx, Gy, Gz
#endif

/* 驱动接口函数 */
void MS901M_Init(void);                      // 初始化 MS901M 驱动
uint8_t MS901M_Update(void);                 // 轮询接收并解析一帧数据，如成功解析返回1，否则返回0
void MS901M_GetAngle(float angle[3]);        // 获取当前姿态角 (roll, pitch, yaw)
void MS901M_GetAccel(float accel[3]);        // 获取当前加速度 (x, y, z)
void MS901M_GetGyro(float gyro[3]);          // 获取当前陀螺仪角速度 (x, y, z)

#ifdef __cplusplus
}
#endif

#endif /* __MS901M_H */
