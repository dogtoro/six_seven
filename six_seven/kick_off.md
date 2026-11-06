# 🚀 KICK-OFF SPRINT: SOTA Benchmarking on Synthetic Invoices & Research Gap Formulation

> **Địa điểm làm việc chính:** [`six_seven/`](.)  
> **Mục tiêu tối thượng:** Chạy thử nghiệm các mô hình SOTA (ADCD-Net, TruFor, TextShield-R1,...) trên tập dữ liệu **hóa đơn giả mạo** (được sinh tự động từ template của `six_seven`) nhằm xác định rõ **Research Gap** cốt lõi cho đồ án:
> 1. **Hướng 1 (Fine-tuning / Domain Adaptation):** Dữ liệu dùng để thích nghi miền (domain adaptation) cho các SOTA hiện có trên miền ảnh hóa đơn (do zero-shot thất bại).
> 2. **Hướng 2 (New Benchmark):** Đóng gói thành một Benchmark / Dataset chất liệu mới đặc thù (Vietnamese Invoices / Receipts under Real-world Forgery & Social Media Compression).
> 3. **Hướng 3 (New Architecture):** Các SOTA hiện tại có hạn chế căn bản (ví dụ: mù màu, chỉ bắt được nén JPEG mà trượt các thủ đoạn can thiệp font/canvas số trên hóa đơn điện tử), buộc phải đề xuất kiến trúc/cơ chế mới.

---

## 👥 Phân công nhiệm vụ (3 thành viên)

```
                       ┌───────────────────────────────────────────────┐
                       │          ZANG (Data & Synthesis)              │
                       │  • Chuẩn hóa tool sinh hóa đơn mẫu            │
                       │  • Xuất dataset mẫu (Orig, Forged, Mask, Meta)│
                       └───────────────────────┬───────────────────────┘
                                               │
                                               ▼ Cung cấp dataset test (~100–300 mẫu)
                       ┌───────────────────────────────────────────────┐
                       │           DÂM NGUYỄN (SOTA & Pipeline)         │
                       │  • Cấu hình môi trường SOTAs (ADCD-Net, etc.) │
                       │  • Chạy zero-shot benchmark & trích xuất số   │
                       └───────────────────────┬───────────────────────┘
                                               │
                                               ▼ Metrics (IoU, F1, Detection score) & Heatmaps
                       ┌───────────────────────────────────────────────┐
                       │               MỸ (Analysis & Gap)             │
                       │  • Phân tích lỗi định tính (Failure cases)     │
                       │  • So sánh các mô hình & chốt Research Gap    │
                       └───────────────────────────────────────────────┘
```

---

### 1. Zang — Data Pipeline & Dataset Mẫu (Lead Data Synthesis)

* **Trách nhiệm:** Dựa vào các template HTML/Canvas sẵn có trong `six_seven/`, xây dựng bộ dataset hóa đơn mẫu đại diện có ground-truth chuẩn xác.
* **Các đầu việc cụ thể:**
  1. **Khảo sát & Tự động hóa các template hóa đơn:**
     - [`vcb-bill-template/`](vcb-bill-template/): Mẫu hóa đơn giao dịch số (`vcbdark_origin.jpg` vs `vcbdark_fake.jpg`, logic tính mask qua `diff_mask.png`).
     - [`mb_bill/`](mb_bill/): Mẫu hóa đơn dạng sáng (`mbwhite_origin.jpg`, `tool_mb.html`).
     - [`tech_bill/`](tech_bill/): Mẫu hóa đơn dạng chuẩn (`techvn_origin.jpg`, `tool_tech.html`).
  2. **Chuẩn hóa nhãn (Ground-Truth Generation):**
     - Đảm bảo mỗi tờ hóa đơn can thiệp đều xuất ra được:
       - `authentic.jpg` (hóa đơn gốc chuẩn trước khi chỉnh sửa)
       - `tampered.jpg` (hóa đơn đã chỉnh sửa số tiền, tên đơn vị/người nhận, mã số hóa đơn/tham chiếu, thời gian)
       - `mask.png` (ảnh nhị phân pixel-level: 255 = vùng chữ bị can thiệp, 0 = nền sạch)
  3. **Đa dạng hóa biến thể (Degradation Simulation):**
     - Sinh thử nghiệm tập nhỏ **Pilot Dataset (~100–300 ảnh)** với các điều kiện:
       - *Thao tác can thiệp:* Thay đổi số tiền thanh toán (amount), thông tin đối tác/khách hàng, mã hóa đơn.
       - *Mức độ nén:* Ảnh xuất từ Canvas $\rightarrow$ nén JPEG (QF = 95, 85, 75) $\rightarrow$ giả lập gửi/nhận hóa đơn qua các kênh trao đổi (Zalo/Messenger/Web screenshot).
  4. **Bàn giao:** Đóng gói thư mục `six_seven/dataset_sample/` kèm file `metadata.json` mô tả tọa độ bbox, loại can thiệp trên hóa đơn để Dâm Nguyễn đưa vào pipeline benchmark.

---

### 2. Dâm Nguyễn — SOTA Model Deployment & Benchmarking (Lead Compute & Execution)

* **Trách nhiệm:** Tận dụng tài nguyên phần cứng mạnh (GPU máy B) để thiết lập môi trường, chạy kiểm thử các mô hình SOTA trên tập dataset hóa đơn do Zang cung cấp.
* **Các đầu việc cụ thể:**
  1. **Triển khai môi trường SOTA:**
     - **ADCD-Net (ICCV 2025):** Tải checkpoint `ADCDNet.pth` + `docres.pkl`, sửa bug nhỏ trong `ds.py` (chuyển sang chạy 1 GPU, patch dòng 91 `save_ckpt` thành `save`).
     - **Mô hình đối trọng (TruFor / CAFTB-Net / TextShield-R1 nếu sẵn sàng):** Thiết lập pipeline inference nhận diện giả mạo ảnh tài liệu hóa đơn.
  2. **Viết script Benchmark tự động (`eval_sota.py`):**
     - Viết loader nạp dataset hóa đơn mẫu từ `dataset_sample/` của Zang.
     - Sinh Heatmap / Probability map dự đoán từ model.
  3. **Thu thập chỉ số định lượng:**
     - **Pixel-level (Localization):** IoU, F1-score (với ngưỡng threshold động và cố định 0.5).
     - **Image-level (Detection):** Max probability score trên từng ảnh, phân loại hóa đơn Thật vs Giả (AUC-ROC, F1 detection).
  4. **Bàn giao:** Toàn bộ bảng số liệu định lượng (file `.csv` / markdown table) + tập ảnh trực quan hóa kết quả (ảnh hóa đơn | mask thật | prediction heatmap) gửi cho Mỹ.

---

### 3. Mỹ — Failure Analysis & Research Gap Formulation (Lead Academic & Evaluation)

* **Trách nhiệm:** Đánh giá sâu kết quả thực nghiệm từ Dâm Nguyễn, phân tích các điểm yếu cấu trúc của SOTA trên ảnh hóa đơn và xây dựng luận điểm khoa học cho nhóm.
* **Các đầu việc cụ thể:**
  1. **Phân tích lỗi định tính (Qualitative Failure Case Analysis):**
     - Tại sao SOTA bắt trượt chữ bị sửa trên các tờ hóa đơn?
       - Do font chữ đồng nhất, không có vết cắt dán truyền thống (*splice*)?
       - Do nền gradient/nền đồ họa số của hóa đơn không có đặc trưng quang học (PRNU) như tài liệu scan/chụp máy ảnh?
       - Do cơ chế của ADCD-Net bị "mù màu" (grayscale conversion) trong khi hóa đơn số có màu sắc/giao diện đặc thù?
  2. **So sánh tương quan giữa các mức nén:**
     - Đo lường mức độ sụt giảm hiệu năng khi ảnh hóa đơn bị nén qua mạng xã hội hoặc nén JPEG nhiều lần.
  3. **Kết luận Research Gap & Đề xuất giải pháp:**
     - Đưa ra khuyến nghị dựa trên bằng chứng thực nghiệm:
       - *Kịch bản A:* Nếu model phát hiện được dấu vết nhưng localization lệch $\rightarrow$ **Đề xuất Fine-tuning + Domain Adaptation** cho miền hóa đơn.
       - *Kịch bản B:* Nếu các SOTA hoàn toàn bất lực (F1 < 0.1) $\rightarrow$ **Đề xuất Invoice Forgery Benchmark** đóng góp cho cộng đồng nghiên cứu tài liệu.
       - *Kịch bản C:* Nếu bài toán đòi hỏi tích hợp thêm Text Consistency / Semantic Context (LLM/VLM để kiểm tra logic số liệu trên hóa đơn) $\rightarrow$ **Đề xuất Kiến trúc mới kết hợp đa phương thức**.
  4. **Bàn giao:** Báo cáo tổng kết thực nghiệm 2–3 trang kèm hình ảnh minh họa phục vụ buổi họp với thầy.

---

## 📅 Lộ trình hành động (Timeline đề xuất - 48h)

| Mốc thời gian | Zang | Dâm Nguyễn | Mỹ |
|:---|:---|:---|:---|
| **Chặng 1 (0h – 12h)** | Khảo sát code HTML/JS trong `six_seven`, viết script export batch hóa đơn đầu tiên (20–30 ảnh) | Thiết lập môi trường ADCD-Net & script inference cơ bản | Soạn khung tiêu chí đánh giá hóa đơn (metrics, failure categories) |
| **Chặng 2 (12h – 24h)** | Hoàn thiện 100–200 mẫu hóa đơn kèm masks + các biến thể nén | Chạy inference trên toàn bộ dataset hóa đơn mẫu, xuất heatmaps & số liệu | Quan sát sơ bộ kết quả, lọc ra các ca sai điển hình (False Positives / False Negatives) |
| **Chặng 3 (24h – 36h)** | Hỗ trợ bổ sung corner-cases (nếu model nhạy cảm với font/kích thước chữ trên hóa đơn) | Tính toán bảng chỉ số hoàn chỉnh (IoU, F1, Detection AUC) | Viết phân tích chi tiết failure cases & tổng hợp biểu đồ so sánh |
| **Chặng 4 (36h – 48h)** | Cùng rà soát và đóng gói repository `six_seven` | Tổng hợp artifact, log thực nghiệm | **Hoàn thành báo cáo Research Gap** chốt định hướng với giáo viên |

---

## 🎯 Tiêu chuẩn đầu ra (Deliverables của Sprint)

1. **`six_seven/dataset_sample/`**: Thư mục dữ liệu hóa đơn mẫu có cấu trúc chuẩn (Images, Masks, Ground-truth labels).
2. **`six_seven/benchmarks/`**: Scripts chạy thử nghiệm SOTA và bảng số liệu định lượng trên hóa đơn.
3. **`six_seven/RESEARCH_GAP.md`**: Bản đúc kết học thuật giải thích rõ lý do chọn hướng đi (Fine-tune vs. Benchmark vs. New Model) kèm minh chứng thực nghiệm.
