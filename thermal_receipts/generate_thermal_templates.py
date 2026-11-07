import os
import json
import random
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Output directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Fonts (bundled in thermal_receipts/fonts/ for cross-platform portability)
FONT_DIR = os.environ.get("THERMAL_FONT_DIR", os.path.join(SCRIPT_DIR, "fonts"))
FONT_REGULAR_PATH = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf")
FONT_SANS_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")


def create_thermal_background(width, height, add_streaks=True, seed=42):
    """Tạo nền giấy in nhiệt với màu ngà tự nhiên, vân giấy nhẹ và mép xé răng cưa."""
    rng = random.Random(seed)
    
    # Màu giấy in nhiệt: ngà xám tự nhiên
    base_color = (248, 248, 246)
    im = Image.new("RGBA", (width, height), base_color)
    draw = ImageDraw.Draw(im)
    
    # 1. Nhiễu hạt vi mô mô phỏng bề mặt giấy nhiệt
    noise = Image.new("L", (width, height), 0)
    noise_pixels = noise.load()
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            val = rng.randint(0, 12)
            noise_pixels[x, y] = val
            if x + 1 < width: noise_pixels[x + 1, y] = val
            if y + 1 < height: noise_pixels[x, y + 1] = val
            if x + 1 < width and y + 1 < height: noise_pixels[x + 1, y + 1] = val
            
    noise = noise.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Ghép nhiễu vào ảnh
    im_noise = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    im_noise.paste((0, 0, 0, 8), mask=noise)
    im = Image.alpha_composite(im, im_noise)
    
    # 2. Vệt xước nhẹ của đầu in nhiệt (đặc trưng máy in POS xài lâu ngày)
    if add_streaks:
        streak_draw = ImageDraw.Draw(im)
        for _ in range(rng.randint(2, 4)):
            sx = rng.randint(40, width - 40)
            sw = rng.choice([1, 2])
            opacity = rng.randint(15, 30)
            streak_draw.line([(sx, 0), (sx, height)], fill=(255, 255, 255, opacity), width=sw)

    # 3. Tạo viền xé răng cưa ở đầu và đuôi bill (Zigzag cut)
    cut_draw = ImageDraw.Draw(im)
    step = 10
    top_points = [(0, 0)]
    for x in range(0, width + step, step):
        y_cut = (step // 2) if (x // step) % 2 == 1 else 0
        top_points.append((x, y_cut))
    top_points.append((width, 0))
    cut_draw.polygon(top_points, fill=(240, 240, 238, 255))
    
    bot_points = [(0, height)]
    for x in range(0, width + step, step):
        y_cut = height - ((step // 2) if (x // step) % 2 == 1 else 0)
        bot_points.append((x, y_cut))
    bot_points.append((width, height))
    cut_draw.polygon(bot_points, fill=(240, 240, 238, 255))

    return im.convert("RGB")


def draw_barcode(draw, x, y, width, height, code_seed=123):
    """Vẽ mã vạch 1D mô phỏng ở chân hóa đơn."""
    rng = random.Random(code_seed)
    cur_x = x
    while cur_x < x + width - 15:
        bar_w = rng.choice([1, 2, 3, 4])
        space_w = rng.choice([2, 3, 4])
        draw.rectangle([cur_x, y, cur_x + bar_w, y + height], fill=(30, 30, 30))
        cur_x += bar_w + space_w


def render_cafe_receipt(tampered=False, seed=100, template_name="PhucLong_Cafe_K80", store_title="PHÚC LONG COFFEE & TEA"):
    # Mẫu Quán Cafe / Trà Sữa (Highlands / Phúc Long) - Khổ 58mm/80mm
    width = 620
    height = 980
    bg = create_thermal_background(width, height, add_streaks=True, seed=seed)
    
    # Masks
    mask = Image.new("L", (width, height), 0)
    
    # Fonts
    font_title = ImageFont.truetype(FONT_SANS_BOLD, 26)
    font_sub = ImageFont.truetype(FONT_REGULAR_PATH, 16)
    font_bold = ImageFont.truetype(FONT_BOLD_PATH, 18)
    font_text = ImageFont.truetype(FONT_REGULAR_PATH, 17)
    font_item = ImageFont.truetype(FONT_REGULAR_PATH, 16)
    font_total = ImageFont.truetype(FONT_BOLD_PATH, 24)
    font_footer = ImageFont.truetype(FONT_REGULAR_PATH, 15)
    
    draw = ImageDraw.Draw(bg)
    mask_draw = ImageDraw.Draw(mask)
    
    ink_color = (25, 25, 25)
    ink_tamper = (28, 28, 28) # Màu hơi khác vi mô nếu bị can thiệp
    
    metadata = {
        "template": template_name,
        "is_tampered": tampered,
        "width": width,
        "height": height,
        "tampered_fields": []
    }

    # 1. HEADER
    y = 35
    # Tiêu đề quán
    title = store_title
    tb = font_title.getbbox(title)
    draw.text(((width - (tb[2] - tb[0])) // 2, y), title, fill=ink_color, font=font_title)
    y += 35
    
    sub1 = "CN Vincom Center, 72 Lê Thánh Tôn, Q.1"
    draw.text(((width - font_sub.getbbox(sub1)[2]) // 2, y), sub1, fill=ink_color, font=font_sub)
    y += 24
    
    sub2 = "Hotline: 1900 2345 - Wifi: PhucLong_Guest"
    draw.text(((width - font_sub.getbbox(sub2)[2]) // 2, y), sub2, fill=ink_color, font=font_sub)
    y += 32
    
    header_title = "=== HÓA ĐƠN BÁN HÀNG ==="
    draw.text(((width - font_bold.getbbox(header_title)[2]) // 2, y), header_title, fill=ink_color, font=font_bold)
    y += 30
    
    # Meta info
    draw.text((45, y), "Số HD: PL-20261104-0892", fill=ink_color, font=font_text)
    draw.text((360, y), "Bàn: T04 (Mang đi)", fill=ink_color, font=font_text)
    y += 24
    draw.text((45, y), "Ngày: 04/11/2026 09:42", fill=ink_color, font=font_text)
    draw.text((360, y), "TN: Nguyễn Văn A", fill=ink_color, font=font_text)
    y += 28
    
    # Đường kẻ phân cách
    div_line = "------------------------------------------------"
    draw.text((45, y), div_line, fill=ink_color, font=font_text)
    y += 22
    
    # 2. BẢNG MẶT HÀNG (Item Table)
    # Header bảng
    tbl_hdr = f"{'Tên món':<20} {'SL':>3} {'Đ.Giá':>9} {'T.Tiền':>11}"
    draw.text((45, y), tbl_hdr, fill=ink_color, font=font_bold)
    y += 24
    draw.text((45, y), div_line, fill=ink_color, font=font_text)
    y += 24
    
    # Items
    items = [
        {"name": "Trà Đào Cam Sả (L)", "qty": 1, "price": 65000, "total": 65000},
        {"name": "  + Thạch đào", "qty": 1, "price": 10000, "total": 10000},
        {"name": "Cà Phê Sữa Đá (M)", "qty": 2, "price": 45000, "total": 90000},
        {"name": "Bánh Mì Chà Bông", "qty": 1, "price": 35000, "total": 35000},
    ]
    
    # Kịch bản can thiệp: Nếu tampered=True -> Sửa số lượng 'Cà Phê Sữa Đá' từ 2 lên 5 và tăng thành tiền
    for it in items:
        item_y = y
        name = it["name"]
        qty_str = str(it["qty"])
        price_str = f"{it['price']:,}"
        tot_str = f"{it['total']:,}"
        
        if tampered and it["name"] == "Cà Phê Sữa Đá (M)":
            # Can thiệp số lượng và thành tiền
            forged_qty = "5"
            forged_tot = "225,000"
            
            # Vẽ tên món và đơn giá bình thường
            draw.text((45, y), f"{name:<20}", fill=ink_color, font=font_item)
            draw.text((365, y), f"{price_str:>9}", fill=ink_color, font=font_item)
            
            # VÙNG GIẢ MẠO 1: Số lượng (2 -> 5)
            qx = 280
            draw.text((qx, y), f"{forged_qty:>3}", fill=ink_tamper, font=font_item)
            q_bbox = font_item.getbbox(forged_qty)
            # Tọa độ bounding box mask
            q_box = [qx + 5, y - 2, qx + 35, y + 22]
            mask_draw.rectangle(q_box, fill=255)
            metadata["tampered_fields"].append({
                "field": "item_qty",
                "original": "2",
                "forged": forged_qty,
                "bbox": q_box
            })
            
            # VÙNG GIẢ MẠO 2: Thành tiền món (90,000 -> 225,000)
            tx = 460
            draw.text((tx, y), f"{forged_tot:>11}", fill=ink_tamper, font=font_item)
            t_box = [tx + 10, y - 2, tx + 115, y + 22]
            mask_draw.rectangle(t_box, fill=255)
            metadata["tampered_fields"].append({
                "field": "item_total",
                "original": tot_str,
                "forged": forged_tot,
                "bbox": t_box
            })
        else:
            line = f"{name:<20} {qty_str:>3} {price_str:>9} {tot_str:>11}"
            draw.text((45, y), line, fill=ink_color, font=font_item)
            
        y += 24
        
    y += 6
    div_eq = "================================================"
    draw.text((45, y), div_eq, fill=ink_color, font=font_text)
    y += 26
    
    # 3. TỔNG KẾT TÀI CHÍNH
    subtotal_orig = 200000
    subtotal_forged = 335000
    
    grand_orig = 194400 # 200k - 20k voucher + 8% VAT (14.4k)
    grand_forged = 340200 # 335k - 20k voucher + 8% VAT (25.2k)
    
    if tampered:
        # Giả mạo cả dòng TỔNG THANH TOÁN
        draw.text((45, y), "Tổng tiền hàng:", fill=ink_color, font=font_text)
        draw.text((460, y), f"{subtotal_forged:>11,}", fill=ink_tamper, font=font_text)
        st_box = [460, y - 2, 575, y + 22]
        mask_draw.rectangle(st_box, fill=255)
        metadata["tampered_fields"].append({
            "field": "subtotal",
            "original": f"{subtotal_orig:,}",
            "forged": f"{subtotal_forged:,}",
            "bbox": st_box
        })
        y += 25
        
        draw.text((45, y), "Giảm giá Voucher:", fill=ink_color, font=font_text)
        draw.text((460, y), f"{'-20,000':>11}", fill=ink_color, font=font_text)
        y += 25
        
        draw.text((45, y), "Thuế VAT (8%):", fill=ink_color, font=font_text)
        draw.text((460, y), f"{'25,200':>11}", fill=ink_tamper, font=font_text)
        vat_box = [460, y - 2, 575, y + 22]
        mask_draw.rectangle(vat_box, fill=255)
        metadata["tampered_fields"].append({
            "field": "vat",
            "original": "14,400",
            "forged": "25,200",
            "bbox": vat_box
        })
        y += 28
        
        # GRAND TOTAL TO BỰ
        draw.text((45, y), "TỔNG CỘNG:", fill=ink_color, font=font_total)
        tot_str_f = f"{grand_forged:,} đ"
        draw.text((360, y), f"{tot_str_f:>13}", fill=ink_tamper, font=font_total)
        gt_box = [370, y - 4, 575, y + 30]
        mask_draw.rectangle(gt_box, fill=255)
        metadata["tampered_fields"].append({
            "field": "grand_total",
            "original": f"{grand_orig:,} đ",
            "forged": tot_str_f,
            "bbox": gt_box
        })
        y += 38
    else:
        draw.text((45, y), "Tổng tiền hàng:", fill=ink_color, font=font_text)
        draw.text((460, y), f"{subtotal_orig:>11,}", fill=ink_color, font=font_text)
        y += 25
        draw.text((45, y), "Giảm giá Voucher:", fill=ink_color, font=font_text)
        draw.text((460, y), f"{'-20,000':>11}", fill=ink_color, font=font_text)
        y += 25
        draw.text((45, y), "Thuế VAT (8%):", fill=ink_color, font=font_text)
        draw.text((460, y), f"{'14,400':>11}", fill=ink_color, font=font_text)
        y += 28
        
        draw.text((45, y), "TỔNG CỘNG:", fill=ink_color, font=font_total)
        draw.text((360, y), f"{grand_orig:>11,} đ", fill=ink_color, font=font_total)
        y += 38

    draw.text((45, y), div_line, fill=ink_color, font=font_text)
    y += 25
    
    # 4. FOOTER & BARCODE
    draw.text((45, y), "Phương thức: Thanh toán QR Napas", fill=ink_color, font=font_footer)
    y += 22
    draw.text((45, y), "Mã tra cứu e-Invoice: PL26119827104", fill=ink_color, font=font_footer)
    y += 32
    
    draw_barcode(draw, (width - 340) // 2, y, 340, 42, code_seed=seed)
    y += 50
    
    ft1 = "CẢM ƠN QUÝ KHÁCH VÀ HẸN GẶP LẠI!"
    draw.text(((width - font_bold.getbbox(ft1)[2]) // 2, y), ft1, fill=ink_color, font=font_bold)
    y += 22
    ft2 = "(Vui lòng kiểm tra lại hóa đơn trước khi rời quầy)"
    draw.text(((width - font_footer.getbbox(ft2)[2]) // 2, y), ft2, fill=ink_color, font=font_footer)
    
    return bg, mask, metadata


def render_supermarket_receipt(tampered=False, seed=200, template_name="WinMart_Supermarket_K80", store_title="WINMART+ CỬA HÀNG TIỆN ÍCH"):
    # Mẫu Siêu thị / WinMart+ (khổ rộng 80mm)
    width = 660
    height = 1040
    bg = create_thermal_background(width, height, add_streaks=True, seed=seed)
    mask = Image.new("L", (width, height), 0)
    
    font_title = ImageFont.truetype(FONT_SANS_BOLD, 28)
    font_sub = ImageFont.truetype(FONT_REGULAR_PATH, 16)
    font_bold = ImageFont.truetype(FONT_BOLD_PATH, 18)
    font_text = ImageFont.truetype(FONT_REGULAR_PATH, 17)
    font_item = ImageFont.truetype(FONT_REGULAR_PATH, 16)
    font_total = ImageFont.truetype(FONT_BOLD_PATH, 25)
    font_footer = ImageFont.truetype(FONT_REGULAR_PATH, 15)
    
    draw = ImageDraw.Draw(bg)
    mask_draw = ImageDraw.Draw(mask)
    ink_color = (20, 20, 20)
    ink_tamper = (24, 24, 24)
    
    metadata = {
        "template": template_name,
        "is_tampered": tampered,
        "width": width,
        "height": height,
        "tampered_fields": []
    }
    
    y = 35
    t1 = store_title
    draw.text(((width - font_title.getbbox(t1)[2]) // 2, y), t1, fill=ink_color, font=font_title)
    y += 36
    t2 = "Đ/C: Số 128 Nguyễn Trãi, Q. Thanh Xuân, Hà Nội"
    draw.text(((width - font_sub.getbbox(t2)[2]) // 2, y), t2, fill=ink_color, font=font_sub)
    y += 24
    t3 = "HÓA ĐƠN BÁN LẺ (GTGT)"
    draw.text(((width - font_bold.getbbox(t3)[2]) // 2, y), t3, fill=ink_color, font=font_bold)
    y += 30
    
    draw.text((45, y), "Số: WM-8829104", fill=ink_color, font=font_text)
    draw.text((380, y), "Quầy: POS-02", fill=ink_color, font=font_text)
    y += 24
    draw.text((45, y), "Ngày: 04/11/2026 10:15", fill=ink_color, font=font_text)
    draw.text((380, y), "TN: Trần Thị B", fill=ink_color, font=font_text)
    y += 28
    
    div_line = "----------------------------------------------------"
    draw.text((45, y), div_line, fill=ink_color, font=font_text)
    y += 22
    
    tbl_hdr = f"{'Tên hàng':<22} {'SL':>3} {'Đ.Giá':>10} {'T.Tiền':>11}"
    draw.text((45, y), tbl_hdr, fill=ink_color, font=font_bold)
    y += 24
    draw.text((45, y), div_line, fill=ink_color, font=font_text)
    y += 24
    
    items = [
        {"name": "Mì Hảo Hảo Tôm Cay", "qty": 5, "price": 4500, "total": 22500},
        {"name": "Sữa Tươi Vinamilk 1L", "qty": 2, "price": 36000, "total": 72000},
        {"name": "Trứng Gà Ba Huân (10)", "qty": 1, "price": 32000, "total": 32000},
        {"name": "Nước Tương Chinsu", "qty": 1, "price": 18000, "total": 18000},
        {"name": "Khăn Ướt Mamamy 80t", "qty": 2, "price": 25000, "total": 50000},
    ]
    
    # Sửa món Sữa Tươi Vinamilk 1L (giả mạo sửa đơn giá hoặc ngày giờ)
    for it in items:
        name = it["name"]
        qty_str = str(it["qty"])
        price_str = f"{it['price']:,}"
        tot_str = f"{it['total']:,}"
        
        if tampered and it["name"] == "Sữa Tươi Vinamilk 1L":
            forged_qty = "6"
            forged_tot = "216,000"
            draw.text((45, y), f"{name:<22}", fill=ink_color, font=font_item)
            draw.text((395, y), f"{price_str:>10}", fill=ink_color, font=font_item)
            
            # Tamper Qty
            draw.text((315, y), f"{forged_qty:>3}", fill=ink_tamper, font=font_item)
            q_box = [320, y - 2, 355, y + 22]
            mask_draw.rectangle(q_box, fill=255)
            metadata["tampered_fields"].append({
                "field": "item_qty", "original": "2", "forged": forged_qty, "bbox": q_box
            })
            
            # Tamper Total
            draw.text((505, y), f"{forged_tot:>11}", fill=ink_tamper, font=font_item)
            t_box = [510, y - 2, 615, y + 22]
            mask_draw.rectangle(t_box, fill=255)
            metadata["tampered_fields"].append({
                "field": "item_total", "original": tot_str, "forged": forged_tot, "bbox": t_box
            })
        else:
            line = f"{name:<22} {qty_str:>3} {price_str:>10} {tot_str:>11}"
            draw.text((45, y), line, fill=ink_color, font=font_item)
        y += 24
        
    y += 6
    draw.text((45, y), "====================================================", fill=ink_color, font=font_text)
    y += 26
    
    grand_orig = 194500
    grand_forged = 338500
    
    if tampered:
        draw.text((45, y), "Tổng tiền hàng (15 món):", fill=ink_color, font=font_text)
        draw.text((480, y), f"{grand_forged:>11,}", fill=ink_tamper, font=font_text)
        st_box = [480, y - 2, 615, y + 22]
        mask_draw.rectangle(st_box, fill=255)
        metadata["tampered_fields"].append({
            "field": "subtotal", "original": f"{grand_orig:,}", "forged": f"{grand_forged:,}", "bbox": st_box
        })
        y += 25
        
        draw.text((45, y), "Chiết khấu WinMember (5%):", fill=ink_color, font=font_text)
        draw.text((480, y), f"{'-16,925':>11}", fill=ink_tamper, font=font_text)
        y += 28
        
        draw.text((45, y), "TỔNG THANH TOÁN:", fill=ink_color, font=font_total)
        tot_f = f"{321575:,} đ"
        draw.text((370, y), f"{tot_f:>14}", fill=ink_tamper, font=font_total)
        gt_box = [380, y - 4, 615, y + 30]
        mask_draw.rectangle(gt_box, fill=255)
        metadata["tampered_fields"].append({
            "field": "grand_total", "original": f"{184775:,} đ", "forged": tot_f, "bbox": gt_box
        })
        y += 38
    else:
        draw.text((45, y), "Tổng tiền hàng (11 món):", fill=ink_color, font=font_text)
        draw.text((480, y), f"{grand_orig:>11,}", fill=ink_color, font=font_text)
        y += 25
        draw.text((45, y), "Chiết khấu WinMember (5%):", fill=ink_color, font=font_text)
        draw.text((480, y), f"{'-9,725':>11}", fill=ink_color, font=font_text)
        y += 28
        draw.text((45, y), "TỔNG THANH TOÁN:", fill=ink_color, font=font_total)
        draw.text((370, y), f"{184775:>12,} đ", fill=ink_color, font=font_total)
        y += 38

    draw.text((45, y), div_line, fill=ink_color, font=font_text)
    y += 25
    draw.text((45, y), "Hình thức: Thẻ Napas / Chip Contactless", fill=ink_color, font=font_footer)
    y += 22
    draw.text((45, y), "Điểm tích lũy Win: +184 điểm", fill=ink_color, font=font_footer)
    y += 32
    
    draw_barcode(draw, (width - 380) // 2, y, 380, 46, code_seed=seed)
    y += 54
    
    f1 = "XIN CẢM ƠN QUÝ KHÁCH!"
    draw.text(((width - font_bold.getbbox(f1)[2]) // 2, y), f1, fill=ink_color, font=font_bold)
    y += 22
    f2 = "Hóa đơn điện tử tra cứu tại: https://winmart.vn/einvoice"
    draw.text(((width - font_footer.getbbox(f2)[2]) // 2, y), f2, fill=ink_color, font=font_footer)
    
    return bg, mask, metadata


def main():
    print("=== ĐANG SINH BỘ TEMPLATE MẪU HÓA ĐƠN IN NHIỆT ===")
    
    # 1. Quán Cafe: Authentic, Tampered, Mask
    cafe_orig, _, meta_c_orig = render_cafe_receipt(tampered=False, seed=101)
    cafe_fake, cafe_mask, meta_c_fake = render_cafe_receipt(tampered=True, seed=101)
    
    cafe_orig.save(os.path.join(OUTPUT_DIR, "cafe_receipt_authentic.png"))
    cafe_fake.save(os.path.join(OUTPUT_DIR, "cafe_receipt_tampered.png"))
    cafe_mask.save(os.path.join(OUTPUT_DIR, "cafe_receipt_mask.png"))
    with open(os.path.join(OUTPUT_DIR, "cafe_receipt_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta_c_fake, f, ensure_ascii=False, indent=2)
    print("✅ Đã xuất mẫu 1: Quán Cafe/Trà sữa (Authentic, Tampered, Mask, Metadata)")

    # 2. Siêu thị WinMart: Authentic, Tampered, Mask
    mart_orig, _, meta_m_orig = render_supermarket_receipt(tampered=False, seed=202)
    mart_fake, mart_mask, meta_m_fake = render_supermarket_receipt(tampered=True, seed=202)
    
    mart_orig.save(os.path.join(OUTPUT_DIR, "supermarket_receipt_authentic.png"))
    mart_fake.save(os.path.join(OUTPUT_DIR, "supermarket_receipt_tampered.png"))
    mart_mask.save(os.path.join(OUTPUT_DIR, "supermarket_receipt_mask.png"))
    with open(os.path.join(OUTPUT_DIR, "supermarket_receipt_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta_m_fake, f, ensure_ascii=False, indent=2)
    print("✅ Đã xuất mẫu 2: Siêu thị WinMart (Authentic, Tampered, Mask, Metadata)")

    # 3. Tạo file HTML so sánh trực quan (Interactive Viewer)
    viewer_html = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>Thermal Receipt Forgery Templates Showcase</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }
  h1 { text-align: center; color: #38bdf8; margin-bottom: 8px; }
  .subtitle { text-align: center; color: #94a3b8; font-size: 14px; margin-bottom: 30px; }
  .showcase-grid { display: flex; flex-direction: column; gap: 40px; max-width: 1400px; margin: 0 auto; }
  .card { background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; }
  .card-title { font-size: 20px; font-weight: bold; color: #a3e635; margin-bottom: 16px; border-bottom: 1px solid #334155; padding-bottom: 8px; }
  .comparison-row { display: flex; gap: 20px; justify-content: space-around; flex-wrap: wrap; }
  .img-col { flex: 1; min-width: 300px; max-width: 420px; text-align: center; }
  .img-col h3 { font-size: 15px; margin-bottom: 10px; color: #cbd5e1; }
  .img-col img { width: 100%; height: auto; border-radius: 6px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); border: 1px solid #475569; }
  .badge-orig { background: #059669; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
  .badge-fake { background: #dc2626; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
  .badge-mask { background: #2563eb; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
  .meta-box { margin-top: 16px; background: #0f172a; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 13px; color: #38bdf8; text-align: left; }
</style>
</head>
<body>
  <h1>🧾 BỘ MẪU HÓA ĐƠN IN NHIỆT (THERMAL POS RECEIPTS)</h1>
  <div class="subtitle">Đặc thù in nhiệt: Nền giấy ngà xám, vệt xước kim đầu in nhiệt, font ma trận monospace, mép xé răng cưa, kèm Ground-Truth Mask chuẩn pixel</div>
  
  <div class="showcase-grid">
    <!-- MẪU 1: CAFE -->
    <div class="card">
      <div class="card-title">☕ Mẫu 1: Quán Cafe & Trà Sữa (Phúc Long / Highlands style)</div>
      <div class="comparison-row">
        <div class="img-col">
          <h3><span class="badge-orig">AUTHENTIC</span> Hóa đơn gốc</h3>
          <img src="cafe_receipt_authentic.png" alt="Cafe Authentic">
        </div>
        <div class="img-col">
          <h3><span class="badge-fake">TAMPERED</span> Đã can thiệp (SL 1->5, Tổng tiền)</h3>
          <img src="cafe_receipt_tampered.png" alt="Cafe Tampered">
        </div>
        <div class="img-col">
          <h3><span class="badge-mask">GROUND-TRUTH</span> Binary Pixel Mask</h3>
          <img src="cafe_receipt_mask.png" alt="Cafe Mask">
        </div>
      </div>
      <div class="meta-box">
        <b>Can thiệp:</b> Sửa số lượng món 'Cà Phê Sữa Đá' từ 2 lên 5; thành tiền món từ 90,000 lên 225,000; sửa Subtotal, Thuế VAT và Grand Total từ 194,400 đ lên 340,200 đ.
      </div>
    </div>

    <!-- MẪU 2: SIÊU THỊ -->
    <div class="card">
      <div class="card-title">🛒 Mẫu 2: Siêu thị / Cửa hàng Bán lẻ (WinMart+ style)</div>
      <div class="comparison-row">
        <div class="img-col">
          <h3><span class="badge-orig">AUTHENTIC</span> Hóa đơn gốc</h3>
          <img src="supermarket_receipt_authentic.png" alt="WinMart Authentic">
        </div>
        <div class="img-col">
          <h3><span class="badge-fake">TAMPERED</span> Đã can thiệp (SL Sữa Vinamilk, Grand Total)</h3>
          <img src="supermarket_receipt_tampered.png" alt="WinMart Tampered">
        </div>
        <div class="img-col">
          <h3><span class="badge-mask">GROUND-TRUTH</span> Binary Pixel Mask</h3>
          <img src="supermarket_receipt_mask.png" alt="WinMart Mask">
        </div>
      </div>
      <div class="meta-box">
        <b>Can thiệp:</b> Sửa số lượng Sữa Tươi Vinamilk từ 2 lên 6; thành tiền từ 72,000 lên 216,000; nâng tổng thanh toán lên 321,575 đ.
      </div>
    </div>
  </div>
</body>
</html>
"""
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(viewer_html)
    print("✅ Đã tạo file xem trực quan: output/index.html")
    print(f"\n🎉 Toàn bộ mẫu đã được lưu tại: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

