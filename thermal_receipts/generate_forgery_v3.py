import argparse
import copy
import io
import json
import os
import random
import shutil
import sys
import time
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from thermal_receipts.generate_dataset_500 import (
    CAFE_BRANDS,
    CAFE_ITEMS,
    CONVENIENCE_BRANDS,
    CONVENIENCE_ITEMS,
    CUSTOM_BRANDS,
    DEFAULT_FONT_DIR,
    MART_BRANDS,
    MART_ITEMS,
    STREETS,
    gen_person_name,
    resolve_font_paths,
)

DEFAULT_V2_DIR = os.path.join(REPO_DIR, "dataset")
DEFAULT_OUT_DIR = os.path.join(REPO_DIR, "dataset_v3_realistic")

METHODS = ("copy_move", "splice_font", "splice_same_font", "double_jpeg")
JPEG_QF_PAIRS = [(75, 85), (75, 95), (85, 75), (85, 95), (95, 75), (95, 85)]


def resolve_v3_fonts(font_dir=None):
    """Resolve both DejaVu (authentic) and alternate splice fonts (Liberation Sans / Mono)."""
    reg_dejavu, bold_dejavu, sans_bold_dejavu = resolve_font_paths(font_dir)
    base_dir = os.path.dirname(reg_dejavu)

    alt_candidates = [
        base_dir,
        DEFAULT_FONT_DIR,
        "/usr/share/fonts/truetype/liberation",
    ]
    alt_files = (
        "LiberationSans-Regular.ttf",
        "LiberationSans-Bold.ttf",
        "LiberationMono-Regular.ttf",
        "LiberationMono-Bold.ttf",
    )
    alt_dir = None
    for cand in alt_candidates:
        if all(os.path.isfile(os.path.join(cand, fn)) for fn in alt_files):
            alt_dir = cand
            break
    if alt_dir is None:
        raise FileNotFoundError(
            f"Could not find alternate splice fonts {alt_files}. "
            f"Pass --font-dir pointing to bundled fonts ({DEFAULT_FONT_DIR})."
        )

    return {
        "dejavu_reg": reg_dejavu,
        "dejavu_bold": bold_dejavu,
        "dejavu_sans_bold": sans_bold_dejavu,
        "libsans_reg": os.path.join(alt_dir, "LiberationSans-Regular.ttf"),
        "libsans_bold": os.path.join(alt_dir, "LiberationSans-Bold.ttf"),
        "libmono_reg": os.path.join(alt_dir, "LiberationMono-Regular.ttf"),
        "libmono_bold": os.path.join(alt_dir, "LiberationMono-Bold.ttf"),
    }


def boxes_overlap(a, b, margin=2):
    return not (
        a[2] + margin < b[0]
        or a[0] - margin > b[2]
        or a[3] + margin < b[1]
        or a[1] - margin > b[3]
    )


def extract_untouched_glyph_pool(auth_im, sample_meta, fonts_map):
    """Reconstruct exact character cell bounding boxes for all untouched text spans on the V2 receipt."""
    seed = sample_meta["seed"]
    sample_index = int(sample_meta["sample_id"].split("_")[1])
    template_type = sample_meta["template"]
    rng_content = random.Random(seed)

    font_title = ImageFont.truetype(fonts_map["dejavu_sans_bold"], 25)
    font_sub = ImageFont.truetype(fonts_map["dejavu_reg"], 15)
    font_bold = ImageFont.truetype(fonts_map["dejavu_bold"], 17)
    font_text = ImageFont.truetype(fonts_map["dejavu_reg"], 16)
    font_item = ImageFont.truetype(fonts_map["dejavu_reg"], 15)
    font_total = ImageFont.truetype(fonts_map["dejavu_bold"], 23)
    font_footer = ImageFont.truetype(fonts_map["dejavu_reg"], 14)

    if template_type == "cafe":
        brand_name = rng_content.choice(CAFE_BRANDS)
        item_pool = CAFE_ITEMS
        num_items = rng_content.randint(3, 5)
        width, height = 620, 960
        table_label = f"Bàn: T{rng_content.randint(1, 15):02d} ({rng_content.choice(['Mang đi', 'Tại quán'])})"
    elif template_type == "supermarket":
        brand_name = rng_content.choice(MART_BRANDS)
        item_pool = MART_ITEMS
        num_items = rng_content.randint(4, 7)
        width, height = 660, 1020 + (num_items - 4) * 24
        table_label = f"Quầy: POS-{rng_content.randint(1, 8):02d}"
    elif template_type == "convenience":
        brand_name = rng_content.choice(CONVENIENCE_BRANDS)
        item_pool = CONVENIENCE_ITEMS
        num_items = rng_content.randint(3, 5)
        width, height = 600, 940
        table_label = f"Quầy: 01 ({rng_content.choice(['Take-away', 'Tại quầy'])})"
    else:
        custom_choice = rng_content.choice(CUSTOM_BRANDS)
        brand_name = custom_choice[0]
        item_pool = custom_choice[2]
        num_items = rng_content.randint(3, 5)
        width, height = 630, 960
        table_label = f"Số phiếu: P-{rng_content.randint(10, 99)}"

    selected_raw = rng_content.sample(item_pool, num_items)
    items_data = []
    for raw in selected_raw:
        qty = rng_content.randint(1, 4)
        price = rng_content.choice([raw[1], raw[2]])
        items_data.append({"name": raw[0], "qty": qty, "price": price, "total": qty * price})

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
    lookup_code_str = f"Mã tra cứu: HD{rng_content.randint(10000000, 99999999)}"

    draw = ImageDraw.Draw(auth_im)
    spans = []  # (text, x, y, font, size_px, is_bold, priority)
    # priority: lower = preferred (0: item/summary columns, 1: receipt header/meta, 2: footer)

    y = 35
    _ = font_title.getbbox(brand_name)
    y += 34
    addr_x = (width - font_sub.getbbox(address)[2]) // 2
    spans.append((address, addr_x, y, font_sub, 15, False, 1))
    y += 22

    info_str = f"Hotline: {hotline} - Wifi: {wifi}"
    info_x = (width - font_sub.getbbox(info_str)[2]) // 2
    spans.append((info_str, info_x, y, font_sub, 15, False, 1))
    y += 28
    y += 28  # hdr_line

    spans.append((f"Số: {receipt_code}", 40, y, font_text, 16, False, 1))
    tbl_x = width - 40 - font_text.getbbox(table_label)[2]
    spans.append((table_label, tbl_x, y, font_text, 16, False, 1))
    y += 22

    spans.append((f"Ngày: {date_str}", 40, y, font_text, 16, False, 1))
    _ = cashier_name
    y += 26
    y += 20  # div
    y += 22  # table header
    y += 22  # div

    tampered_field_map = {tf["field"]: tf for tf in sample_meta["tampered_fields"]}
    forbidden_boxes = [tf["bbox"] for tf in sample_meta["tampered_fields"]]
    field_positions = {}

    for i, it in enumerate(items_data):
        qty_x = width // 2 + 5
        orig_q_str = str(it["qty"])
        if f"item_{i}_qty" in tampered_field_map:
            field_positions[f"item_{i}_qty"] = {
                "align": "left",
                "anchor_x": qty_x,
                "y": y,
                "size": 15,
                "bold": False,
            }
        else:
            spans.append((orig_q_str, qty_x, y, font_item, 15, False, 0))

        p_str = f"{it['price']:,}"
        p_x = width - 130 - font_item.getbbox(p_str)[2]
        spans.append((p_str, p_x, y, font_item, 15, False, 0))

        orig_tot_str = f"{it['total']:,}"
        orig_tot_x = width - 40 - font_item.getbbox(orig_tot_str)[2]
        if f"item_{i}_total" in tampered_field_map:
            field_positions[f"item_{i}_total"] = {
                "align": "right",
                "anchor_x": width - 40,
                "y": y,
                "size": 15,
                "bold": False,
            }
        else:
            spans.append((orig_tot_str, orig_tot_x, y, font_item, 15, False, 0))
        y += 24

    y += 6
    y += 24  # eq_div

    orig_st_str = f"{subtotal:,} đ"
    st_orig_x = width - 40 - font_text.getbbox(orig_st_str)[2]
    if "subtotal" in tampered_field_map:
        field_positions["subtotal"] = {
            "align": "right",
            "anchor_x": width - 40,
            "y": y,
            "size": 16,
            "bold": False,
        }
    else:
        spans.append((orig_st_str, st_orig_x, y, font_text, 16, False, 0))
    y += 24

    if has_discount:
        dc_str = f"-{discount_val:,} đ"
        dc_x = width - 40 - font_text.getbbox(dc_str)[2]
        spans.append((dc_str, dc_x, y, font_text, 16, False, 0))
        y += 24

    vat_label = f"Thuế VAT ({vat_percent}%):"
    spans.append((vat_label, 40, y, font_text, 16, False, 1))
    orig_vat_str = f"{vat_val:,} đ"
    vat_orig_x = width - 40 - font_text.getbbox(orig_vat_str)[2]
    if "vat" in tampered_field_map:
        field_positions["vat"] = {
            "align": "right",
            "anchor_x": width - 40,
            "y": y,
            "size": 16,
            "bold": False,
        }
    else:
        spans.append((orig_vat_str, vat_orig_x, y, font_text, 16, False, 0))
    y += 28

    orig_gt_str = f"{grand_total:,} đ"
    gt_orig_x = width - 40 - font_total.getbbox(orig_gt_str)[2]
    if "grand_total" in tampered_field_map:
        field_positions["grand_total"] = {
            "align": "right",
            "anchor_x": width - 40,
            "y": y,
            "size": 23,
            "bold": True,
        }
    else:
        spans.append((orig_gt_str, gt_orig_x, y, font_total, 23, True, 0))
    y += 34

    y += 22  # div
    y += 20  # method_str
    spans.append((lookup_code_str, 40, y, font_footer, 14, False, 2))
    y += 28
    y += 52  # barcode
    y += 20  # f1
    y += 22  # below f2 -> blank paper starts around y + 10

    blank_y_start = min(y + 12, height - 90)
    blank_y_end = height - 16

    # Build character donor map: char -> list of donor dicts
    glyph_pool = {}
    for text, sx, sy, fnt, sz, is_bold, prio in spans:
        # Uniform vertical cell anchored to line y so baselines align cleanly
        ref_tb = draw.textbbox((0, sy), "0123456789,", font=fnt)
        cell_y0 = max(0, ref_tb[1] - 1)
        cell_y1 = min(height, ref_tb[3] + 1)
        for idx_ch, ch in enumerate(text):
            if ch not in "0123456789,đ":
                continue
            cx0 = int(round(sx + draw.textlength(text[:idx_ch], font=fnt)))
            cx1 = int(round(sx + draw.textlength(text[: idx_ch + 1], font=fnt)))
            if cx1 <= cx0:
                continue
            cbox_incl = [cx0, cell_y0, cx1 - 1, cell_y1 - 1]
            if any(boxes_overlap(cbox_incl, fb, margin=3) for fb in forbidden_boxes):
                continue
            glyph_pool.setdefault(ch, []).append({
                "char": ch,
                "crop_box": (cx0, cell_y0, cx1, cell_y1),  # PIL crop (exclusive right/bottom)
                "bbox_incl": cbox_incl,                    # Metadata bbox (inclusive)
                "size": sz,
                "bold": is_bold,
                "priority": prio,
            })

    return glyph_pool, field_positions, (blank_y_start, blank_y_end)


def sample_clean_bg_patch(canvas_im, target_w, target_h, target_x0, blank_y_range, rng):
    """Crop an ink-free local thermal paper background patch from the same receipt."""
    w, h = canvas_im.size
    by0, by1 = blank_y_range
    # Try matching x coordinate (with small jitter) in the receipt's blank thermal paper zone
    for attempt in range(40):
        jitter_x = rng.randint(-8, 8) if attempt > 0 else 0
        sx0 = max(12, min(w - 12 - target_w, target_x0 + jitter_x))
        max_sy0 = max(by0, by1 - target_h)
        sy0 = rng.randint(by0, max_sy0) if max_sy0 > by0 else by0
        sy0 = max(10, min(h - 12 - target_h, sy0))
        patch = canvas_im.crop((sx0, sy0, sx0 + target_w, sy0 + target_h))
        extrema = patch.getextrema()
        min_val = min(ch_ext[0] for ch_ext in extrema)
        if min_val >= 210:  # Clean thermal paper (even under JPEG QF75 noise)
            return patch
    # Fallback: top margin strip y=10..32 tiled if needed
    strip = canvas_im.crop((max(12, min(w - 12 - target_w, target_x0)), 10, max(12, min(w - 12 - target_w, target_x0)) + target_w, 30))
    out = Image.new("RGB", (target_w, target_h))
    for yy in range(0, target_h, strip.height):
        out.paste(strip, (0, yy))
    return out


def can_copy_move_sample(glyph_pool, tampered_fields):
    """Return True if every forged character needed (excluding unchanged ' đ' suffix) exists in glyph_pool."""
    for tf in tampered_fields:
        forged_str = tf["forged"]
        orig_str = tf["original"]
        if forged_str.endswith(" đ") and orig_str.endswith(" đ"):
            core = forged_str[:-2]
        else:
            core = forged_str
        for ch in core:
            if ch == " ":
                continue
            if ch not in glyph_pool or len(glyph_pool[ch]) == 0:
                return False
    return True


def apply_copy_move_edits(base_im, sample_meta, glyph_pool, field_positions, blank_y_range, fonts_map, rng):
    """Apply copy-move forgery by cropping authentic digit glyphs from elsewhere on the same receipt."""
    out_im = base_im.copy()
    draw_ref = ImageDraw.Draw(out_im)
    updated_fields = []
    all_source_bboxes = []

    font_dejavu_map = {
        (15, False): ImageFont.truetype(fonts_map["dejavu_reg"], 15),
        (16, False): ImageFont.truetype(fonts_map["dejavu_reg"], 16),
        (23, True): ImageFont.truetype(fonts_map["dejavu_bold"], 23),
    }

    for tf in sample_meta["tampered_fields"]:
        fname = tf["field"]
        orig_str = tf["original"]
        forged_str = tf["forged"]
        orig_bbox = tf["bbox"]  # inclusive [x0, y0, x1, y1]
        pos = field_positions[fname]
        target_fnt = font_dejavu_map[(pos["size"], pos["bold"])]

        # If both original and forged end with ' đ' (right-aligned at width-40), keep ' đ' untouched in place
        keep_currency_suffix = forged_str.endswith(" đ") and orig_str.endswith(" đ") and pos["align"] == "right"
        if keep_currency_suffix:
            suffix_w = int(round(draw_ref.textlength(" đ", font=target_fnt)))
            edit_right_x = pos["anchor_x"] - suffix_w
            orig_num_w = int(round(draw_ref.textlength(orig_str[:-2], font=target_fnt)))
            orig_edit_x0 = edit_right_x - orig_num_w - 2
            orig_edit_x1 = edit_right_x  # exclusive right edge right before ' đ'
            core_forged = forged_str[:-2]
        else:
            edit_right_x = pos["anchor_x"]
            orig_edit_x0 = orig_bbox[0]
            orig_edit_x1 = orig_bbox[2] + 1
            core_forged = forged_str

        ref_tb = draw_ref.textbbox((0, pos["y"]), "0123456789,", font=target_fnt)
        target_y0 = ref_tb[1] - 1
        target_y1 = ref_tb[3] + 1
        target_cell_h = target_y1 - target_y0
        target_char_w = max(1, int(round(draw_ref.textlength("0", font=target_fnt))))

        # Select donor glyphs for each character in core_forged
        cropped_cells = []
        field_sources = []
        for ch in core_forged:
            if ch == " ":
                blank_cell = sample_clean_bg_patch(base_im, target_char_w, target_cell_h, edit_right_x - 20, blank_y_range, rng)
                cropped_cells.append(blank_cell)
                continue
            candidates = glyph_pool[ch]
            # Sort candidates by size match, bold match, priority, then pick deterministically with slight variety
            ranked = sorted(
                candidates,
                key=lambda d: (
                    0 if (d["size"] == pos["size"] and d["bold"] == pos["bold"]) else 1,
                    abs(d["size"] - pos["size"]),
                    d["priority"],
                ),
            )
            top_tier = [c for c in ranked if c["size"] == ranked[0]["size"] and c["priority"] == ranked[0]["priority"]]
            chosen = rng.choice(top_tier)
            cell_im = base_im.crop(chosen["crop_box"])
            if cell_im.size != (target_char_w, target_cell_h):
                cell_im = cell_im.resize((target_char_w, target_cell_h), Image.BICUBIC)
            cropped_cells.append(cell_im)
            field_sources.append(chosen["bbox_incl"])
            all_source_bboxes.append(chosen["bbox_incl"])

        assembled_w = sum(c.width for c in cropped_cells)
        if pos["align"] == "left":
            paste_x0 = pos["anchor_x"]
        else:
            paste_x0 = edit_right_x - assembled_w
        paste_x1 = paste_x0 + assembled_w

        # Erase union of original number region and new pasted glyph region
        erase_x0 = min(orig_edit_x0, paste_x0 - 1)
        erase_y0 = min(orig_bbox[1], target_y0)
        erase_x1 = max(orig_edit_x1, paste_x1 + 1)
        erase_y1 = max(orig_bbox[3] + 1, target_y1)

        bg_patch = sample_clean_bg_patch(
            base_im, erase_x1 - erase_x0, erase_y1 - erase_y0, erase_x0, blank_y_range, rng
        )
        out_im.paste(bg_patch, (erase_x0, erase_y0))

        cur_x = paste_x0
        for cell_im in cropped_cells:
            out_im.paste(cell_im, (cur_x, target_y0))
            cur_x += cell_im.width

        mod_bbox_incl = [erase_x0, erase_y0, erase_x1 - 1, erase_y1 - 1]
        new_tf = copy.deepcopy(tf)
        new_tf["bbox"] = mod_bbox_incl
        new_tf["source_bboxes"] = field_sources
        updated_fields.append(new_tf)

    return out_im, updated_fields, all_source_bboxes


def apply_splice_text_edits(
    base_im, sample_meta, field_positions, blank_y_range, fonts_map, rng, use_alt_font=True
):
    """Erase field with local background patch and render forged text (with alternate font or same font + filter)."""
    out_im = base_im.copy()
    updated_fields = []

    if use_alt_font:
        family = rng.choice(["LiberationSans", "LiberationMono"])
        if family == "LiberationSans":
            f_item = ImageFont.truetype(fonts_map["libsans_reg"], 15)
            f_text = ImageFont.truetype(fonts_map["libsans_reg"], 16)
            f_tot = ImageFont.truetype(fonts_map["libsans_bold"], 23)
        else:
            f_item = ImageFont.truetype(fonts_map["libmono_reg"], 15)
            f_text = ImageFont.truetype(fonts_map["libmono_reg"], 16)
            f_tot = ImageFont.truetype(fonts_map["libmono_bold"], 23)
        filter_mode = "none"
    else:
        family = "DejaVuSansMono"
        f_item = ImageFont.truetype(fonts_map["dejavu_reg"], 15)
        f_text = ImageFont.truetype(fonts_map["dejavu_reg"], 16)
        f_tot = ImageFont.truetype(fonts_map["dejavu_bold"], 23)
        filter_mode = rng.choice(["blur", "sharpen"])

    font_lookup = {(15, False): f_item, (16, False): f_text, (23, True): f_tot}
    ink_choices = [(16, 16, 16), (28, 28, 28), (32, 32, 32)]
    forged_ink = rng.choice(ink_choices)

    probe_draw = ImageDraw.Draw(out_im)

    for tf in sample_meta["tampered_fields"]:
        fname = tf["field"]
        forged_str = tf["forged"]
        orig_bbox = tf["bbox"]
        pos = field_positions[fname]
        fnt = font_lookup[(pos["size"], pos["bold"])]

        tw = int(round(probe_draw.textlength(forged_str, font=fnt)))
        tx = pos["anchor_x"] if pos["align"] == "left" else (pos["anchor_x"] - tw)
        ty = pos["y"]
        new_tb = probe_draw.textbbox((tx, ty), forged_str, font=fnt)

        pad = 3
        erase_x0 = max(8, min(orig_bbox[0], new_tb[0] - pad))
        erase_y0 = max(8, min(orig_bbox[1], new_tb[1] - pad))
        erase_x1 = min(base_im.width - 8, max(orig_bbox[2] + 1, new_tb[2] + pad))
        erase_y1 = min(base_im.height - 8, max(orig_bbox[3] + 1, new_tb[3] + pad))

        patch_w = erase_x1 - erase_x0
        patch_h = erase_y1 - erase_y0
        patch = sample_clean_bg_patch(base_im, patch_w, patch_h, erase_x0, blank_y_range, rng)
        pdraw = ImageDraw.Draw(patch)
        pdraw.text((tx - erase_x0, ty - erase_y0), forged_str, fill=forged_ink, font=fnt)

        if filter_mode == "blur":
            patch = patch.filter(ImageFilter.GaussianBlur(radius=0.65))
        elif filter_mode == "sharpen":
            patch = patch.filter(ImageFilter.UnsharpMask(radius=1.2, percent=145, threshold=2))

        out_im.paste(patch, (erase_x0, erase_y0))
        mod_bbox_incl = [erase_x0, erase_y0, erase_x1 - 1, erase_y1 - 1]
        new_tf = copy.deepcopy(tf)
        new_tf["bbox"] = mod_bbox_incl
        updated_fields.append(new_tf)

    detail = {"font_family": family, "patch_filter": filter_mode, "ink_rgb": list(forged_ink)}
    return out_im, updated_fields, detail


def jpeg_roundtrip(im, quality):
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=int(quality), subsampling=0)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def compute_strict_rgb_diff(im_a, im_b):
    """Exact 3-channel RGB difference mask (255 wherever R, G, or B differs by >= 1)."""
    r, g, b = ImageChops.difference(im_a, im_b).split()
    return ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda p: 255 if p > 0 else 0)


def assign_balanced_methods(selected_by_template, compat_flags, seed=20261107):
    """Assign exactly 75 of each of the 4 methods across 300 samples (18-19 per template),
    ensuring copy_move is only assigned to samples with 100% intra-receipt donor glyph coverage."""
    rng = random.Random(seed)
    assignments = {}
    # Rotate which method gets 18 vs 19 across the 4 templates -> total = 75, 75, 75, 75!
    base_counts = [19, 19, 19, 18]

    for t_idx, (t_name, samples) in enumerate(selected_by_template.items()):
        assert len(samples) == 75, f"Expected 75 samples for {t_name}, got {len(samples)}"
        rotated = base_counts[t_idx:] + base_counts[:t_idx]
        method_quotas = dict(zip(METHODS, rotated))

        incompatible = [m["sample_id"] for m in samples if not compat_flags[m["sample_id"]]]
        compatible = [m["sample_id"] for m in samples if compat_flags[m["sample_id"]]]
        rng.shuffle(incompatible)
        rng.shuffle(compatible)

        # Incompatible samples (missing a rare digit for copy_move) get splice_font or splice_same_font
        non_cm_pool = (
            ["splice_font"] * method_quotas["splice_font"]
            + ["splice_same_font"] * method_quotas["splice_same_font"]
        )
        rng.shuffle(non_cm_pool)
        assert len(incompatible) <= len(non_cm_pool), f"Too many incompatible samples in {t_name}"

        for sid in incompatible:
            assignments[sid] = non_cm_pool.pop()

        remaining_pool = (
            non_cm_pool
            + ["copy_move"] * method_quotas["copy_move"]
            + ["double_jpeg"] * method_quotas["double_jpeg"]
        )
        rng.shuffle(remaining_pool)
        assert len(remaining_pool) == len(compatible)
        for sid, meth in zip(compatible, remaining_pool):
            assignments[sid] = meth

    return assignments


def main():
    parser = argparse.ArgumentParser(
        description="Generate V3 realistic-forgery subset (300 pairs) from V2 authentic receipts."
    )
    parser.add_argument("--v2-dir", default=DEFAULT_V2_DIR, help="Path to V2 dataset directory.")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="Output directory for V3 dataset.")
    parser.add_argument("--font-dir", default=None, help="Directory containing bundled TrueType fonts.")
    args = parser.parse_args()

    v2_dir = os.path.abspath(args.v2_dir)
    out_dir = os.path.abspath(args.out_dir)
    fonts_map = resolve_v3_fonts(args.font_dir)

    auth_out = os.path.join(out_dir, "authentic")
    tamp_out = os.path.join(out_dir, "tampered")
    mask_out = os.path.join(out_dir, "masks")
    os.makedirs(auth_out, exist_ok=True)
    os.makedirs(tamp_out, exist_ok=True)
    os.makedirs(mask_out, exist_ok=True)

    with open(os.path.join(v2_dir, "metadata.json"), encoding="utf-8") as f:
        v2_meta = json.load(f)

    by_template = {"cafe": [], "supermarket": [], "convenience": [], "custom": []}
    for rec in v2_meta:
        t = rec["template"]
        if len(by_template[t]) < 75:
            by_template[t].append(rec)

    selected_samples = (
        by_template["cafe"]
        + by_template["supermarket"]
        + by_template["convenience"]
        + by_template["custom"]
    )
    assert len(selected_samples) == 300

    print("=" * 70)
    print("🚀 SINH DATASET V3 REALISTIC FORGERY (300 CẶP - 75 MẪU / TEMPLATE)")
    print(f"Nguồn V2:  {v2_dir}")
    print(f"Đích V3:   {out_dir}")
    print(f"Font dir:  {os.path.dirname(fonts_map['dejavu_reg'])}")
    print("=" * 70)

    start_t = time.time()

    # Pre-extract glyph pools & check intra-receipt copy-move donor availability
    precomputed = {}
    compat_flags = {}
    for rec in selected_samples:
        sid = rec["sample_id"]
        auth_src = os.path.join(v2_dir, rec["authentic_file"])
        auth_im = Image.open(auth_src).convert("RGB")
        glyph_pool, field_pos, blank_yr = extract_untouched_glyph_pool(auth_im, rec, fonts_map)
        precomputed[sid] = (auth_src, auth_im, glyph_pool, field_pos, blank_yr)
        compat_flags[sid] = can_copy_move_sample(glyph_pool, rec["tampered_fields"])

    assignments = assign_balanced_methods(by_template, compat_flags, seed=20261107)

    # Pre-build balanced QF pair cycle and submethod cycle for the 75 double_jpeg samples
    rng_global = random.Random(20261107)
    dj_configs = []
    for i in range(75):
        qf_pre, qf_post = JPEG_QF_PAIRS[i % len(JPEG_QF_PAIRS)]
        sub_m = "copy_move" if (i % 2 == 0) else "splice_font"
        dj_configs.append((qf_pre, qf_post, sub_m))
    rng_global.shuffle(dj_configs)
    dj_cursor = 0

    v3_records = []
    method_counts = {m: 0 for m in METHODS}

    for idx_out, rec in enumerate(selected_samples, start=1):
        sid = rec["sample_id"]
        method = assignments[sid]
        method_counts[method] += 1
        auth_src, auth_im, glyph_pool, field_pos, blank_yr = precomputed[sid]
        rng_sample = random.Random(rec["seed"] + 3333333)

        source_bbox = None
        jpeg_qf_pre = None
        jpeg_qf_post = None
        forgery_detail = {}

        if method == "copy_move":
            tamp_im, new_fields, src_boxes = apply_copy_move_edits(
                auth_im, rec, glyph_pool, field_pos, blank_yr, fonts_map, rng_sample
            )
            source_bbox = src_boxes
            forgery_detail = {"submethod": "intra_receipt_glyph_crop"}

        elif method == "splice_font":
            tamp_im, new_fields, detail = apply_splice_text_edits(
                auth_im, rec, field_pos, blank_yr, fonts_map, rng_sample, use_alt_font=True
            )
            forgery_detail = detail

        elif method == "splice_same_font":
            tamp_im, new_fields, detail = apply_splice_text_edits(
                auth_im, rec, field_pos, blank_yr, fonts_map, rng_sample, use_alt_font=False
            )
            forgery_detail = detail

        elif method == "double_jpeg":
            qf_pre, qf_post, sub_m = dj_configs[dj_cursor]
            dj_cursor += 1
            jpeg_qf_pre = qf_pre
            jpeg_qf_post = qf_post

            # 1) Save authentic as JPEG QF_pre
            a_qf1 = jpeg_roundtrip(auth_im, qf_pre)
            # 2) Apply copy_move or splice_font on JPEG(QF_pre) image
            if sub_m == "copy_move":
                t_mid, mid_fields, src_boxes = apply_copy_move_edits(
                    a_qf1, rec, glyph_pool, field_pos, blank_yr, fonts_map, rng_sample
                )
                source_bbox = src_boxes
                forgery_detail = {"double_jpeg_submethod": "copy_move"}
            else:
                t_mid, mid_fields, detail = apply_splice_text_edits(
                    a_qf1, rec, field_pos, blank_yr, fonts_map, rng_sample, use_alt_font=True
                )
                forgery_detail = {"double_jpeg_submethod": "splice_font", **detail}

            # 3) Save edited receipt as JPEG QF_post (different QF)
            t_qf2 = jpeg_roundtrip(t_mid, qf_post)

            # Composite 8x8-DCT-grid-aligned double-JPEG blocks onto authentic canvas so:
            # - Inside mask: genuine 8x8 DCT blocks with (QF_pre -> edit -> QF_post) double-JPEG history
            # - Outside mask: authentic pixels stay strictly unchanged (diff_outside_mask_px == 0)
            tamp_im = auth_im.copy()
            new_fields = []
            w, h = auth_im.size
            for mf in mid_fields:
                bx0, by0, bx1, by1 = mf["bbox"]
                mcu_x0 = max(0, ((bx0 - 4) // 8) * 8)
                mcu_y0 = max(0, ((by0 - 4) // 8) * 8)
                mcu_x1 = min(w, ((bx1 + 5 + 7) // 8) * 8)
                mcu_y1 = min(h, ((by1 + 5 + 7) // 8) * 8)
                dj_patch = t_qf2.crop((mcu_x0, mcu_y0, mcu_x1, mcu_y1))
                tamp_im.paste(dj_patch, (mcu_x0, mcu_y0))
                nf = copy.deepcopy(mf)
                nf["bbox"] = [mcu_x0, mcu_y0, mcu_x1 - 1, mcu_y1 - 1]
                new_fields.append(nf)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Build pixel mask = union of every modified patch bbox (inclusive coordinates)
        mask_im = Image.new("L", auth_im.size, 0)
        draw_m = ImageDraw.Draw(mask_im)
        for nf in new_fields:
            draw_m.rectangle(nf["bbox"], fill=255)

        # Strict 3-channel RGB diff verification (diff ⊆ mask => diff_outside_mask_px == 0)
        diff_im = compute_strict_rgb_diff(auth_im, tamp_im)
        outside_im = ImageChops.subtract(diff_im, mask_im)
        outside_px = outside_im.histogram()[255]
        diff_px = diff_im.histogram()[255]
        mask_px = mask_im.histogram()[255]

        if outside_px != 0:
            raise ValueError(
                f"Validation failed on {sid} ({method}): "
                f"{outside_px} RGB diff pixels outside mask at {outside_im.getbbox()}"
            )
        assert diff_px > 0, f"{sid} ({method}): diff_px == 0!"
        assert mask_px >= diff_px, f"{sid} ({method}): mask_px < diff_px!"

        # Reuse V2 authentic PNG byte-for-byte
        auth_dst = os.path.join(auth_out, f"{sid}_authentic.png")
        tamp_dst = os.path.join(tamp_out, f"{sid}_tampered.png")
        mask_dst = os.path.join(mask_out, f"{sid}_mask.png")

        shutil.copy2(auth_src, auth_dst)
        tamp_im.save(tamp_dst, optimize=True)
        mask_im.save(mask_dst, optimize=True)

        v3_meta = copy.deepcopy(rec)
        v3_meta["tampered_fields"] = new_fields
        v3_meta["n_regions"] = len(new_fields)
        v3_meta["forgery_method"] = method
        v3_meta["source_bbox"] = source_bbox
        v3_meta["jpeg_qf_pre"] = jpeg_qf_pre
        v3_meta["jpeg_qf_post"] = jpeg_qf_post
        v3_meta["forgery_detail"] = forgery_detail
        v3_meta["mask_px"] = mask_px
        v3_meta["diff_px"] = diff_px
        v3_meta["diff_outside_mask_px"] = outside_px
        v3_meta["mask_covers_diff"] = 1.0
        v3_meta["generator_version"] = "v3"
        v3_meta["authentic_file"] = f"authentic/{sid}_authentic.png"
        v3_meta["tampered_file"] = f"tampered/{sid}_tampered.png"
        v3_meta["mask_file"] = f"masks/{sid}_mask.png"
        v3_records.append(v3_meta)

        if idx_out % 50 == 0 or idx_out == 300:
            print(
                f"  -> Đã xong {idx_out}/300 mẫu ({sid} | {rec['template']} | {method}) "
                f"Diff={diff_px}px Mask={mask_px}px Outside={outside_px}"
            )

    manifest_jsonl = os.path.join(out_dir, "manifest.jsonl")
    metadata_json = os.path.join(out_dir, "metadata.json")
    with open(manifest_jsonl, "w", encoding="utf-8") as f:
        for r in v3_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(metadata_json, "w", encoding="utf-8") as f:
        json.dump(v3_records, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_t
    print("\n" + "=" * 70)
    print(f"🎉 HOÀN THÀNH 300 MẪU DATASET V3 REALISTIC TRONG {elapsed:.2f} GIÂY!")
    print(f"📊 Phân bổ phương pháp: {method_counts}")
    print(f"📁 Authentic: {len(os.listdir(auth_out))} | Tampered: {len(os.listdir(tamp_out))} | Masks: {len(os.listdir(mask_out))}")
    print(f"📋 Metadata:  {metadata_json}")
    print("=" * 70)


if __name__ == "__main__":
    main()
