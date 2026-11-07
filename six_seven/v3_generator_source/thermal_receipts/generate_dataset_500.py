import argparse
import os
import json
import random
import time
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "dataset")
AUTHENTIC_DIR = os.path.join(DATASET_DIR, "authentic")
TAMPERED_DIR = os.path.join(DATASET_DIR, "tampered")
MASKS_DIR = os.path.join(DATASET_DIR, "masks")
DEFAULT_FONT_DIR = os.path.join(SCRIPT_DIR, "fonts")


def resolve_font_paths(font_dir=None):
    """Resolve DejaVu TrueType font paths portably across Linux and Windows."""
    candidates = []
    if font_dir:
        candidates.append(font_dir)
    if os.environ.get("THERMAL_FONT_DIR"):
        candidates.append(os.environ["THERMAL_FONT_DIR"])
    candidates.append(DEFAULT_FONT_DIR)
    candidates.append("/usr/share/fonts/truetype/dejavu")

    required = ("DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf", "DejaVuSans-Bold.ttf")
    for cand in candidates:
        if all(os.path.isfile(os.path.join(cand, fn)) for fn in required):
            return (
                os.path.join(cand, "DejaVuSansMono.ttf"),
                os.path.join(cand, "DejaVuSansMono-Bold.ttf"),
                os.path.join(cand, "DejaVuSans-Bold.ttf"),
            )
    raise FileNotFoundError(
        f"Could not find required DejaVu fonts {required}. "
        f"Pass --font-dir or ensure bundled fonts exist in {DEFAULT_FONT_DIR}."
    )


def check_arith_consistent(items, subtotal, discount, vat_percent, vat, grand_total):
    """Check whether printed receipt line items and summary numbers add up."""
    if any(it["qty"] * it["price"] != it["total"] for it in items):
        return False
    if sum(it["total"] for it in items) != subtotal:
        return False
    taxable = max(0, subtotal - discount)
    if int(taxable * (vat_percent / 100)) != vat:
        return False
    if taxable + vat != grand_total:
        return False
    return True


# Default font paths (overridable via --font-dir)
FONT_REGULAR_PATH, FONT_BOLD_PATH, FONT_SANS_BOLD = resolve_font_paths()

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
            if y + 1 < height: noise_pixels[x, y + 1] = val
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


def draw_barcode(draw, x, y, width, height, barcode_seed):
    rng = random.Random(barcode_seed)
    cur_x = x
    while cur_x < x + width - 15:
        bar_w = rng.choice([1, 2, 3, 4])
        space_w = rng.choice([2, 3, 4])
        draw.rectangle([cur_x, y, cur_x + bar_w, y + height], fill=(30, 30, 30))
        cur_x += bar_w + space_w


def generate_single_receipt_v2(template_type, sample_index, seed=1000, font_dir=None):
    rng_content = random.Random(seed)
    rng_tamper = random.Random(seed + 7777777)

    if font_dir:
        reg_path, bold_path, sans_bold_path = resolve_font_paths(font_dir)
    else:
        reg_path, bold_path, sans_bold_path = FONT_REGULAR_PATH, FONT_BOLD_PATH, FONT_SANS_BOLD
    
    # Font loaders
    font_title = ImageFont.truetype(sans_bold_path, 25)
    font_sub = ImageFont.truetype(reg_path, 15)
    font_bold = ImageFont.truetype(bold_path, 17)
    font_text = ImageFont.truetype(reg_path, 16)
    font_item = ImageFont.truetype(reg_path, 15)
    font_total = ImageFont.truetype(bold_path, 23)
    font_footer = ImageFont.truetype(reg_path, 14)
    
    # Select brand & items according to template_type
    if template_type == "cafe":
        template_id = "cafe_fnb"
        brand_name = rng_content.choice(CAFE_BRANDS)
        item_pool = CAFE_ITEMS
        num_items = rng_content.randint(3, 5)
        width, height = 620, 960
        table_label = f"Bàn: T{rng_content.randint(1, 15):02d} ({rng_content.choice(['Mang đi', 'Tại quán'])})"
    elif template_type == "supermarket":
        template_id = "supermarket_retail"
        brand_name = rng_content.choice(MART_BRANDS)
        item_pool = MART_ITEMS
        num_items = rng_content.randint(4, 7)
        width, height = 660, 1020 + (num_items - 4) * 24
        table_label = f"Quầy: POS-{rng_content.randint(1, 8):02d}"
    elif template_type == "convenience":
        template_id = "convenience_store"
        brand_name = rng_content.choice(CONVENIENCE_BRANDS)
        item_pool = CONVENIENCE_ITEMS
        num_items = rng_content.randint(3, 5)
        width, height = 600, 940
        table_label = f"Quầy: 01 ({rng_content.choice(['Take-away', 'Tại quầy'])})"
    else:  # custom
        custom_choice = rng_content.choice(CUSTOM_BRANDS)
        brand_name = custom_choice[0]
        template_id = f"custom_{custom_choice[1]}"
        item_pool = custom_choice[2]
        num_items = rng_content.randint(3, 5)
        width, height = 630, 960
        table_label = f"Số phiếu: P-{rng_content.randint(10, 99)}"

    # Generate item rows
    selected_raw = rng_content.sample(item_pool, num_items)
    items_data = []
    for raw in selected_raw:
        qty = rng_content.randint(1, 4)
        price = rng_content.choice([raw[1], raw[2]])
        items_data.append({
            "name": raw[0],
            "qty": qty,
            "price": price,
            "total": qty * price
        })
        
    address = f"Số {rng_content.randint(10, 250)} {rng_content.choice(STREETS)}"
    hotline = f"1900 {rng_content.randint(1000, 9999)}"
    wifi = f"Pass: {rng_content.randint(10000000, 99999999)}"
    receipt_code = f"HD-2026{rng_content.randint(1, 12):02d}{rng_content.randint(1, 28):02d}-{sample_index:04d}"
    
    hour = rng_content.randint(7, 22)
    minute = rng_content.randint(0, 59)
    date_str = f"{rng_content.randint(1, 28):02d}/{rng_content.randint(1, 12):02d}/2026 {hour:02d}:{minute:02d}"
    cashier_name = gen_person_name(rng_content)
    
    subtotal = sum(it["total"] for it in items_data)
    has_discount = rng_content.random() < 0.6
    discount_val = rng_content.choice([10000, 15000, 20000, 30000]) if has_discount else 0
    vat_percent = rng_content.choice([8, 10])
    taxable = max(0, subtotal - discount_val)
    vat_val = int(taxable * (vat_percent / 100))
    grand_total = taxable + vat_val

    # Footer data (deterministic for both authentic & tampered)
    lookup_code_str = f"Mã tra cứu: HD{rng_content.randint(10000000, 99999999)}"
    barcode_seed = rng_content.randint(100000, 999999)

    # Tampering Plan
    tamper_type = rng_tamper.choice(["qty_and_total", "grand_total_only", "full_financial"])
    tamper_item_idx = rng_tamper.randint(0, len(items_data) - 1)
    
    if tamper_type in ["qty_and_total", "full_financial"]:
        orig_item = items_data[tamper_item_idx]
        forged_qty = orig_item["qty"] + rng_tamper.choice([2, 3, 4])
        forged_item_tot = forged_qty * orig_item["price"]
        item_delta = forged_item_tot - orig_item["total"]
    else:
        forged_qty = None
        forged_item_tot = None
        item_delta = 0
        
    if tamper_type == "full_financial":
        f_subtotal = subtotal + item_delta
        f_taxable = max(0, f_subtotal - discount_val)
        f_vat = int(f_taxable * (vat_percent / 100))
        f_grand = f_taxable + f_vat
    elif tamper_type == "grand_total_only":
        f_subtotal = subtotal
        f_vat = vat_val
        f_grand = grand_total + rng_tamper.choice([100000, 200000, 300000])
    else:  # qty_and_total
        f_subtotal = subtotal
        f_vat = vat_val
        f_grand = grand_total

    # ==========================================================================
    # SYNCHRONIZED RENDERING (Authentic + Tampered + Mask)
    # ==========================================================================
    bg_auth = create_thermal_background(width, height, add_streaks=True, seed=seed)
    bg_tamper = bg_auth.copy()
    mask = Image.new("L", (width, height), 0)
    
    draw_a = ImageDraw.Draw(bg_auth)
    draw_t = ImageDraw.Draw(bg_tamper)
    draw_m = ImageDraw.Draw(mask)
    
    ink_color = (22, 22, 22)
    tamper_ink_text = (26, 26, 26)
    tamper_ink_total = (28, 28, 28)
    pad = 2
    
    tampered_fields = []
    
    def record_tamper(box_auth, box_tamp, field_name, orig_val, forged_val):
        union_box = [
            min(box_auth[0], box_tamp[0]) - pad,
            min(box_auth[1], box_tamp[1]) - pad,
            max(box_auth[2], box_tamp[2]) + pad,
            max(box_auth[3], box_tamp[3]) + pad
        ]
        draw_m.rectangle(union_box, fill=255)
        tampered_fields.append({
            "field": field_name,
            "original": str(orig_val),
            "forged": str(forged_val),
            "bbox": union_box
        })

    # Header
    y = 35
    tb = font_title.getbbox(brand_name)
    title_x = (width - (tb[2] - tb[0])) // 2
    draw_a.text((title_x, y), brand_name, fill=ink_color, font=font_title)
    draw_t.text((title_x, y), brand_name, fill=ink_color, font=font_title)
    y += 34
    
    addr_x = (width - font_sub.getbbox(address)[2]) // 2
    draw_a.text((addr_x, y), address, fill=ink_color, font=font_sub)
    draw_t.text((addr_x, y), address, fill=ink_color, font=font_sub)
    y += 22
    
    info_str = f"Hotline: {hotline} - Wifi: {wifi}"
    info_x = (width - font_sub.getbbox(info_str)[2]) // 2
    draw_a.text((info_x, y), info_str, fill=ink_color, font=font_sub)
    draw_t.text((info_x, y), info_str, fill=ink_color, font=font_sub)
    y += 28
    
    hdr_line = "=== HÓA ĐƠN BÁN HÀNG ==="
    hdr_x = (width - font_bold.getbbox(hdr_line)[2]) // 2
    draw_a.text((hdr_x, y), hdr_line, fill=ink_color, font=font_bold)
    draw_t.text((hdr_x, y), hdr_line, fill=ink_color, font=font_bold)
    y += 28
    
    draw_a.text((40, y), f"Số: {receipt_code}", fill=ink_color, font=font_text)
    draw_t.text((40, y), f"Số: {receipt_code}", fill=ink_color, font=font_text)
    tbl_x = width - 40 - font_text.getbbox(table_label)[2]
    draw_a.text((tbl_x, y), table_label, fill=ink_color, font=font_text)
    draw_t.text((tbl_x, y), table_label, fill=ink_color, font=font_text)
    y += 22
    
    draw_a.text((40, y), f"Ngày: {date_str}", fill=ink_color, font=font_text)
    draw_t.text((40, y), f"Ngày: {date_str}", fill=ink_color, font=font_text)
    c_str = f"TN: {cashier_name}"
    c_x = width - 40 - font_text.getbbox(c_str)[2]
    draw_a.text((c_x, y), c_str, fill=ink_color, font=font_text)
    draw_t.text((c_x, y), c_str, fill=ink_color, font=font_text)
    y += 26
    
    div = "-" * int((width - 80) / 10.5)
    draw_a.text((40, y), div, fill=ink_color, font=font_text)
    draw_t.text((40, y), div, fill=ink_color, font=font_text)
    y += 20
    
    # Table header
    draw_a.text((40, y), "Tên hàng", fill=ink_color, font=font_bold)
    draw_t.text((40, y), "Tên hàng", fill=ink_color, font=font_bold)
    draw_a.text((width // 2, y), "SL", fill=ink_color, font=font_bold)
    draw_t.text((width // 2, y), "SL", fill=ink_color, font=font_bold)
    draw_a.text((width - 170, y), "Đ.Giá", fill=ink_color, font=font_bold)
    draw_t.text((width - 170, y), "Đ.Giá", fill=ink_color, font=font_bold)
    draw_a.text((width - 80, y), "T.Tiền", fill=ink_color, font=font_bold)
    draw_t.text((width - 80, y), "T.Tiền", fill=ink_color, font=font_bold)
    y += 22
    draw_a.text((40, y), div, fill=ink_color, font=font_text)
    draw_t.text((40, y), div, fill=ink_color, font=font_text)
    y += 22
    
    # Item rows
    for i, it in enumerate(items_data):
        item_name = it["name"][:20]
        draw_a.text((40, y), item_name, fill=ink_color, font=font_item)
        draw_t.text((40, y), item_name, fill=ink_color, font=font_item)
        
        # Quantity
        qty_x = width // 2 + 5
        orig_q_str = str(it["qty"])
        if (tamper_type in ["qty_and_total", "full_financial"]) and i == tamper_item_idx:
            forged_q_str = str(forged_qty)
            b_qa = draw_a.textbbox((qty_x, y), orig_q_str, font=font_item)
            b_qt = draw_t.textbbox((qty_x, y), forged_q_str, font=font_item)
            draw_a.text((qty_x, y), orig_q_str, fill=ink_color, font=font_item)
            draw_t.text((qty_x, y), forged_q_str, fill=tamper_ink_text, font=font_item)
            record_tamper(b_qa, b_qt, f"item_{i}_qty", orig_q_str, forged_q_str)
        else:
            draw_a.text((qty_x, y), orig_q_str, fill=ink_color, font=font_item)
            draw_t.text((qty_x, y), orig_q_str, fill=ink_color, font=font_item)
            
        # Price (always identical)
        p_str = f"{it['price']:,}"
        p_x = width - 130 - font_item.getbbox(p_str)[2]
        draw_a.text((p_x, y), p_str, fill=ink_color, font=font_item)
        draw_t.text((p_x, y), p_str, fill=ink_color, font=font_item)
        
        # Total
        orig_tot_str = f"{it['total']:,}"
        orig_tot_x = width - 40 - font_item.getbbox(orig_tot_str)[2]
        if (tamper_type in ["qty_and_total", "full_financial"]) and i == tamper_item_idx:
            f_tot_str = f"{forged_item_tot:,}"
            f_tot_x = width - 40 - font_item.getbbox(f_tot_str)[2]
            b_ta = draw_a.textbbox((orig_tot_x, y), orig_tot_str, font=font_item)
            b_tt = draw_t.textbbox((f_tot_x, y), f_tot_str, font=font_item)
            draw_a.text((orig_tot_x, y), orig_tot_str, fill=ink_color, font=font_item)
            draw_t.text((f_tot_x, y), f_tot_str, fill=tamper_ink_text, font=font_item)
            record_tamper(b_ta, b_tt, f"item_{i}_total", orig_tot_str, f_tot_str)
        else:
            draw_a.text((orig_tot_x, y), orig_tot_str, fill=ink_color, font=font_item)
            draw_t.text((orig_tot_x, y), orig_tot_str, fill=ink_color, font=font_item)
            
        y += 24

    y += 6
    eq_div = "=" * int((width - 80) / 10.5)
    draw_a.text((40, y), eq_div, fill=ink_color, font=font_text)
    draw_t.text((40, y), eq_div, fill=ink_color, font=font_text)
    y += 24
    
    # Subtotal
    draw_a.text((40, y), "Tổng tiền hàng:", fill=ink_color, font=font_text)
    draw_t.text((40, y), "Tổng tiền hàng:", fill=ink_color, font=font_text)
    orig_st_str = f"{subtotal:,} đ"
    st_orig_x = width - 40 - font_text.getbbox(orig_st_str)[2]
    if tamper_type == "full_financial":
        f_st_str = f"{f_subtotal:,} đ"
        st_f_x = width - 40 - font_text.getbbox(f_st_str)[2]
        b_sta = draw_a.textbbox((st_orig_x, y), orig_st_str, font=font_text)
        b_stt = draw_t.textbbox((st_f_x, y), f_st_str, font=font_text)
        draw_a.text((st_orig_x, y), orig_st_str, fill=ink_color, font=font_text)
        draw_t.text((st_f_x, y), f_st_str, fill=tamper_ink_text, font=font_text)
        record_tamper(b_sta, b_stt, "subtotal", orig_st_str, f_st_str)
    else:
        draw_a.text((st_orig_x, y), orig_st_str, fill=ink_color, font=font_text)
        draw_t.text((st_orig_x, y), orig_st_str, fill=ink_color, font=font_text)
    y += 24
    
    # Discount (if any, always authentic)
    if has_discount:
        draw_a.text((40, y), "Chiết khấu / Giảm giá:", fill=ink_color, font=font_text)
        draw_t.text((40, y), "Chiết khấu / Giảm giá:", fill=ink_color, font=font_text)
        dc_str = f"-{discount_val:,} đ"
        dc_x = width - 40 - font_text.getbbox(dc_str)[2]
        draw_a.text((dc_x, y), dc_str, fill=ink_color, font=font_text)
        draw_t.text((dc_x, y), dc_str, fill=ink_color, font=font_text)
        y += 24
        
    # VAT
    vat_label = f"Thuế VAT ({vat_percent}%):"
    draw_a.text((40, y), vat_label, fill=ink_color, font=font_text)
    draw_t.text((40, y), vat_label, fill=ink_color, font=font_text)
    orig_vat_str = f"{vat_val:,} đ"
    vat_orig_x = width - 40 - font_text.getbbox(orig_vat_str)[2]
    if tamper_type == "full_financial":
        f_vat_str = f"{f_vat:,} đ"
        vat_f_x = width - 40 - font_text.getbbox(f_vat_str)[2]
        b_vata = draw_a.textbbox((vat_orig_x, y), orig_vat_str, font=font_text)
        b_vatt = draw_t.textbbox((vat_f_x, y), f_vat_str, font=font_text)
        draw_a.text((vat_orig_x, y), orig_vat_str, fill=ink_color, font=font_text)
        draw_t.text((vat_f_x, y), f_vat_str, fill=tamper_ink_text, font=font_text)
        record_tamper(b_vata, b_vatt, "vat", orig_vat_str, f_vat_str)
    else:
        draw_a.text((vat_orig_x, y), orig_vat_str, fill=ink_color, font=font_text)
        draw_t.text((vat_orig_x, y), orig_vat_str, fill=ink_color, font=font_text)
    y += 28
    
    # Grand Total
    draw_a.text((40, y), "TỔNG CỘNG:", fill=ink_color, font=font_total)
    draw_t.text((40, y), "TỔNG CỘNG:", fill=ink_color, font=font_total)
    orig_gt_str = f"{grand_total:,} đ"
    gt_orig_x = width - 40 - font_total.getbbox(orig_gt_str)[2]
    if tamper_type in ["full_financial", "grand_total_only"]:
        f_gt_str = f"{f_grand:,} đ"
        gt_f_x = width - 40 - font_total.getbbox(f_gt_str)[2]
        b_gta = draw_a.textbbox((gt_orig_x, y), orig_gt_str, font=font_total)
        b_gtt = draw_t.textbbox((gt_f_x, y), f_gt_str, font=font_total)
        draw_a.text((gt_orig_x, y), orig_gt_str, fill=ink_color, font=font_total)
        draw_t.text((gt_f_x, y), f_gt_str, fill=tamper_ink_total, font=font_total)
        record_tamper(b_gta, b_gtt, "grand_total", orig_gt_str, f_gt_str)
    else:
        draw_a.text((gt_orig_x, y), orig_gt_str, fill=ink_color, font=font_total)
        draw_t.text((gt_orig_x, y), orig_gt_str, fill=ink_color, font=font_total)
    y += 34
    
    draw_a.text((40, y), div, fill=ink_color, font=font_text)
    draw_t.text((40, y), div, fill=ink_color, font=font_text)
    y += 22
    
    method_str = "Phương thức: Tiền mặt / Thẻ ngân hàng / QR"
    draw_a.text((40, y), method_str, fill=ink_color, font=font_footer)
    draw_t.text((40, y), method_str, fill=ink_color, font=font_footer)
    y += 20
    
    # Lookup code (IDENTICAL on both)
    draw_a.text((40, y), lookup_code_str, fill=ink_color, font=font_footer)
    draw_t.text((40, y), lookup_code_str, fill=ink_color, font=font_footer)
    y += 28
    
    # Barcode (IDENTICAL on both)
    draw_barcode(draw_a, (width - 340) // 2, y, 340, 42, barcode_seed)
    draw_barcode(draw_t, (width - 340) // 2, y, 340, 42, barcode_seed)
    y += 52
    
    f1 = "CẢM ƠN QUÝ KHÁCH - HẸN GẶP LẠI!"
    f1_x = (width - font_bold.getbbox(f1)[2]) // 2
    draw_a.text((f1_x, y), f1, fill=ink_color, font=font_bold)
    draw_t.text((f1_x, y), f1, fill=ink_color, font=font_bold)
    y += 20
    
    f2 = "(Vui lòng kiểm tra lại hóa đơn trước khi rời quầy)"
    f2_x = (width - font_footer.getbbox(f2)[2]) // 2
    draw_a.text((f2_x, y), f2, fill=ink_color, font=font_footer)
    draw_t.text((f2_x, y), f2, fill=ink_color, font=font_footer)

    # ==========================================================================
    # RIGOROUS VERIFICATION (diff ⊆ mask)
    # ==========================================================================
    diff = ImageChops.difference(bg_auth, bg_tamper).convert("L").point(lambda p: 255 if p > 0 else 0)
    outside = ImageChops.subtract(diff, mask)
    outside_px = outside.histogram()[255]
    diff_px = diff.histogram()[255]
    mask_px = mask.histogram()[255]
    
    if outside_px > 0:
        raise ValueError(
            f"ERROR in Sample {sample_index} ({template_type}): "
            f"{outside_px} diff pixels are OUTSIDE mask! BBox: {outside.getbbox()}"
        )
    assert diff_px > 0, f"Sample {sample_index}: diff_px is 0!"
    assert mask_px >= diff_px, f"Sample {sample_index}: mask_px ({mask_px}) < diff_px ({diff_px})"

    # Printed financial states & arithmetic consistency (Z2)
    auth_items_printed = [
        {"name": it["name"], "qty": it["qty"], "price": it["price"], "total": it["total"]}
        for it in items_data
    ]
    tamp_items_printed = []
    for idx_it, it in enumerate(items_data):
        if (tamper_type in ["qty_and_total", "full_financial"]) and idx_it == tamper_item_idx:
            tamp_items_printed.append({
                "name": it["name"],
                "qty": forged_qty,
                "price": it["price"],
                "total": forged_item_tot,
            })
        else:
            tamp_items_printed.append({
                "name": it["name"],
                "qty": it["qty"],
                "price": it["price"],
                "total": it["total"],
            })

    auth_arith = check_arith_consistent(
        auth_items_printed, subtotal, discount_val, vat_percent, vat_val, grand_total
    )
    tamp_arith = check_arith_consistent(
        tamp_items_printed, f_subtotal, discount_val, vat_percent, f_vat, f_grand
    )
    assert auth_arith is True, f"Sample {sample_index}: authentic arith_consistent must be True!"
    assert tamp_arith is (tamper_type == "full_financial"), (
        f"Sample {sample_index}: unexpected tampered arith_consistent={tamp_arith} for {tamper_type}!"
    )

    authentic_fin = {
        "items": auth_items_printed,
        "subtotal": subtotal,
        "discount": discount_val,
        "vat_percent": vat_percent,
        "vat": vat_val,
        "grand_total": grand_total,
        "arith_consistent": auth_arith,
    }
    tampered_fin = {
        "items": tamp_items_printed,
        "subtotal": f_subtotal,
        "discount": discount_val,
        "vat_percent": vat_percent,
        "vat": f_vat,
        "grand_total": f_grand,
        "arith_consistent": tamp_arith,
    }

    meta = {
        "sample_id": f"receipt_{sample_index:04d}",
        "seed": seed,
        "template": template_type,
        "template_id": template_id,
        "brand_name": brand_name,
        "receipt_code": receipt_code,
        "date": date_str,
        "width": width,
        "height": height,
        "tamper_type": tamper_type,
        "tampering_type": tamper_type,
        "tampered_fields": tampered_fields,
        "n_regions": len(tampered_fields),
        "authentic": authentic_fin,
        "tampered": tampered_fin,
        "arith_consistent": tamp_arith,
        "mask_px": mask_px,
        "diff_px": diff_px,
        "diff_outside_mask_px": outside_px,
        "mask_covers_diff": 1.0,
        "generator_version": "v2"
    }

    return bg_auth, bg_tamper, mask, meta


def main():
    parser = argparse.ArgumentParser(description="Generate 500 Vietnamese POS thermal receipt triplets (V2).")
    parser.add_argument("--font-dir", default=None, help="Directory containing DejaVu TrueType fonts.")
    parser.add_argument("--out-dir", default=DATASET_DIR, help="Output dataset directory.")
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Update metadata.json and manifest.jsonl only, verifying pixel identity against existing images.",
    )
    args = parser.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    auth_dir = os.path.join(out_dir, "authentic")
    tamp_dir = os.path.join(out_dir, "tampered")
    masks_dir = os.path.join(out_dir, "masks")
    os.makedirs(auth_dir, exist_ok=True)
    os.makedirs(tamp_dir, exist_ok=True)
    os.makedirs(masks_dir, exist_ok=True)

    # Validate font resolution upfront
    resolved_fonts = resolve_font_paths(args.font_dir)

    print("=" * 65)
    print("🚀 BẮT ĐẦU SINH TẬP DỮ LIỆU HÓA ĐƠN IN NHIỆT (500 MẪU - V2)")
    print("4 Template: Cafe (125), Siêu thị (125), Cửa hàng tiện lợi (125), Custom (125)")
    print(f"Lưu tại: {out_dir} (metadata_only={args.metadata_only})")
    print(f"Font dir: {os.path.dirname(resolved_fonts[0])}")
    print("Tự động kiểm tra: 100% diff pixel phải nằm trọn trong mask (diff ⊆ mask) + arith_consistent")
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
    total_samples = 500
    
    for t_name, count in templates:
        print(f"\n📂 Đang xử lý template [{t_name.upper()}] ({count} mẫu)...")
        for i in range(count):
            seed = 10000 + current_idx * 17
            auth_im, fake_im, mask_im, meta = generate_single_receipt_v2(
                t_name, current_idx, seed=seed, font_dir=args.font_dir
            )
            
            sample_id = f"receipt_{current_idx:04d}"
            auth_path = os.path.join(auth_dir, f"{sample_id}_authentic.png")
            fake_path = os.path.join(tamp_dir, f"{sample_id}_tampered.png")
            mask_path = os.path.join(masks_dir, f"{sample_id}_mask.png")
            
            if args.metadata_only:
                # Verify pixel-by-pixel identity with existing V2 images on disk
                for disk_p, gen_im in ((auth_path, auth_im), (fake_path, fake_im), (mask_path, mask_im)):
                    if os.path.exists(disk_p):
                        disk_im = Image.open(disk_p).convert(gen_im.mode)
                        if ImageChops.difference(disk_im, gen_im).getbbox() is not None:
                            raise ValueError(f"Pixel mismatch against existing file: {disk_p}")
            else:
                auth_im.save(auth_path, optimize=True)
                fake_im.save(fake_path, optimize=True)
                mask_im.save(mask_path, optimize=True)
            
            meta["authentic_file"] = f"authentic/{sample_id}_authentic.png"
            meta["tampered_file"] = f"tampered/{sample_id}_tampered.png"
            meta["mask_file"] = f"masks/{sample_id}_mask.png"
            manifest_records.append(meta)
            
            if (i + 1) % 25 == 0 or (i + 1) == count:
                print(
                    f"  -> [{t_name}] Đã xong {i+1}/{count} mẫu ({sample_id}) | "
                    f"Diff: {meta['diff_px']} px | Arith: {meta['arith_consistent']} | Outside: 0"
                )
                
            current_idx += 1
            
    # Write metadata JSON Lines & JSON
    manifest_jsonl = os.path.join(out_dir, "manifest.jsonl")
    manifest_json = os.path.join(out_dir, "metadata.json")
    
    with open(manifest_jsonl, "w", encoding="utf-8") as f:
        for r in manifest_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    with open(manifest_json, "w", encoding="utf-8") as f:
        json.dump(manifest_records, f, ensure_ascii=False, indent=2)
        
    duration = time.time() - start_time
    print("\n" + "=" * 65)
    print(f"🎉 HOÀN THÀNH {total_samples} MẪU DATASET V2 TRONG {duration:.2f} GIÂY!")
    print(f"📁 Authentic Images: {len(os.listdir(auth_dir))} file ({auth_dir})")
    print(f"📁 Tampered Images:  {len(os.listdir(tamp_dir))} file ({tamp_dir})")
    print(f"📁 Ground-Truth Masks: {len(os.listdir(masks_dir))} file ({masks_dir})")
    print(f"📋 Manifest JSONL:   {manifest_jsonl}")
    print(f"📋 Metadata JSON:    {manifest_json}")
    print("=" * 65)


if __name__ == "__main__":
    main()
