#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// IP của máy tính (Laptop/PC) đang chạy Server Python
const char* backendURL = "http://10.206.163.93:5000/api/remote-log";

const char* ssid = "quang anh";
const char* password = "12345678";

void startCameraServer();

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Tắt cảnh báo sụt áp để tránh Reset liên tục
  Serial.begin(115200);   // Giao tiếp với STM32 (U0R, U0T)
  
  // Cổng debug nếu cần (In ra Serial để xem tình trạng WiFi)
  // Serial.setDebugOutput(true); 

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
  config.xclk_freq_hz = 10000000; // Hạ xuống 10MHz để ổn định hơn
  config.pixel_format = PIXFORMAT_JPEG;

  if(psramFound()){
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 10;           
    config.fb_count = 2;                
  } else {
    config.frame_size = FRAMESIZE_CIF;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    return;
  }

  sensor_t * s = esp_camera_sensor_get();
  s->set_framesize(s, FRAMESIZE_VGA); 
  s->set_vflip(s, 1);     // Giữ nguyên chiều dọc
  s->set_hmirror(s, 0);   // Lật ngang để không bị soi gương (Mirror)

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }

  startCameraServer();
}

void loop() {
  // LẮNG NGHE TÍN HIỆU TỪ STM32
  if (Serial.available()) {
    String logLine = Serial.readStringUntil('\n');
    logLine.trim();
    
    if (logLine.length() > 0) {
      // 1. CHUYỂN TIẾP TRẠNG THÁI LÊN SERVER
      if(WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(backendURL);
        http.addHeader("Content-Type", "application/json");
        
        String jsonPayload = "{\"log\": \"" + logLine + "\"}";
        int httpResponseCode = http.POST(jsonPayload);
        
        // 2. NHẬN LỆNH ĐIỀU KHIỂN TỪ SERVER VÀ GỬI NGƯỢC VỀ STM32
        if (httpResponseCode > 0) {
          String response = http.getString();
          
          // Forward lệnh [OPEN_IN] hoặc [OPEN_OUT] về STM32
          if (response.indexOf("[OPEN_IN]") != -1) {
              int start = response.indexOf("[OPEN_IN]");
              int end = response.indexOf("\"", start);
              if (end == -1) end = response.length() - 1;
              String cmd = response.substring(start, end);
              Serial.println(cmd);
          }
          else if (response.indexOf("[OPEN_OUT]") != -1) {
              int start = response.indexOf("[OPEN_OUT]");
              int end = response.indexOf("\"", start);
              if (end == -1) end = response.length() - 1;
              String cmd = response.substring(start, end);
              Serial.println(cmd);
          }
          else if (response.indexOf("[DENIED]") != -1) {
              Serial.println("[DENIED]");
          }
        }
        http.end();
      } else {
        // Nếu mất WiFi, báo lỗi về cho STM32
        Serial.println("[DENIED]"); 
      }
    }
  }
}