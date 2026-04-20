import cv2
import os
import numpy as np
import re
import easyocr

# Khoi tao mo hinh EasyOCR (su dung ngon ngu tieng Anh)
# Lan dau chay co the ton mot chut thoi gian de tai model weights
print("[INFO] Dang tai mo hinh EasyOCR...")
reader = easyocr.Reader(['en'], gpu=False, verbose=False)  # Dat gpu=True neu may tinh co card roi NVIDIA
print("[INFO] Tai mo hinh thanh cong!")

def preprocess_for_easyocr(img: np.ndarray) -> np.ndarray:
    # Phóng to x2 là đủ
    h, w = img.shape[:2]
    img = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    
    # Xám hóa và tăng tương phản nhẹ (CLAHE)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    return gray

def correct_special_format(text: str) -> str:
    if not text or len(text) < 2: return text
    
    # Sửa lỗi phổ biến cho 2 ký tự đầu (thường là mã tỉnh - số)
    # Nhưng vẫn giữ lại toàn bộ các ký tự phía sau
    chars = list(text)
    
    # Ví dụ: Nếu ký tự đầu là 'O' thì đổi thành '0' (vì mã tỉnh bắt đầu bằng số)
    m_num = {'O':'0', 'D':'0', 'I':'1', 'S':'5', 'B':'8'}
    if chars[0] in m_num: chars[0] = m_num[chars[0]]
    if chars[1] in m_num: chars[1] = m_num[chars[1]]

    return "".join(chars)

def read_license_plate(image_path: str) -> str | None:
    if not os.path.exists(image_path): return None
    try:
        img = cv2.imread(image_path)
        if img is None: return None
        h, w = img.shape[:2]
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # --- LAN 1: QUET ANH GOC ---
        results = reader.readtext(img_rgb, detail=1)
        
        # --- LAN 2: NEU KHONG THAY thi PHONG TO ---
        if not results:
            img_big = cv2.resize(img_rgb, (0,0), fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            results = reader.readtext(img_big, detail=1)

        # --- LAN 3: CROP CAN THAN (Neu da thay so bo) ---
        if results:
            try:
                # Lay vung chu ro nhat
                best_box = max(results, key=lambda x: x[2])[0]
                ymin = int(max(0, min(p[1] for p in best_box) - 15))
                ymax = int(min(h, max(p[1] for p in best_box) + 15))
                xmin = int(max(0, min(p[0] for p in best_box) - 15))
                xmax = int(min(w, max(p[0] for p in best_box) + 15))
                
                crop = img_rgb[ymin:ymax, xmin:xmax]
                crop = cv2.resize(crop, (0,0), fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
                
                # Quet lai tren vung tieu diem
                new_results = reader.readtext(crop, detail=1)
                if new_results:
                    results = new_results
            except:
                pass # Neu crop loi thi dung ket qua cu

        all_pieces = []
        for (bbox, text, prob) in results:
            raw = text.upper().replace("^", "1").replace("|", "1").replace("!", "1")
            clean = re.sub(r'[^A-Z0-9]', '', raw)
            
            if len(clean) > 0 and prob > 0.15:
                center_x = (bbox[0][0] + bbox[1][0]) / 2
                all_pieces.append((center_x, clean, prob))
                print(f"[AI Raw] Thay: '{clean}' (Goc: '{text}') | Conf: {prob:.2f}", flush=True)

        if all_pieces:
            all_pieces.sort(key=lambda x: x[0])
            combined = "".join([p[1] for p in all_pieces])
            
            final = combined
            if len(final) >= 2:
                final = correct_special_format(final)
            
            print(f'[OCR Pro] Chot: {final} (Conf: {sum(p[2] for p in all_pieces)/len(all_pieces):.2f})', flush=True)
            return final
            
        print("[AI Debug] Khong tim thay chu trong anh.", flush=True)
        return None
    except Exception as e:
        print(f'[!] Loi OCR: {e}', flush=True)
        return None
