# BÁO CÁO TỔNG HỢP TIẾN ĐỘ VÀ ĐÓNG GÓP DỰ ÁN
**Đề tài:** Phát hiện Gian lận và Giả mạo Hóa đơn / Biên lai Nhiệt (Thermal POS Receipt Tampering Detection)  
**Nhóm thực hiện:** Zang (Data Lead), Dâm Nguyễn (Benchmark Lead), Mỹ (Failure Analysis Lead)  
**Thời gian cập nhật:** 08/11/2026

---

## 1. BẢNG PHÂN CÔNG VÀ KẾT QUẢ ĐẠT ĐƯỢC

| Thành viên | Trách nhiệm chính | Môi trường | Deliverables chính | Trạng thái |
| :--- | :--- | :--- | :--- | :---: |
| **Zang** | **Dataset & Generator Lead**<br>• Sinh dữ liệu tổng hợp V2 & V3<br>• Thiết kế logic giả mạo pixel & số học | Linux (Machine A)<br>Python stdlib + PIL | • `thermal_receipts/generate_dataset_500.py` (V2)<br>• `thermal_receipts/generate_forgery_v3.py` (V3)<br>• `thermal_receipts/fonts/` (7 TTF fonts)<br>• Nhãn tài chính & `arith_consistent` (Z2) | **Hoàn thành 100%** |
| **Dâm Nguyễn** | **Benchmark & Pipeline Lead**<br>• Setup & chạy mô hình SOTA GPU<br>• Đánh giá biến thể nén & phân giải | Windows (Machine B)<br>GPU + PyTorch + Paddle | • `benchmarks/build_dataset_sample.py`<br>• `benchmarks/adcdnet_infer.py` (PaddleOCR + GPU)<br>• `benchmarks/eval_sota.py`<br>• Kết quả benchmark V2 (5.000 ảnh) & V3 (3.000 ảnh)<br>• Resolution Ablation Report (512 vs 1024 vs 2048) | **Hoàn thành 100%** |
| **Mỹ** | **Failure Analysis & Synthesis Lead**<br>• Phân tích lỗi & kiểm định giả thuyết<br>• Đánh giá đa phương thức (Scenario C) | Linux/Python<br>Data Science & Stats | • Yêu cầu cải tiến Z1-Z4 (cho Zang) & T1-T7 (cho Dâm)<br>• `six_seven/analysis/analyze_results.py`<br>• `six_seven/analysis/make_figures.py`<br>• Đột phá Fusion Pixel + Arithmetic (TPR > 85%)<br>• Trọn bộ 4 đồ thị & 20+ bảng thống kê bài báo | **Hoàn thành 100%** |

---

## 2. CHI TIẾT ĐÓNG GÓP CỦA TỪNG THÀNH VIÊN

### 👤 1. ZANG — Dataset Generator & Simulation Lead

* **Khắc phục và chuẩn hóa Dataset V2 (500 cặp hóa đơn):**
  - Sửa lỗi RNG drift trên barcode và mã hóa đơn, tách độc lập RNG nội dung (`seed`) và RNG thao tác giả mạo (`seed + 7777777`).
  - Sinh 500 cặp hóa đơn (`cafe`, `supermarket`, `convenience`, `custom` - mỗi loại 125 mẫu) với 3 dạng gian lận: `grand_total_only`, `qty_and_total`, `full_financial`.
* **Xây dựng Dataset V3 Realistic Forgery (Z1 - 300 cặp, 75 mẫu/template):**
  - Giữ nguyên ảnh gốc `authentic` từ V2 (trùng 100% mã hash SHA-256).
  - Triển khai 4 phương pháp giả mạo trực tiếp trên pixel ảnh thật (cân bằng chính xác 75 mẫu/phương pháp):
    1. `copy_move`: Cắt các ký tự số từ vị trí khác trên cùng hóa đơn ghép vào vùng cần sửa, xóa nền bằng patch giấy nhiệt lân cận.
    2. `splice_font`: Xóa nền và vẽ lại bằng font chữ khác (`LiberationSans` / `LiberationMono`).
    3. `splice_same_font`: Vẽ lại bằng `DejaVuSansMono` và áp dụng bộ lọc mờ viền / làm nét viền (`blur` / `sharpen`).
    4. `double_jpeg`: Nén JPEG trước (`QF ∈ {75, 85, 95}`) → chỉnh sửa pixel → nén JPEG lại ở QF khác, căn chỉnh chính xác theo lưới DCT $8 \times 8$.
  - Đảm bảo kiểm tra nghiêm ngặt: $100\%$ mẫu đạt `diff_outside_mask_px == 0` trên cả 3 kênh RGB.
* **Chuẩn hóa nhãn nhất quán số học (Z2 - Semantic/Arithmetic Label):**
  - Tích hợp cấu trúc dòng tiền in thực tế: `items`, `subtotal`, `discount`, `vat_percent`, `vat`, `grand_total`.
  - Gán nhãn `arith_consistent: bool`: $100\%$ authentic = `True`; $100\%$ `grand_total_only` & `qty_and_total` = `False`; $100\%$ `full_financial` = `True`.
* **Đóng gói Font di động (Z3):**
  - Đóng gói 7 file font tĩnh TrueType (`DejaVu` & `Liberation`) trong thư mục `thermal_receipts/fonts/` kèm CLI `--font-dir`, cho phép chạy hoàn hảo trên cả Linux và Windows không phụ thuộc font hệ thống.
* **Xác định ranh giới phạm vi (Z4):**
  - Định rõ phạm vi nghiên cứu tập trung vào hóa đơn nhiệt POS, loại trừ biên lai ngân hàng điện tử do thiếu tính ràng buộc số học nhiều dòng cần cho Scenario C.

---

### 👤 2. DÂM NGUYỄN — Benchmark Implementation & GPU Lead (Machine B)

* **Chuẩn hóa Pipeline xử lý ảnh thực nghiệm:**
  - Viết `build_dataset_sample.py` tự động sinh 5 biến thể nén chuẩn: `png` (gốc), `jpeg95`, `jpeg85`, `jpeg75`, và `social_sim` (mô phỏng nén mạng xã hội: resize $\times 0.75$ bicubic + JPEG Q70).
  - Đánh giá song song trên cả 2 ground-truth mask: `official_mask` (vùng bounding box) và `diff_mask` (từng pixel thay đổi thật sự).
* **Triển khai các mô hình SOTA và Baselines:**
  - **ADCD-Net:** Tự viết engine inference đơn GPU (`adcdnet_infer.py`), tích hợp PaddleOCR PP-OCRv5 tạo text mask tự động với tăng tốc GPU, sửa lỗi checkpoint `save_ckpt` trong mã nguồn mở gốc.
  - **TruFor:** Chạy inference xuất map xác suất và tích hợp điểm nhận diện gốc (`score_source=native`) theo đúng yêu cầu T1.
  - **Baselines:** Chạy kiểm thử đối chứng với ELA (Error Level Analysis) và Random baseline.
* **Thực nghiệm then chốt — Resolution Ablation trên ADCD-Net (T3):**
  - Khám phá và thực nghiệm ở 3 mức phân giải: `512px` (mặc định của tác giả), `1024px`, và `2048px` (kích thước đầy đủ).
  - **Kết quả đột phá:**
    - Ở 512px: F1@0.5 chỉ đạt `0.0265`, Det_AUC = `0.5619` (gần như mất khả năng định vị).
    - Ở 1024px: F1@0.5 tăng lên `0.1373`, Det_AUC = `0.6834`.
    - Ở 2048px (full-res): F1@0.5 đạt `0.1502`, **Det_AUC đạt `0.7002`**!
  - Chứng minh thực nghiệm kết luận: Thao tác downscale về 512px trong bài báo ADCD-Net gốc đã phá hủy toàn bộ vết giả mạo kích thước nhỏ trên hóa đơn.

---

### 👤 3. MỸ — Failure Analysis & Multi-modal Fusion Lead

* **Phân tích căn nguyên thất bại trên Dataset V2:**
  - Nhận diện lý do SOTA đạt AUC $\approx 0.50$ trên V2: Cả ảnh thật và giả đều sinh tham số bằng code từ cùng một font và nền, không có vết can thiệp pixel thật.
  - Đưa ra danh sách yêu cầu chuẩn hóa Z1-Z4 cho Zang và T1-T7 cho Dâm để xây dựng tập V3.
* **Phân tích định lượng so sánh V2 vs V3:**
  - So sánh trực tiếp trên cùng tập mẫu:
    - `TruFor`: Det_AUC tăng từ `0.498` (V2) lên **`0.571`** (V3), F1 tăng từ `0.111` lên **`0.170`**.
    - `ADCD-Net`: Det_AUC tăng từ `0.495` (V2) lên **`0.700`** (V3 full-res), F1 tăng từ `0.002` lên **`0.150`**.
  - Kết luận bài báo: Các mô hình thị giác máy tính SOTA hoàn toàn có khả năng bắt được vết giả mạo khi tài liệu có can thiệp pixel thực tế.
* **Đóng góp học thuật xuất sắc nhất — Mô hình kết hợp Scenario C (Fusion):**
  - Đề xuất và kiểm nghiệm mô hình kết hợp giữa **Dấu vết vật lý pixel (Pixel Forensics)** và **Kiểm tra tính nhất quán số học (Arithmetic Consistency)**:
    - *Chỉ dùng TruFor pixel:* TPR đạt $13.8\%$ (FPR = 5%).
    - *Chỉ dùng ADCD-Net full-res:* TPR đạt $33.3\%$ (FPR = 5%).
    - *Chỉ dùng kiểm tra số học:* TPR đạt $68.3\%$ (FPR = 0%).
    - **KẾT HỢP FUSION (Pixel + Arithmetic):** Nâng TPR lên **82.4%** (toàn bộ 300 mẫu) và **85.4%** (trên 220 mẫu dễ đọc), trong khi vẫn giữ FPR ở mức chỉ $5\%$.
* **Hệ thống hóa đồ thị & bảng biểu nghiên cứu:**
  - Viết `analyze_results.py` và `make_figures.py`.
  - Xuất 4 đồ thị chuẩn bài báo: `fig1_auc_by_cue.png` (AUC theo loại vết giả mạo), `fig2_compression.png` (ảnh hưởng của chuẩn nén), `fig3_panels.png` (trực quan hóa phát hiện), `fig4_garbled.png` (ảnh hưởng của OCR).

---

## 3. TỔNG KẾT VỊ TRÍ TÀI LIỆU VÀ MÃ NGUỒN TRÊN REPO

- **Mã nguồn Dataset & Generator (Zang):** `thermal_receipts/` (`generate_dataset_500.py`, `generate_forgery_v3.py`, `fonts/`).
- **Mã nguồn Benchmark & Raw Results (Dâm):** `six_seven/benchmarks/` (`results_v3_realistic/`, `RESOLUTION_REPORT.md`, `adcdnet_infer.py`).
- **Mã nguồn Phân tích & Đồ thị Báo cáo (Mỹ):** `six_seven/analysis/` (`analyze_results.py`, `make_figures.py`, `out/fusion.csv`, `out/figures/`).
- **Nhánh Git hiện có:**
  - `main`: Chứa code generator V3 và font chuẩn của Zang.
  - `dam`: Chứa toàn bộ kết quả thực nghiệm V3 của Dâm.
  - `my`: Chứa toàn bộ kết quả phân tích thống kê và đồ thị của Mỹ.
