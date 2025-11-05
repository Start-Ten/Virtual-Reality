// 为 AI-THINKER 模块准备的 ESP32-CAM MJPEG 流示例（使用 esp_http_server）
#include "esp_camera.h"
#include <WiFi.h>
#include "esp_http_server.h"

// -------- WiFi 配置 ----------
const char* ssid = "你的WiFi名称";
const char* password = "你的WiFi密码";

// -------- 摄像头引脚（AI-THINKER） ----------
#define CAMERA_MODEL_AI_THINKER
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// -------- 全局 stream server handle ----------
httpd_handle_t stream_httpd = NULL;

void startCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_SVGA; // UXGA/XY may be heavy; SVGA 更稳
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    while (true) { delay(1000); } // 停住，方便调试
  }
}

// 根页面（简洁）
esp_err_t index_handler(httpd_req_t *req){
  const char* resp =
    "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'>"
    "<title>ESP32-CAM Stream</title></head><body style='text-align:center;'>"
    "<h2>ESP32-CAM 视频流</h2>"
    "<img src='/stream' style='max-width:100%;width:640px;height:auto;'/>"
    "<p>打开 <code>/stream</code> 可直接看到 MJPEG 流</p>"
    "</body></html>";
  httpd_resp_set_type(req, "text/html");
  httpd_resp_send(req, resp, strlen(resp));
  return ESP_OK;
}

// MJPEG 流处理函数
esp_err_t stream_handler(httpd_req_t *req){
  camera_fb_t * fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;
  char part_buf[64];

  // 设置响应头为 multipart
  res = httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");
  if (res != ESP_OK) return res;

  // 允许 CORS（可选）
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      res = ESP_FAIL;
    } else {
      if (fb->format != PIXFORMAT_JPEG) {
        // 转成 JPEG（动态分配内存）
        if (!frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len)) {
          Serial.println("frame2jpg failed");
          esp_camera_fb_return(fb);
          res = ESP_FAIL;
        }
      } else {
        _jpg_buf_len = fb->len;
        _jpg_buf = fb->buf;
      }
    }

    if (res == ESP_OK) {
      // 边界
      res = httpd_resp_send_chunk(req, "--frame\r\n", strlen("--frame\r\n"));
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, "Content-Type: image/jpeg\r\n", strlen("Content-Type: image/jpeg\r\n"));
    }
    if (res == ESP_OK) {
      snprintf(part_buf, sizeof(part_buf), "Content-Length: %u\r\n\r\n", (unsigned int)_jpg_buf_len);
      res = httpd_resp_send_chunk(req, part_buf, strlen(part_buf));
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, (const char*)_jpg_buf, _jpg_buf_len);
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, "\r\n", 2);
    }

    // 释放内存和 frame buffer
    if (fb->format != PIXFORMAT_JPEG && _jpg_buf) {
      free(_jpg_buf);
      _jpg_buf = NULL;
      _jpg_buf_len = 0;
    }
    if (fb) {
      esp_camera_fb_return(fb);
      fb = NULL;
    }

    if (res != ESP_OK) {
      break;
    }

    // 可调整帧率：延时越短帧率越高
    // delay(30); // 可按需解注释以降低带宽/CPU
  }

  return res;
}

void startCameraServer(){
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 8080;
  config.ctrl_port = 32768;

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    // register index
    httpd_uri_t index_uri = {
      .uri       = "/",
      .method    = HTTP_GET,
      .handler   = index_handler,
      .user_ctx  = NULL
    };
    httpd_register_uri_handler(stream_httpd, &index_uri);

    // register stream
    httpd_uri_t stream_uri = {
      .uri       = "/stream",
      .method    = HTTP_GET,
      .handler   = stream_handler,
      .user_ctx  = NULL
    };
    httpd_register_uri_handler(stream_httpd, &stream_uri);

    Serial.println("Camera HTTP server started on port: 8080");
  } else {
    Serial.println("Failed to start HTTP server");
  }
}

void connectToWiFi() {
  Serial.printf("Connecting to %s ", ssid);
  WiFi.begin(ssid, password);
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - start > 20000) { // 20s 超时提示
      Serial.println("\nWiFi connect timeout, retrying...");
      start = millis();
    }
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void setup() {
  Serial.begin(115200);
  delay(100);

  startCamera();
  connectToWiFi();
  startCameraServer();
}

void loop() {
  // 使用 esp_http_server 不需要在 loop 中 poll server
  delay(1000);
}
