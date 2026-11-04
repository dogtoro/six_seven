# 🧾 Six-Seven: Vietnamese Thermal Receipt & Document Image Forgery Synthesis Suite

Bộ công cụ nghiên cứu, sinh dữ liệu hóa đơn in nhiệt giả lập (Thermal POS Receipts) và nhãn can thiệp chuẩn mức pixel (Pixel-level Ground Truth Masks) phục vụ bài toán **Document Image Forgery Detection & Localization (Phát hiện & Định vị Vùng Giả mạo Ảnh Tài liệu)**.

---

## 🌟 Tính Năng Cốt Lõi

1. **Bộ sinh Hóa đơn In nhiệt Đa dạng (Thermal POS Receipt Generator):**
   - Hỗ trợ 4 nhóm ngành hàng thực tế tại Việt Nam:
     - ☕ **Quán Cafe & Trà Sữa (`cafe`):** Khổ 58/80mm, Highlands/Phúc Long style, hỗ trợ Size/Topping, số bàn, mật khẩu Wifi.
     - 🛒 **Siêu thị Bán lẻ (`supermarket`):** Khổ 80mm, WinMart+/Co.opmart style, danh sách nhiều món, thuế VAT, mã tra cứu e-Invoice.
     - 🏪 **Cửa hàng tiện lợi (`convenience`):** Circle K/GS25 style, đồ ăn nhanh, nước ngọt, bố cục hẹp và gọn.
     - ✨ **Tùy chỉnh tự do (`custom`):** Nhà thuốc (Long Châu), Nhà hàng/Quán ăn (Cơm tấm), Nhà sách/Văn phòng phẩm.
2. **Mô phỏng Đặc tính Vật lý của Máy In Nhiệt:**
   - Màu giấy ngà xám tự nhiên (`#f8f8f6`) với lớp vi hạt bề mặt giấy cảm nhiệt.
   - Giả lập vệt xước mờ dọc do đầu in kim/nhiệt bị mòn theo thời gian (*thermal head streaks*).
   - Đường cắt mép giấy răng cưa zíc-zắc (*zigzag cut edge*) chuẩn dao cắt máy POS.
   - Mã vạch 1D Barcode mô phỏng ở chân hóa đơn.
3. **Tự động sinh Ground-Truth Binary Mask (Mức Pixel):**
   - Mỗi mẫu can thiệp đều tự động xuất mặt nạ nhị phân chuẩn xác 100%:
     - `255` (Trắng): Chính xác vùng ký tự chữ bị can thiệp/sửa đổi.
     - `0` (Đen): Nền và các ký tự nguyên bản.
4. **Interactive Studio Tool (Giao diện Web Trực quan):**
   - Chỉnh sửa nội dung thời gian thực trên HTML5 Canvas.
   - Thêm/bớt món, sửa giá, sửa số lượng, đổi tên template tự do.
   - Chế độ Tampered Mode tự động trích xuất Mask.

---

## 📂 Cấu Trúc Thư Mục

```text
six_seven/
├── thermal_receipts/                 # Module Hóa đơn in nhiệt (Chính)
│   ├── tool_thermal_receipt.html     # Studio Web tương tác chỉnh sửa & xuất mẫu
│   ├── generate_thermal_templates.py # Script sinh mẫu cơ sở & viewer index.html
│   ├── generate_dataset_500.py       # Pipeline sinh batch 500 mẫu tự động
│   └── output/                       # Thư mục chứa mẫu xuất thử nghiệm
│       └── index.html                # Trang so sánh trực quan Auth vs Tampered vs Mask
├── dataset/                          # Thư mục lưu 500 mẫu dataset (Ignored on Git)
│   ├── authentic/                    # 500 ảnh hóa đơn gốc sạch
│   ├── tampered/                     # 500 ảnh hóa đơn can thiệp
│   ├── masks/                        # 500 mặt nạ nhị phân ground-truth
│   ├── metadata.json                 # Metadata toàn bộ 500 mẫu
│   └── manifest.jsonl                # Metadata dạng JSON Lines
├── mb_bill/                          # Template MB Bank (Canvas Studio)
├── tech_bill/                        # Template Techcombank (Canvas Studio)
└── vcb-bill-template/                # Template VCB Digibank (Canvas & CDP scripts)
```

---

## 🚀 Hướng Dẫn Sử Dụng

### 1. Dùng Trình Studio Chỉnh Sửa Trực Quan (Web Studio)
Mở file `tool_thermal_receipt.html` bằng trình duyệt (Chrome / Firefox / Edge):
```bash
# Trên Linux / Ubuntu:
firefox six_seven/thermal_receipts/tool_thermal_receipt.html &

# Hoặc mở bằng VS Code Live Server / Live Preview
```
* **Tính năng:**
  - Chọn template có sẵn hoặc tự đặt tên template tại ô **`🏷️ Tên Template`**.
  - Tự do sửa đổi từng trường chữ, thêm/xóa dòng món hàng.
  - Bật switch **`🔴 Đánh dấu Chế độ Giả mạo`** để tự sinh Mask.
  - Bấm **`📦 Xuất Bộ Mẫu`** để tải về đồng thời ảnh Gốc, ảnh Can thiệp, Mask và file Metadata JSON.

### 2. Sinh Thử Nghiệm Mẫu Bằng Python
```bash
python3 six_seven/thermal_receipts/generate_thermal_templates.py
```
* Kết quả sẽ được lưu vào `thermal_receipts/output/`. Bạn có thể mở `thermal_receipts/output/index.html` để xem so sánh song song.

### 3. Sinh Tập Dữ Liệu Lớn (500 Mẫu Dataset Benchmark)
```bash
python3 six_seven/thermal_receipts/generate_dataset_500.py
```
* Tự động sinh đều 125 mẫu cho mỗi loại: `cafe`, `supermarket`, `convenience`, `custom`.
* Lưu trữ đồng bộ vào `six_seven/dataset/` kèm mã băm và tọa độ Bounding Box của từng trường bị sửa.

---

## 📋 Cấu Trúc Metadata JSON

Mỗi mẫu trong dataset được ghi nhận chi tiết:
```json
{
  "sample_id": "receipt_0001",
  "template": "cafe",
  "template_id": "cafe_fnb",
  "brand_name": "PHÚC LONG COFFEE & TEA",
  "receipt_code": "HD-20261104-0001",
  "date": "04/11/2026 09:42",
  "width": 620,
  "height": 960,
  "tampering_type": "full_financial",
  "tampered_fields": [
    {
      "field": "item_2_qty",
      "original": "2",
      "forged": "5",
      "bbox": [308, 324, 335, 346]
    },
    {
      "field": "grand_total",
      "original": "194,400 đ",
      "forged": "340,200 đ",
      "bbox": [376, 520, 584, 549]
    }
  ],
  "authentic_file": "authentic/receipt_0001_authentic.png",
  "tampered_file": "tampered/receipt_0001_tampered.png",
  "mask_file": "masks/receipt_0001_mask.png"
}
```

---

## 🛠️ Yêu Cầu Môi Trường (Requirements)

- **Python:** $\ge 3.8$
- **Thư viện:** `Pillow` (PIL) $\ge 9.0$
- **Hệ thống Font:** Hỗ trợ font Monospace có tiếng Việt (ví dụ: `DejaVuSansMono.ttf`, `DejaVuSans.ttf` trên Linux hoặc `Consolas`, `Courier New` trên Windows).
