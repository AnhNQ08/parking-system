import cv2
import pytesseract
import os
import numpy as np
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ---------------------------------------------------------------------------
# Format biển số Việt Nam:
#   Xe máy / ô tô 1 hàng : 2 số tỉnh + 1-2 chữ sê-ri + 4-5 số (7-9 ký tự)
#   Ví dụ: 51A12345 | 51AB12345 | 30A12345
# ---------------------------------------------------------------------------
_VN_PLATE_RE = re.compile(r'^[0-9]{2}[A-Z]{1,2}[0-9]{4,5}$')

# Tesseract config tối ưu cho 1 dòng biển số
_OCR_WHITELIST = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
_OCR_CONFIGS = [
    f'--oem 3 --psm 7 -c tessedit_char_whitelist={_OCR_WHITELIST}',   # Single line
    f'--oem 3 --psm 6 -c tessedit_char_whitelist={_OCR_WHITELIST}',   # Uniform block
    f'--oem 3 --psm 8 -c tessedit_char_whitelist={_OCR_WHITELIST}',   # Single word
    f'--oem 1 --psm 7 -c tessedit_char_whitelist={_OCR_WHITELIST}',   # LSTM engine
]


# ── 1. VALIDATE ────────────────────────────────────────────────────────────

def is_valid_vn_plate(text: str) -> bool:
    """Kiểm tra text có đúng format biển số Việt Nam không."""
    return bool(_VN_PLATE_RE.match(text)) if text else False


# ── 2. SỬA LỖI OCR THEO VỊ TRÍ ────────────────────────────────────────────

def correct_ocr_errors(raw: str) -> str:
    """
    Sửa lỗi OCR dựa theo cấu trúc biển số VN:
      - Vị trí 0-1  : PHẢI là số  → sửa O→0, I→1, S→5, Z→2, B→8, G→6
      - Vị trí 2(-3): PHẢI là chữ → sửa 0→O, 1→I, 5→S, 8→B
      - Vị trí còn lại: PHẢI là số → sửa tương tự phần đầu
    """
    if not raw:
        return ''

    text = re.sub(r'[^A-Z0-9]', '', raw.upper())
    if not text:
        return ''

    chars = list(text)

    TO_DIGIT  = {'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'B': '8', 'G': '6', 'T': '7', 'D': '0'}
    TO_LETTER = {'0': 'O', '1': 'I', '5': 'S', '8': 'B', '6': 'G'}

    # 2 ký tự đầu phải là số (mã tỉnh)
    for i in range(min(2, len(chars))):
        chars[i] = TO_DIGIT.get(chars[i], chars[i])

    # Ký tự thứ 2 (index 2) và có thể 3 phải là chữ (sê-ri)
    # Heuristic: nếu chuỗi >= 7 ký tự, vị trí 2 là chữ
    if len(chars) >= 7:
        chars[2] = TO_LETTER.get(chars[2], chars[2])
        # Nếu vị trí 3 cũng là chữ (biển 2 chữ sê-ri, tổng 8-9 ký tự)
        if len(chars) >= 8 and not chars[3].isdigit():
            chars[3] = TO_LETTER.get(chars[3], chars[3])
        # Phần số sau cùng
        start_digit = 4 if len(chars) >= 8 else 3
        for i in range(start_digit, len(chars)):
            chars[i] = TO_DIGIT.get(chars[i], chars[i])

    return ''.join(chars)


# ── 3. TIỀN XỬ LÝ ẢNH ─────────────────────────────────────────────────────

def _upscale(gray: np.ndarray) -> np.ndarray:
    """Phóng to ảnh nhỏ từ ESP32-CAM để OCR chính xác hơn."""
    h, w = gray.shape
    # Mục tiêu: chiều rộng ~600px để Tesseract hoạt động tốt
    if w < 200:
        scale = 4
    elif w < 400:
        scale = 3
    elif w < 600:
        scale = 2
    else:
        return gray
    return cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)


def preprocess_all_strategies(img: np.ndarray):
    """
    Trả về list các ảnh đã xử lý với nhiều chiến lược khác nhau.
    Tesseract hoạt động tốt nhất với ảnh: nền TRẮNG, chữ ĐEN.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    gray = _upscale(gray)

    processed = []

    # ── Chiến lược 1: CLAHE + Otsu (tốt khi ánh sáng không đều)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    blur1 = cv2.GaussianBlur(enhanced, (3, 3), 0)
    _, otsu = cv2.threshold(blur1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed.append(otsu)
    processed.append(cv2.bitwise_not(otsu))   # Cả 2 phiên bản (nền trắng / nền đen)

    # ── Chiến lược 2: Adaptive Threshold (tốt khi có bóng đổ cục bộ)
    # Dùng bilateral filter nhẹ hơn (d=7 thay vì d=11) → nhanh hơn 3-4x
    blur2 = cv2.bilateralFilter(gray, 7, 75, 75)
    adaptive = cv2.adaptiveThreshold(
        blur2, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 4
    )
    processed.append(adaptive)
    processed.append(cv2.bitwise_not(adaptive))

    # ── Chiến lược 3: Morphological closing (làm liền nét chữ đứt đoạn)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    morph_close = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
    processed.append(morph_close)

    # ── Chiến lược 4: Sharpening trước Otsu (tăng tương phản cạnh)
    sharpen_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, sharpen_kernel)
    _, sharp_thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed.append(sharp_thresh)

    return processed


# ── 4. PHÁT HIỆN VÙNG BIỂN SỐ ─────────────────────────────────────────────

def find_plate_regions(img: np.ndarray):
    """
    Phát hiện các vùng có thể là biển số trong ảnh.
    Trả về list các ảnh đã cắt (BGR), ưu tiên vùng có tỉ lệ khung giống biển số VN.
    """
    regions = []
    h_img, w_img = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.bilateralFilter(gray, 7, 75, 75)

    # Phát hiện cạnh
    edges = cv2.Canny(blur, 30, 200)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 2))
    edges = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # Sắp xếp theo diện tích, lấy top 30
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

    seen = set()
    for c in contours:
        area = cv2.contourArea(c)
        # Lọc quá nhỏ hoặc quá lớn (biển số chiếm tối đa ~40% ảnh)
        if area < 500 or area > w_img * h_img * 0.4:
            continue

        x, y, w, h = cv2.boundingRect(c)
        asp = w / h if h > 0 else 0

        # Tỉ lệ biển số VN: 2:1 đến 5.5:1
        if not (1.5 < asp < 5.5):
            continue
        if w < 60 or h < 15:
            continue

        # Tránh duplicate vùng giống nhau
        key = (x // 20, y // 20)
        if key in seen:
            continue
        seen.add(key)

        pad = 8
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(w_img, x + w + pad), min(h_img, y + h + pad)
        region = img[y1:y2, x1:x2]
        if region.size > 0:
            regions.append((area, region))

    # Sắp xếp theo diện tích giảm dần (vùng lớn nhất ưu tiên trước)
    regions.sort(key=lambda r: r[0], reverse=True)
    return [r for _, r in regions[:5]]   # Tối đa 5 vùng ứng viên


# ── 5. CHẠY OCR ────────────────────────────────────────────────────────────

def _ocr_on_image(processed_img: np.ndarray) -> list[str]:
    """Chạy Tesseract với tất cả config, trả về list kết quả đã làm sạch."""
    results = []
    for cfg in _OCR_CONFIGS:
        try:
            raw = pytesseract.image_to_string(processed_img, config=cfg)
            cleaned = re.sub(r'[^A-Z0-9]', '', raw.upper())
            if cleaned:
                results.append(cleaned)
        except Exception:
            pass
    return results


def _score_candidate(text: str) -> float:
    """
    Chấm điểm ứng viên biển số:
      - Khớp format VN → điểm cao nhất
      - Gần 7-8 ký tự → điểm tốt
      - Chuỗi rác dài → điểm thấp
    """
    if is_valid_vn_plate(text):
        return 100.0
    length_score = max(0.0, 10.0 - abs(len(text) - 7) * 2)
    return length_score


# ── 6. HÀM CHÍNH ───────────────────────────────────────────────────────────

def read_license_plate(image_path: str) -> str | None:
    """
    Pipeline nhận diện biển số đa tầng, tối ưu cho ảnh ESP32-CAM chất lượng thấp.

    Luồng xử lý:
      Stage 1 → Cắt vùng biển số → nhiều preprocessing → Tesseract → validate VN
      Stage 2 → Toàn ảnh          → nhiều preprocessing → Tesseract → validate VN
      Stage 3 → Chọn ứng viên tốt nhất trong tất cả kết quả theo score
    """
    if not os.path.exists(image_path):
        return None

    try:
        img = cv2.imread(image_path)
        if img is None:
            return None

        all_candidates: list[str] = []

        # ── STAGE 1: Xử lý vùng biển số đã cắt ──────────────────────────
        plate_regions = find_plate_regions(img)
        for region in plate_regions:
            for processed in preprocess_all_strategies(region):
                for raw in _ocr_on_image(processed):
                    corrected = correct_ocr_errors(raw)
                    if is_valid_vn_plate(corrected):
                        print(f'[OCR-Stage1] Biển số hợp lệ: {corrected}')
                        return corrected
                    if len(corrected) >= 5:
                        all_candidates.append(corrected)

        # ── STAGE 2: Xử lý toàn bộ ảnh ──────────────────────────────────
        for processed in preprocess_all_strategies(img):
            for raw in _ocr_on_image(processed):
                corrected = correct_ocr_errors(raw)
                if is_valid_vn_plate(corrected):
                    print(f'[OCR-Stage2] Biển số hợp lệ: {corrected}')
                    return corrected
                if len(corrected) >= 5:
                    all_candidates.append(corrected)

        # ── STAGE 3: Chọn ứng viên tốt nhất ─────────────────────────────
        if all_candidates:
            best = max(all_candidates, key=_score_candidate)
            score = _score_candidate(best)
            # Chỉ trả về nếu điểm đủ tốt (tránh trả về chuỗi rác)
            if score >= 4.0:
                print(f'[OCR-Fallback] Ứng viên tốt nhất (score={score:.1f}): {best}')
                return best

        print('[OCR] Không nhận diện được biển số.')
        return None

    except Exception as e:
        print(f'[!] Lỗi OCR: {e}')
        return None
