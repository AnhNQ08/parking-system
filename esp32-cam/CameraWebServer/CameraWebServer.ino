#include "esp_camera.h"
#include <WiFi.h>

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

const char* ssid = "quang anh";
const char* password = "12345678";

void startCameraServer();

void setup() {
  Serial.begin(115200);
  
  // BẬT TÍNH NĂNG IN LOG CHI TIẾT CỦA HỆ THỐNG
  Serial.setDebugOutput(true); 
  delay(1000);

  Serial.println("\n\n===== BOOT START =====");
  
  // Kiểm tra tình trạng bộ nhớ ban đầu
  Serial.println("[LOG] Kiem tra bo nho he thong:");
  Serial.printf("- Total heap: %d\n", ESP.getHeapSize());
  Serial.printf("- Free heap: %d\n", ESP.getFreeHeap());
  Serial.printf("- Total PSRAM: %d\n", ESP.getPsramSize());
  Serial.printf("- Free PSRAM: %d\n", ESP.getFreePsram());

  Serial.println("[LOG] Dang cau hinh Camera Pins...");
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = 5;
  config.pin_d1 = 18;
  config.pin_d2 = 19;
  config.pin_d3 = 21;
  config.pin_d4 = 36;
  config.pin_d5 = 39;
  config.pin_d6 = 34;
  config.pin_d7 = 35;
  config.pin_xclk = 0;
  config.pin_pclk = 22;
  config.pin_vsync = 25;
  config.pin_href = 23;
  config.pin_sccb_sda = 26;
  config.pin_sccb_scl = 27;
  config.pin_pwdn = 32;
  config.pin_reset = -1;
  
  // GIẢM XUNG NHỊP XUỐNG 10MHz ĐỂ TĂNG ĐỘ ỔN ĐỊNH GIAO TIẾP
  config.xclk_freq_hz = 10000000; 
  config.pixel_format = PIXFORMAT_JPEG;

  Serial.println("[LOG] Kiem tra PSRAM de set do phan giai...");
  if(psramFound()){
    Serial.println("[LOG] -> PSRAM FOUND! Dang ap dung cau hinh AN TOAN (SVGA).");
    config.frame_size = FRAMESIZE_SVGA; // Đã giảm từ UXGA xuống SVGA
    config.jpeg_quality = 12;           // Đã tăng số (giảm chất lượng nhẹ) để nhẹ RAM
    config.fb_count = 1;                // Chỉ dùng 1 FrameBuffer
  } else {
    Serial.println("[LOG] -> PSRAM NOT FOUND! Dang ap dung cau hinh THAP (CIF).");
    config.frame_size = FRAMESIZE_CIF;
    config.jpeg_quality = 15;
    config.fb_count = 1;
  }

  // Kiểm tra bộ nhớ ngay trước khi khởi tạo
  Serial.println("[LOG] Bo nho truoc khi goi esp_camera_init:");
  Serial.printf("- Free heap: %d\n", ESP.getFreeHeap());
  Serial.printf("- Free PSRAM: %d\n", ESP.getFreePsram());

  Serial.println("[LOG] >>> BAT DAU GOI esp_camera_init() <<<");
  esp_err_t err = esp_camera_init(&config);

  if (err != ESP_OK) {
    Serial.printf("[ERROR] !!! Camera init failed with error 0x%x !!!\n", err);
    return;
  }

  Serial.println("[LOG] <<< ESP_CAMERA_INIT THÀNH CÔNG! >>>");

  sensor_t * s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    Serial.println("[LOG] OV3660 detected");
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  } else {
    Serial.printf("[LOG] Camera PID hien tai: 0x%x\n", s->id.PID);
  }

  s->set_framesize(s, FRAMESIZE_QVGA);

  Serial.println("[LOG] Dang ket noi WiFi...");
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n[LOG] WiFi connected!");
  Serial.print("[LOG] IP address: ");
  Serial.println(WiFi.localIP());

  Serial.println("[LOG] Dang khoi tao Camera Server...");
  startCameraServer();

  Serial.println("[LOG] Camera server da chay!");
}

void loop() {
  delay(10000);
}