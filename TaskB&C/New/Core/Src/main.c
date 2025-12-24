/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body (Gyro on USART2)
  ******************************************************************************
  * 说明：
  * - 移除 ADC 功能
  * - USART1 → PC 日志；USART2 ↔ MS901M 模块
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "stm32f1xx_hal.h"
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* 模块串口波特率（MS901M 默认 115200/8N1） */
#define MS901M_BAUDRATE 115200

/* 加速度/角速度量程（用于换算；与模块当前量程保持一致） */
#define MS901M_ACC_FSR_G   4.0f     /* ±2/4/8/16 G → 这里默认 4G */
#define MS901M_GYRO_FSR_DPS 2000.0f /* ±250/500/1000/2000 dps → 此处仅示例 */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
static void log_printf(const char *fmt, ...);
/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* 日志串口与模块串口 */
UART_HandleTypeDef  huart1;    /* USART1 → PC 日志（PA9/PA10） */
UART_HandleTypeDef  huart2;    /* USART2 ↔ MS901M（PA2/PA3）    */

/* USER CODE BEGIN PV */
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_USART2_UART_Init(void);

/* ====== 放在文件顶部或紧接着你的宏定义后面 ====== */
#define IMU_PRINT_PERIOD_MS   10     /* 打印周期：10ms 一行（100Hz） */
#define IMU_DRAIN_CALLS       16     /* 每个周期内最多调用多少次 Update 用于“排水” */
/* ================================================ */

/* =========================  MS901M 接口与解析  ========================= */
/* 让驱动使用 USART2（模块接在 USART2）：
   注意：确保你的 ms901m.h 里有
     extern UART_HandleTypeDef huart2;
     #define MS901M_UART  (&huart2)
   若尚未添加，请在 ms901m.h 顶部用户配置区按上面补齐。 */
#define MS901M_UART (&huart2)

/* 驱动头文件（请将 ms901m.h/.c 放到 Core/Inc 与 Core/Src） */
#include "ms901m.h"

/* 提示：若需要快速确认串口是否有数据，可打开简易十六进制抓包输出 */
static void dump_hex_uart2_to_uart1_once(void)
{
  uint8_t b;
  static const char *hex = "0123456789ABCDEF";
  while (HAL_UART_Receive(&huart2, &b, 1, 0) == HAL_OK) {
    char s[4] = { hex[b>>4], hex[b & 0x0F], ' ', 0 };
    HAL_UART_Transmit(&huart1, (uint8_t*)s, 3, 0xFFFF);
  }
}
/* ======================================================================== */

/* USER CODE BEGIN 0 */
/* USER CODE END 0 */

/**
  * @brief  应用入口
  */
int main(void)
{
  /* MCU 基础初始化 */
  HAL_Init();
  SystemClock_Config();

  /* 外设初始化：先 GPIO，再 USART */
  MX_GPIO_Init();
  MX_USART1_UART_Init();   /* USART1 → PC 日志 */
  MX_USART2_UART_Init();   /* USART2 ↔ MS901M */

  /* Gyro 驱动初始化（依赖串口已就绪） */
  MS901M_Init();
  
  /* 主循环 */
  uint32_t t_imu = HAL_GetTick();

  while (1)
  {
    /* -------- ① “排水”：在当前周期内尽量多吃几帧串口数据 --------
       说明：MS901M_Update() 若抓到完整帧就会更新内部角度/加速度数组。
       这里循环多次，有助于把环形缓冲中的新数据及时解析出来。 */
    for (int i = 0; i < IMU_DRAIN_CALLS; ++i) {
      (void)MS901M_Update();
    }

    /* -------- ② 每 10ms 打印一次：IMU 六值（紧凑格式） -------- */
    if (HAL_GetTick() - t_imu >= IMU_PRINT_PERIOD_MS) {
      t_imu += IMU_PRINT_PERIOD_MS;
      float ang[3] = {0};   /* Roll, Pitch, Yaw (deg) */
      float acc[3] = {0};   /* Ax, Ay, Az (G)        */
      MS901M_GetAngle(ang);
      MS901M_GetAccel(acc);
      char buf[160];
      /* 格式：Roll,Pitch,Yaw,Ax,Ay,Az */
      int len = snprintf(buf, sizeof(buf),
          "%.2f,%.2f,%.2f,%.3f,%.3f,%.3f\r\n",
          ang[0], ang[1], ang[2], acc[0], acc[1], acc[2]);
      HAL_UART_Transmit(&huart1, (uint8_t*)buf, (uint16_t)len, 0xFFFF);
    }
  }
}

/* ============================== 时钟配置 ============================== */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) { Error_Handler(); }

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                              | RCC_CLOCKTYPE_PCLK1| RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource   = RCC_SYSCLKSOURCE_HSI; /* 8MHz */
  RCC_ClkInitStruct.AHBCLKDivider  = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;
  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK) {
    Error_Handler();
  }
}

/* ============================== GPIO 时钟 ============================== */
static void MX_GPIO_Init(void)
{
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  /* 如需 LED 指示可在此补充 */
}

/* ============================== USART1 初始化（PC 日志） ============================== */
static void MX_USART1_UART_Init(void)
{
  __HAL_RCC_USART1_CLK_ENABLE();

  huart1.Instance        = USART1;
  huart1.Init.BaudRate   = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits   = UART_STOPBITS_1;
  huart1.Init.Parity     = UART_PARITY_NONE;
  huart1.Init.Mode       = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl  = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK) { Error_Handler(); }
}

/* ============================== USART2 初始化（MS901M 模块） ============================== */
static void MX_USART2_UART_Init(void)
{
  __HAL_RCC_USART2_CLK_ENABLE();

  huart2.Instance        = USART2;
  huart2.Init.BaudRate   = MS901M_BAUDRATE;  /* 115200 */
  huart2.Init.WordLength = UART_WORDLENGTH_8B;
  huart2.Init.StopBits   = UART_STOPBITS_1;
  huart2.Init.Parity     = UART_PARITY_NONE;
  huart2.Init.Mode       = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl  = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK) { Error_Handler(); }
}

/* ============================== 简易日志输出 ============================== */
static void log_printf(const char *fmt, ...)
{
  char buf[160];
  va_list ap;
  va_start(ap, fmt);
  int n = vsnprintf(buf, sizeof(buf), fmt, ap);
  va_end(ap);
  if (n <= 0) return;
  if (n > (int)sizeof(buf)) n = sizeof(buf);
  HAL_UART_Transmit(&huart1, (uint8_t*)buf, (uint16_t)n, 0xFFFF);
}

/* ============================== 错误处理 ============================== */
void Error_Handler(void)
{
  __disable_irq();
  while (1) { /* 可在此处闪烁LED提示 */ }
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
  (void)file; (void)line;
}
#endif
