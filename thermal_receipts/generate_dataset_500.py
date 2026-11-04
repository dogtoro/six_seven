import os
import json
import random
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "dataset")
AUTHENTIC_DIR = os.path.join(DATASET_DIR, "authentic")
TAMPERED_DIR = os.path.join(DATASET_DIR, "tampered")
MASKS_DIR = os.path.join(DATASET_DIR, "masks")

os.makedirs(AUTHENTIC_DIR, exist_ok=True)
os.makedirs(TAMPERED_DIR, exist_ok=True)
os.makedirs(MASKS_DIR, exist_ok=True)

# Fonts
FONT_REGULAR_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ==============================================================================
# DATA POOLS
# ==============================================================================
FIRST_NAMES = ["An", "Bình", "Cường", "Dũng", "Giang", "Hải", "Hiếu", "Huy", "Linh", "Minh", "Nam", "Phong", "Quân", "Sơn", "Thắng", "Tùng", "Tuấn", "Vy", "Hương", "Trang", "Mai", "Phương", "Hà"]
LAST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
MIDDLE_NAMES = ["Văn", "Thị", "Đình", "Đức", "Quang", "Ngọc", "Hoàng", "Thảo", "Huy", "Minh", "Thanh"]

STREETS = [
    "Lê Thánh Tôn, Q.1, TP.HCM", "Nguyễn Trãi, Thanh Xuân, Hà Nội", "Cầu Giấy, Cầu Giấy, Hà Nội",
    "Hai Bà Trưng, Q.3, TP.HCM", "Nguyễn Huệ, Q.1, TP.HCM", "Trần Phú, Hà Đông, Hà Nội",
    "Hoàng Diệu, Hải Châu, Đà Nẵng", "Lê Lợi, Q.1, TP.HCM", "Xã Đàn, Đống Đa, Hà Nội",
    "Phan Xích Long, Phú Nhuận, TP.HCM", "Võ Văn Ngân, TP.Thủ Đức", "Điện Biên Phủ, Bình Thạnh, TP.HCM"
]

CAFE_BRANDS = [
    "PHÚC LONG COFFEE & TEA", "HIGHLANDS COFFEE", "THE COFFEE HOUSE",
    "TRÀ SỮA GONG CHA", "TRÀ SỮA KOI THÉ", "CÀ PHÊ TRUNG NGUYÊN", "CỘNG CÀ PHÊ"
]
CAFE_ITEMS = [
    ("Trà Đào Cam Sả", 55000, 65000), ("Trà Sen Vàng", 50000, 60000), ("Trà Vải Lài", 55000, 65000),
    ("Cà Phê Sữa Đá", 35000, 45000), ("Bạc Xỉu Đá", 35000, 45000), ("Cà Phê Đen Đá", 30000, 40000),
    ("Freeze Trà Xanh", 60000, 70000), ("Trà Sữa Oolong", 45000, 55000), ("Trà Sữa Trân Châu", 45000, 55000),
    ("Bánh Mì Chà Bông", 30000, 35000), ("Croissant Trứng Muối", 35000, 45000), ("Mousse Tiramisu", 40000, 48000),
    ("Trà Xanh Đậu Đỏ", 50000, 60000), ("Cà Phê Muối", 35000, 45000)
]

MART_BRANDS = [
    "WINMART+ CỬA HÀNG TIỆN ÍCH", "CO.OPMART SIÊU THỊ", "BÁCH HÓA XANH",
    "LOTTE MART VIỆT NAM", "AEON MALL MINI", "TOPS MARKET VIỆT NAM"
]
MART_ITEMS = [
    ("Mì Hảo Hảo Tôm Cay", 4500, 5000), ("Sữa Tươi Vinamilk 1L", 35000, 38000), ("Trứng Gà Ba Huân (10)", 31000, 34000),
    ("Nước Tương Chinsu", 17000, 20000), ("Dầu Ăn Simply 1L", 58000, 65000), ("Gạo ST25 (5kg)", 175000, 190000),
    ("Nước Mắm Nam Ngư", 36000, 42000), ("Khăn Ướt Mamamy 80t", 24000, 28000), ("Nước Giặt OMO Matic", 165000, 185000),
    ("Xúc Xích Tiệt Trùng CP", 22000, 26000), ("Cá Hộp Ba Cô Gái", 21000, 25000), ("Bột Giặt Tide 2.5kg", 110000, 125000),
    ("Bánh Quy Cosy Mè", 18000, 22000), ("Bơ Tường An 200g", 23000, 27000), ("Đường Trắng Biên Hòa", 26000, 30000)
]

CONVENIENCE_BRANDS = [
    "CIRCLE K VIỆT NAM", "FAMILYMART", "7-ELEVEN VIỆT NAM",
    "GS25 TIỆN LỢI", "MINISTOP VIỆT NAM"
]
CONVENIENCE_ITEMS = [
    ("Bánh Mì Que Cay", 14000, 16000), ("Mì Trộn Trứng Xúc Xích", 28000, 35000), ("Lẩu Ly Thập Cẩm", 30000, 38000),
    ("Bao Tử Cá Cay", 25000, 32000), ("Sandwich Gà Nướng", 22000, 28000), ("Trà Sữa Thái Xanh", 20000, 25000),
    ("Cà Phê Sữa Tươi", 20000, 26000), ("Nước Tăng Lực RedBull", 14000, 16000), ("Snack Khoai Tây Lay's", 16000, 20000),
    ("Kẹo Cao Su Doublemint", 8000, 10000), ("Kem Cornetto Socola", 18000, 22000), ("Nước Suối Aquafina", 6000, 8000),
    ("Cơm Nắm Onigiri Cá Hồi", 16000, 20000), ("Bánh Bao Trứng Muối", 16000, 20000)
]

CUSTOM_BRANDS = [
    ("NHÀ THUỐC FPT LONG CHÂU", "pharmacy", [
        ("Panadol Extra Đỏ (Vỉ)", 18000, 22000), ("Vitamin C Berocca Sủi", 75000, 85000),
        ("Khẩu Trang 4D KF94", 25000, 32000), ("Nước Muối Sinh Lý 500ml", 8000, 12000),
        ("Men Tiêu Hóa Enterogermina", 120000, 135000), ("Oresol Cam Bù Nước", 6000, 8000),
        ("Băng Cá Nhân Urgo", 15000, 20000), ("Dầu Gió Xanh Thiên Thảo", 28000, 35000)
    ]),
    ("QUÁN CƠM TẤM PHÚC LỘC THỌ", "food_restaurant", [
        ("Cơm Tấm Sườn Nướng", 46000, 52000), ("Cơm Tấm Sườn Bì Chả", 56000, 65000),
        ("Canh Khổ Qua Nhồi Thịt", 18000, 24000), ("Canh Rong Biển Thịt Bằm", 16000, 20000),
        ("Chả Chưng Thêm", 12000, 15000), ("Trứng Ốp La", 8000, 10000),
        ("Trà Đá Đường", 5000, 8000), ("Khăn Lạnh Cao Cấp", 3000, 5000)
    ]),
    ("NHÀ SÁCH TIỀN PHONG", "bookstore", [
        ("Bút Bi Thiên Long 0.5", 5000, 6000), ("Sổ Tay Bìa Da A5", 45000, 55000),
        ("Giấy Double A A4 70gsm", 78000, 88000), ("Bút Dạ Quang Highlight", 12000, 15000),
        ("Thước Kẻ Kim Loại 20cm", 10000, 14000), ("Băng Dính Trong 5cm", 18000, 22000),
        ("Kẹp Bấm Giấy Deli", 15000, 20000), ("Bút Chì 2B Staedtler", 8000, 11000)
    ])
]


def gen_person_name(rng):
    l = rng.choice(LAST_NAMES)
    m = rng.choice(MIDDLE_NAMES)
    f = rng.choice(FIRST_NAMES)
    return f"{l} {m} {f}"


def create_thermal_background(width, height, add_streaks=True, seed=42):
    rng = random.Random(seed)
    base_color = (248, 248, 246)
    im = Image.new("RGBA", (width, height), base_color)
    
    # 1. Micro noise
    noise = Image.new("L", (width, height), 0)
    noise_pixels = noise.load()
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            val = rng.randint(0, 14)
            noise_pixels[x, y] = val
            if x + 1 < width: noise_pixels[x + 1, y] = val
            if y + 1 < height: noise_pixels[x, y] = val
            if x + 1 < width and y + 1 < height: noise_pixels[x + 1, y + 1] = val
    noise = noise.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    im_noise = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    im_noise.paste((0, 0, 0, 8), mask=noise)
    im = Image.alpha_composite(im, im_noise)
    
    # 2. Thermal head streak lines
    if add_streaks:
        streak_draw = ImageDraw.Draw(im)
        for _ in range(rng.randint(2, 4)):
            sx = rng.randint(40, width - 40)
            sw = rng.choice([1, 2])
            opacity = rng.randint(15, 30)
            streak_draw.line([(sx, 0), (sx, height)], fill=(255, 255, 255, opacity), width=sw)

    # 3. Zigzag cut at top and bottom
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


def draw_barcode(draw, x, y, width, height, rng):
    cur_x = x
    while cur_x < x + width - 15:
        bar_w = rng.choice([1, 2, 3, 4])
        space_w = rng.choice([2, 3, 4])
        draw.rectangle([cur_x, y, cur_x + bar_w, y + height], fill=(30, 30, 30))
        cur_x += bar_w + space_w


def generate_single_receipt(template_type, sample_index, seed=1000):
    rng = random.Random(seed)
    
    # Font loaders
    font_title = ImageFont.truetype(FONT_SANS_BOLD, 25)
    font_sub = ImageFont.truetype(FONT_REGULAR_PATH, 15)
    font_bold = ImageFont.truetype(FONT_BOLD_PATH, 17)
    font_text = ImageFont.truetype(FONT_REGULAR_PATH, 16)
    font_item = ImageFont.truetype(FONT_REGULAR_PATH, 15)
    font_total = ImageFont.truetype(FONT_BOLD_PATH, 23)
    font_footer = ImageFont.truetype(FONT_REGULAR_PATH, 14)
    
    # Select brand & items according to template_type
    if template_type == "cafe":
        template_id = "cafe_fnb"
        brand_name = rng.choice(CAFE_BRANDS)
        item_pool = CAFE_ITEMS
        num_items = rng.randint(3, 5)
        width, height = 620, 960
        table_label = f"Bàn: T{rng.randint(1, 15):02d} ({rng.choice(['Mang đi', 'Tại quán'])})"
    elif template_type == "supermarket":
        template_id = "supermarket_retail"
        brand_name = rng.choice(MART_BRANDS)
        item_pool = MART_ITEMS
        num_items = rng.randint(4, 7)
        width, height = 660, 1020 + (num_items - 4) * 24
        table_label = f"Quầy: POS-{rng.randint(1, 8):02d}"
    elif template_type == "convenience":
        template_id = "convenience_store"
        brand_name = rng.choice(CONVENIENCE_BRANDS)
        item_pool = CONVENIENCE_ITEMS
        num_items = rng.randint(3, 5)
        width, height = 600, 940
        table_label = f"Quầy: 01 ({rng.choice(['Take-away', 'Tại quầy'])})"
    else: # custom
        custom_choice = rng.choice(CUSTOM_BRANDS)
        brand_name = custom_choice[0]
        template_id = f"custom_{custom_choice[1]}"
        item_pool = custom_choice[2]
        num_items = rng.randint(3, 5)
        width, height = 630, 960
        table_label = f"Số phiếu: P-{rng.randint(10, 99)}"

    # Generate item rows
    selected_raw = rng.sample(item_pool, num_items)
    items_data = []
    for raw in selected_raw:
        qty = rng.randint(1, 4)
        price = rng.choice([raw[1], raw[2]])
        items_data.append({
            "name": raw[0],
            "qty": qty,
            "price": price,
            "total": qty * price
        })
        
    address = f"Số {rng.randint(10, 250)} {rng.choice(STREETS)}"
    hotline = f"1900 {rng.randint(1000, 9999)}"
    wifi = f"Pass: {rng.randint(10000000, 99999999)}"
    receipt_code = f"HD-2026{rng.randint(1, 12):02d}{rng.randint(1, 28):02d}-{sample_index:04d}"
    
    hour = rng.randint(7, 22)
    minute = rng.randint(0, 59)
    date_str = f"{rng.randint(1, 28):02d}/{rng.randint(1, 12):02d}/2026 {hour:02d}:{minute:02d}"
    cashier_name = gen_person_name(rng)
    
    subtotal = sum(it["total"] for it in items_data)
    has_discount = rng.random() < 0.6
    discount_val = rng.choice([10000, 15000, 20000, 30000]) if has_discount else 0
    vat_percent = rng.choice([8, 10])
    taxable = max(0, subtotal - discount_val)
    vat_val = int(taxable * (vat_percent / 100))
    grand_total = taxable + vat_val

    # ==========================================================================
    # 1. RENDER AUTHENTIC IMAGE
    # ==========================================================================
    bg_auth = create_thermal_background(width, height, add_streaks=True, seed=seed)
    draw_a = ImageDraw.Draw(bg_auth)
    ink_color = (22, 22, 22)
    
    # Header
    y = 35
    tb = font_title.getbbox(brand_name)
    draw_a.text(((width - (tb[2] - tb[0])) // 2, y), brand_name, fill=ink_color, font=font_title)
    y += 34
    
    draw_a.text(((width - font_sub.getbbox(address)[2]) // 2, y), address, fill=ink_color, font=font_sub)
    y += 22
    info_str = f"Hotline: {hotline} - Wifi: {wifi}"
    draw_a.text(((width - font_sub.getbbox(info_str)[2]) // 2, y), info_str, fill=ink_color, font=font_sub)
    y += 28
    
    hdr_line = "=== HÓA ĐƠN BÁN HÀNG ==="
    draw_a.text(((width - font_bold.getbbox(hdr_line)[2]) // 2, y), hdr_line, fill=ink_color, font=font_bold)
    y += 28
    
    draw_a.text((40, y), f"Số: {receipt_code}", fill=ink_color, font=font_text)
    draw_a.text((width - 40 - font_text.getbbox(table_label)[2], y), table_label, fill=ink_color, font=font_text)
    y += 22
    draw_a.text((40, y), f"Ngày: {date_str}", fill=ink_color, font=font_text)
    c_str = f"TN: {cashier_name}"
    draw_a.text((width - 40 - font_text.getbbox(c_str)[2], y), c_str, fill=ink_color, font=font_text)
    y += 26
    
    div = "-" * int((width - 80) / 10.5)
    draw_a.text((40, y), div, fill=ink_color, font=font_text)
    y += 20
    
    # Table header
    draw_a.text((40, y), "Tên hàng", fill=ink_color, font=font_bold)
    draw_a.text((width // 2, y), "SL", fill=ink_color, font=font_bold)
    draw_a.text((width - 170, y), "Đ.Giá", fill=ink_color, font=font_bold)
    draw_a.text((width - 80, y), "T.Tiền", fill=ink_color, font=font_bold)
    y += 22
    draw_a.text((40, y), div, fill=ink_color, font=font_text)
    y += 22
    
    # Rows
    for it in items_data:
        draw_a.text((40, y), it["name"][:20], fill=ink_color, font=font_item)
        draw_a.text((width // 2 + 5, y), str(it["qty"]), fill=ink_color, font=font_item)
        p_str = f"{it['price']:,}"
        draw_a.text((width - 130 - font_item.getbbox(p_str)[2], y), p_str, fill=ink_color, font=font_item)
        tot_str = f"{it['total']:,}"
        draw_a.text((width - 40 - font_item.getbbox(tot_str)[2], y), tot_str, fill=ink_color, font=font_item)
        y += 24
        
    y += 6
    eq_div = "=" * int((width - 80) / 10.5)
    draw_a.text((40, y), eq_div, fill=ink_color, font=font_text)
    y += 24
    
    # Summary
    draw_a.text((40, y), "Tổng tiền hàng:", fill=ink_color, font=font_text)
    st_str = f"{subtotal:,} đ"
    draw_a.text((width - 40 - font_text.getbbox(st_str)[2], y), st_str, fill=ink_color, font=font_text)
    y += 24
    
    if has_discount:
        draw_a.text((40, y), "Chiết khấu / Giảm giá:", fill=ink_color, font=font_text)
        dc_str = f"-{discount_val:,} đ"
        draw_a.text((width - 40 - font_text.getbbox(dc_str)[2], y), dc_str, fill=ink_color, font=font_text)
        y += 24
        
    draw_a.text((40, y), f"Thuế VAT ({vat_percent}%):", fill=ink_color, font=font_text)
    vat_str = f"{vat_val:,} đ"
    draw_a.text((width - 40 - font_text.getbbox(vat_str)[2], y), vat_str, fill=ink_color, font=font_text)
    y += 28
    
    # Grand Total
    draw_a.text((40, y), "TỔNG CỘNG:", fill=ink_color, font=font_total)
    gt_str = f"{grand_total:,} đ"
    draw_a.text((width - 40 - font_total.getbbox(gt_str)[2], y), gt_str, fill=ink_color, font=font_total)
    y += 34
    
    draw_a.text((40, y), div, fill=ink_color, font=font_text)
    y += 22
    
    draw_a.text((40, y), "Phương thức: Tiền mặt / Thẻ ngân hàng / QR", fill=ink_color, font=font_footer)
    y += 20
    draw_a.text((40, y), f"Mã tra cứu: HD{rng.randint(10000000, 99999999)}", fill=ink_color, font=font_footer)
    y += 28
    
    draw_barcode(draw_a, (width - 340) // 2, y, 340, 42, rng)
    y += 52
    
    f1 = "CẢM ƠN QUÝ KHÁCH - HẸN GẶP LẠI!"
    draw_a.text(((width - font_bold.getbbox(f1)[2]) // 2, y), f1, fill=ink_color, font=font_bold)
    y += 20
    f2 = "(Vui lòng kiểm tra lại hóa đơn trước khi rời quầy)"
    draw_a.text(((width - font_footer.getbbox(f2)[2]) // 2, y), f2, fill=ink_color, font=font_footer)

    # ==========================================================================
    # 2. RENDER TAMPERED IMAGE & PIXEL-PERFECT MASK
    # ==========================================================================
    bg_tamper = create_thermal_background(width, height, add_streaks=True, seed=seed)
    mask = Image.new("L", (width, height), 0)
    draw_t = ImageDraw.Draw(bg_tamper)
    mask_draw = ImageDraw.Draw(mask)
    
    # Choose tampering modality
    # 0: quantity & item total
    # 1: grand total only
    # 2: quantity, item total & grand total
    tamper_type = rng.choice(["qty_and_total", "grand_total_only", "full_financial"])
    
    tampered_fields = []
    
    # Redo header on tampered
    y = 35
    draw_t.text(((width - (tb[2] - tb[0])) // 2, y), brand_name, fill=ink_color, font=font_title)
    y += 34
    draw_t.text(((width - font_sub.getbbox(address)[2]) // 2, y), address, fill=ink_color, font=font_sub)
    y += 22
    draw_t.text(((width - font_sub.getbbox(info_str)[2]) // 2, y), info_str, fill=ink_color, font=font_sub)
    y += 28
    draw_t.text(((width - font_bold.getbbox(hdr_line)[2]) // 2, y), hdr_line, fill=ink_color, font=font_bold)
    y += 28
    draw_t.text((40, y), f"Số: {receipt_code}", fill=ink_color, font=font_text)
    draw_t.text((width - 40 - font_text.getbbox(table_label)[2], y), table_label, fill=ink_color, font=font_text)
    y += 22
    draw_t.text((40, y), f"Ngày: {date_str}", fill=ink_color, font=font_text)
    draw_t.text((width - 40 - font_text.getbbox(c_str)[2], y), c_str, fill=ink_color, font=font_text)
    y += 26
    draw_t.text((40, y), div, fill=ink_color, font=font_text)
    y += 20
    
    draw_t.text((40, y), "Tên hàng", fill=ink_color, font=font_bold)
    draw_t.text((width // 2, y), "SL", fill=ink_color, font=font_bold)
    draw_t.text((width - 170, y), "Đ.Giá", fill=ink_color, font=font_bold)
    draw_t.text((width - 80, y), "T.Tiền", fill=ink_color, font=font_bold)
    y += 22
    draw_t.text((40, y), div, fill=ink_color, font=font_text)
    y += 22
    
    # Rows with tampering on chosen item
    tamper_item_idx = rng.randint(0, len(items_data) - 1)
    new_subtotal = subtotal
    
    for i, it in enumerate(items_data):
        draw_t.text((40, y), it["name"][:20], fill=ink_color, font=font_item)
        
        if (tamper_type in ["qty_and_total", "full_financial"]) and i == tamper_item_idx:
            orig_qty = it["qty"]
            forged_qty = orig_qty + rng.choice([2, 3, 4])
            forged_tot = forged_qty * it["price"]
            new_subtotal += (forged_tot - it["total"])
            
            # Draw forged QTY
            draw_t.text((width // 2 + 5, y), str(forged_qty), fill=(26, 26, 26), font=font_item)
            q_box = [width // 2 - 2, y - 2, width // 2 + 25, y + 20]
            mask_draw.rectangle(q_box, fill=255)
            tampered_fields.append({
                "field": f"item_{i}_qty",
                "original": str(orig_qty),
                "forged": str(forged_qty),
                "bbox": q_box
            })
            
            # Price normal
            p_str = f"{it['price']:,}"
            draw_t.text((width - 130 - font_item.getbbox(p_str)[2], y), p_str, fill=ink_color, font=font_item)
            
            # Draw forged ITEM TOTAL
            f_tot_str = f"{forged_tot:,}"
            tot_x = width - 40 - font_item.getbbox(f_tot_str)[2]
            draw_t.text((tot_x, y), f_tot_str, fill=(26, 26, 26), font=font_item)
            t_box = [tot_x - 3, y - 2, width - 36, y + 20]
            mask_draw.rectangle(t_box, fill=255)
            tampered_fields.append({
                "field": f"item_{i}_total",
                "original": f"{it['total']:,}",
                "forged": f_tot_str,
                "bbox": t_box
            })
        else:
            draw_t.text((width // 2 + 5, y), str(it["qty"]), fill=ink_color, font=font_item)
            p_str = f"{it['price']:,}"
            draw_t.text((width - 130 - font_item.getbbox(p_str)[2], y), p_str, fill=ink_color, font=font_item)
            tot_str = f"{it['total']:,}"
            draw_t.text((width - 40 - font_item.getbbox(tot_str)[2], y), tot_str, fill=ink_color, font=font_item)
            
        y += 24

    y += 6
    draw_t.text((40, y), eq_div, fill=ink_color, font=font_text)
    y += 24
    
    # Financial tampering
    if tamper_type == "full_financial":
        # Recalculate forged grand total
        f_taxable = max(0, new_subtotal - discount_val)
        f_vat = int(f_taxable * (vat_percent / 100))
        f_grand = f_taxable + f_vat
        
        # Subtotal
        f_st_str = f"{new_subtotal:,} đ"
        draw_t.text((40, y), "Tổng tiền hàng:", fill=ink_color, font=font_text)
        st_x = width - 40 - font_text.getbbox(f_st_str)[2]
        draw_t.text((st_x, y), f_st_str, fill=(26, 26, 26), font=font_text)
        st_box = [st_x - 3, y - 2, width - 36, y + 20]
        mask_draw.rectangle(st_box, fill=255)
        tampered_fields.append({"field": "subtotal", "original": st_str, "forged": f_st_str, "bbox": st_box})
        y += 24
        
        if has_discount:
            draw_t.text((40, y), "Chiết khấu / Giảm giá:", fill=ink_color, font=font_text)
            draw_t.text((width - 40 - font_text.getbbox(dc_str)[2], y), dc_str, fill=ink_color, font=font_text)
            y += 24
            
        # VAT
        f_vat_str = f"{f_vat:,} đ"
        draw_t.text((40, y), f"Thuế VAT ({vat_percent}%):", fill=ink_color, font=font_text)
        vat_x = width - 40 - font_text.getbbox(f_vat_str)[2]
        draw_t.text((vat_x, y), f_vat_str, fill=(26, 26, 26), font=font_text)
        vat_box = [vat_x - 3, y - 2, width - 36, y + 20]
        mask_draw.rectangle(vat_box, fill=255)
        tampered_fields.append({"field": "vat", "original": vat_str, "forged": f_vat_str, "bbox": vat_box})
        y += 28
        
        # Grand Total
        f_gt_str = f"{f_grand:,} đ"
        draw_t.text((40, y), "TỔNG CỘNG:", fill=ink_color, font=font_total)
        gt_x = width - 40 - font_total.getbbox(f_gt_str)[2]
        draw_t.text((gt_x, y), f_gt_str, fill=(28, 28, 28), font=font_total)
        gt_box = [gt_x - 4, y - 3, width - 36, y + 26]
        mask_draw.rectangle(gt_box, fill=255)
        tampered_fields.append({"field": "grand_total", "original": gt_str, "forged": f_gt_str, "bbox": gt_box})
        y += 34
    elif tamper_type == "grand_total_only":
        # Keep items same, arbitrarily tamper grand total (e.g. padding an extra 100k or 200k)
        draw_t.text((40, y), "Tổng tiền hàng:", fill=ink_color, font=font_text)
        draw_t.text((width - 40 - font_text.getbbox(st_str)[2], y), st_str, fill=ink_color, font=font_text)
        y += 24
        if has_discount:
            draw_t.text((40, y), "Chiết khấu / Giảm giá:", fill=ink_color, font=font_text)
            draw_t.text((width - 40 - font_text.getbbox(dc_str)[2], y), dc_str, fill=ink_color, font=font_text)
            y += 24
        draw_t.text((40, y), f"Thuế VAT ({vat_percent}%):", fill=ink_color, font=font_text)
        draw_t.text((width - 40 - font_text.getbbox(vat_str)[2], y), vat_str, fill=ink_color, font=font_text)
        y += 28
        
        f_grand = grand_total + rng.choice([100000, 200000, 300000])
        f_gt_str = f"{f_grand:,} đ"
        draw_t.text((40, y), "TỔNG CỘNG:", fill=ink_color, font=font_total)
        gt_x = width - 40 - font_total.getbbox(f_gt_str)[2]
        draw_t.text((gt_x, y), f_gt_str, fill=(28, 28, 28), font=font_total)
        gt_box = [gt_x - 4, y - 3, width - 36, y + 26]
        mask_draw.rectangle(gt_box, fill=255)
        tampered_fields.append({"field": "grand_total", "original": gt_str, "forged": f_gt_str, "bbox": gt_box})
        y += 34
    else: # qty_and_total only, subtotal/grand remain untouched or slightly mismatched
        draw_t.text((40, y), "Tổng tiền hàng:", fill=ink_color, font=font_text)
        draw_t.text((width - 40 - font_text.getbbox(st_str)[2], y), st_str, fill=ink_color, font=font_text)
        y += 24
        if has_discount:
            draw_t.text((40, y), "Chiết khấu / Giảm giá:", fill=ink_color, font=font_text)
            draw_t.text((width - 40 - font_text.getbbox(dc_str)[2], y), dc_str, fill=ink_color, font=font_text)
            y += 24
        draw_t.text((40, y), f"Thuế VAT ({vat_percent}%):", fill=ink_color, font=font_text)
        draw_t.text((width - 40 - font_text.getbbox(vat_str)[2], y), vat_str, fill=ink_color, font=font_text)
        y += 28
        draw_t.text((40, y), "TỔNG CỘNG:", fill=ink_color, font=font_total)
        draw_t.text((width - 40 - font_total.getbbox(gt_str)[2], y), gt_str, fill=ink_color, font=font_total)
        y += 34

    draw_t.text((40, y), div, fill=ink_color, font=font_text)
    y += 22
    draw_t.text((40, y), "Phương thức: Tiền mặt / Thẻ ngân hàng / QR", fill=ink_color, font=font_footer)
    y += 20
    draw_t.text((40, y), f"Mã tra cứu: HD{rng.randint(10000000, 99999999)}", fill=ink_color, font=font_footer)
    y += 28
    draw_barcode(draw_t, (width - 340) // 2, y, 340, 42, rng)
    y += 52
    draw_t.text(((width - font_bold.getbbox(f1)[2]) // 2, y), f1, fill=ink_color, font=font_bold)
    y += 20
    draw_t.text(((width - font_footer.getbbox(f2)[2]) // 2, y), f2, fill=ink_color, font=font_footer)

    meta = {
        "sample_id": f"receipt_{sample_index:04d}",
        "template": template_type,
        "template_id": template_id,
        "brand_name": brand_name,
        "receipt_code": receipt_code,
        "date": date_str,
        "width": width,
        "height": height,
        "tampering_type": tamper_type,
        "tampered_fields": tampered_fields
    }

    return bg_auth, bg_tamper, mask, meta


def main():
    print("=" * 65)
    print("🚀 BẮT ĐẦU SINH TẬP DỮ LIỆU HÓA ĐƠN IN NHIỆT (500 MẪU)")
    print("4 Template: Cafe (125), Siêu thị (125), Cửa hàng tiện lợi (125), Custom (125)")
    print(f"Lưu tại: {DATASET_DIR}")
    print("=" * 65)
    
    start_time = time.time()
    manifest_records = []
    
    templates = [
        ("cafe", 125),
        ("supermarket", 125),
        ("convenience", 125),
        ("custom", 125)
    ]
    
    current_idx = 1
    for t_name, count in templates:
        print(f"\n📂 Đang sinh template [{t_name.upper()}] ({count} mẫu)...")
        for i in range(count):
            seed = 10000 + current_idx * 17
            auth_im, fake_im, mask_im, meta = generate_single_receipt(t_name, current_idx, seed=seed)
            
            sample_id = f"receipt_{current_idx:04d}"
            
            # Save files
            auth_path = os.path.join(AUTHENTIC_DIR, f"{sample_id}_authentic.png")
            fake_path = os.path.join(TAMPERED_DIR, f"{sample_id}_tampered.png")
            mask_path = os.path.join(MASKS_DIR, f"{sample_id}_mask.png")
            
            auth_im.save(auth_path, optimize=True)
            fake_im.save(fake_path, optimize=True)
            mask_im.save(mask_path, optimize=True)
            
            meta["authentic_file"] = f"authentic/{sample_id}_authentic.png"
            meta["tampered_file"] = f"tampered/{sample_id}_tampered.png"
            meta["mask_file"] = f"masks/{sample_id}_mask.png"
            manifest_records.append(meta)
            
            if (i + 1) % 25 == 0 or (i + 1) == count:
                print(f"  -> [{t_name}] Đã xong {i+1}/{count} mẫu (Sample ID: {sample_id})")
                
            current_idx += 1
            
    # Write metadata JSON Lines & JSON
    manifest_jsonl = os.path.join(DATASET_DIR, "manifest.jsonl")
    manifest_json = os.path.join(DATASET_DIR, "metadata.json")
    
    with open(manifest_jsonl, "w", encoding="utf-8") as f:
        for r in manifest_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(manifest_records, f, ensure_ascii=False, indent=2)
        
    duration = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"🎉 HOÀN THÀNH XUẤT 500 MẪU DATASET TRONG {duration:.2f} GIÂY!")
    print(f"📁 Authentic Images: {len(os.listdir(AUTHENTIC_DIR))} file ({AUTHENTIC_DIR})")
    print(f"📁 Tampered Images:  {len(os.listdir(TAMPERED_DIR))} file ({TAMPERED_DIR})")
    print(f"📁 Ground-Truth Masks: {len(os.listdir(MASKS_DIR))} file ({MASKS_DIR})")
    print(f"📋 Manifest JSON:    {manifest_json}")
    print("=" * 65)


if __name__ == "__main__":
    main()

