import sys
import os
import time
import json
import base64
import random
import hashlib
import platform
import argparse
import tempfile
import subprocess
import urllib.request
import asyncio
import websockets
import numpy as np
from PIL import Image


class ValidationError(Exception):
    """Raised when a rendered sample fails quality assertions."""
    pass

sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "templates", "structure_card.html").replace("\\", "/")
IMAGES_DIR = os.path.join(SCRIPT_DIR, "images")
MANIFEST_PATH = os.path.join(SCRIPT_DIR, "manifest.jsonl")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

VIETNAMESE_LAST_NAMES = [
    "NGUYEN", "TRAN", "LE", "PHAM", "HOANG", "VU", "VO", 
    "DANG", "BUI", "DO", "HO", "NGO", "DUONG", "LY"
]
VIETNAMESE_MIDDLE_NAMES = [
    "VAN", "THI", "DINH", "DUC", "QUANG", "NGOC", "HOANG", "THAO", "HUY", "MINH"
]
VIETNAMESE_FIRST_NAMES = [
    "AN", "BINH", "CUONG", "DUNG", "GIANG", "HAI", "HIEU", "HUY", 
    "KHANH", "LINH", "MINH", "NAM", "PHONG", "QUAN", "SON", "TAM", 
    "THANG", "TUNG", "TUAN", "VY"
]

SAMPLE_MESSAGES = [
    "Tien an trua",
    "Chuyen tien hoc phi hoc ky 1",
    "Thanh toan tien thue nha thang 9",
    "Tra tien mua sach vo va dung cu hoc tap",
    "Chuc mung sinh nhat vui ve hanh phuc nhe",
    "Gui tien tieu vat tuan nay cho em",
    "Thanh toan hop dong dich vu phan mem so 2026",
    "Chuyen tien mua qua bieu gia dinh",
    "Thanh toan tien dien nuoc va internet thang 9",
    "Tien dong quy lop va lien hoan cuoi tuan"
]

BANK_VARIANTS = [
    "V-DigiBank Digital",
    "V-DigiBank Pay",
    "V-DigiBank Premium"
]

def generate_transaction_data(seed: int, theme: str = None):
    rng = random.Random(seed)
    
    # Tiered amount
    tier = rng.random()
    if tier < 0.30:
        amount_val = rng.randint(1, 50) * 10000
    elif tier < 0.80:
        amount_val = rng.randint(20, 1000) * 50000
    else:
        amount_val = rng.randint(100, 999) * 1000000
        
    amount_str = f"-{amount_val:,.0f} VND"
    
    # Recipient name (2 to 4 words)
    words_count = rng.choice([2, 3, 4])
    last = rng.choice(VIETNAMESE_LAST_NAMES)
    first = rng.choice(VIETNAMESE_FIRST_NAMES)
    if words_count == 2:
        name = f"{last} {first}"
    elif words_count == 3:
        mid = rng.choice(VIETNAMESE_MIDDLE_NAMES)
        name = f"{last} {mid} {first}"
    else:
        mid1 = rng.choice(VIETNAMESE_MIDDLE_NAMES)
        mid2 = rng.choice(VIETNAMESE_MIDDLE_NAMES)
        name = f"{last} {mid1} {mid2} {first}"
        
    account_num = "".join([str(rng.randint(0, 9)) for _ in range(rng.randint(9, 12))])
    bank_name = rng.choice(BANK_VARIANTS)
    
    # Timestamp
    day = rng.randint(1, 28)
    month = rng.randint(1, 12)
    hour = rng.randint(6, 23)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    time_str = f"{hour:02d}:{minute:02d}:{second:02d} - {day:02d}/{month:02d}/2026"
    status_time = f"{hour:02d}:{minute:02d}"
    
    tx_code = f"FT26{month:02d}{day:02d}" + "".join([str(rng.randint(0, 9)) for _ in range(6)])
    message = rng.choice(SAMPLE_MESSAGES)
    
    if theme is None:
        theme = "dark" if (seed % 2 == 0) else "light"
        
    return {
        "theme": theme,
        "statusbar_time": status_time,
        "amount": amount_str,
        "status_text": "Giao dịch thành công",
        "timestamp": time_str,
        "recipient_name": name,
        "account_number": account_num,
        "bank_name": bank_name,
        "tx_code": tx_code,
        "message": message
    }


class ChromeCDPRenderer:
    def __init__(self, port=9222):
        self.port = port
        self.proc = None
        self.user_data_dir = tempfile.mkdtemp(prefix="chrome_cdp_render_")
        self.ws = None
        self.msg_id = 0
        self.browser_version = "Unknown"

    def start(self):
        cmd = [
            CHROME_PATH,
            "--headless=new",
            f"--remote-debugging-port={self.port}",
            "--remote-allow-origins=*",
            f"--user-data-dir={self.user_data_dir}",
            "--disable-extensions",
            "--disable-gpu",
            "--disable-lcd-text",
            "--force-color-profile=srgb",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.2)
        
        # Connect
        resp = urllib.request.urlopen(f"http://localhost:{self.port}/json")
        tabs = json.loads(resp.read().decode("utf-8"))
        page_tabs = [t for t in tabs if t.get("type") == "page"]
        assert len(page_tabs) > 0, "No page tab available"
        self.ws_url = page_tabs[0]["webSocketDebuggerUrl"]

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=50*1024*1024)
        ver_res = await self.call("Browser.getVersion")
        self.browser_version = ver_res.get("product", "Chrome/Unknown")
        await self.call("Page.enable")
        await self.call("Emulation.setDeviceMetricsOverride", {
            "width": 360, "height": 800, "deviceScaleFactor": 3, "mobile": True
        })

    async def call(self, method, params=None):
        self.msg_id += 1
        mid = self.msg_id
        payload = {"id": mid, "method": method}
        if params:
            payload["params"] = params
        await self.ws.send(json.dumps(payload))
        while True:
            raw = await self.ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"CDP Error in {method}: {msg['error']}")
                return msg.get("result", {})

    async def render_bill(self, sample_id: str, seed: int, data: dict, output_path: str):
        # 1. Navigate
        await self.call("Page.navigate", {"url": f"file:///{TEMPLATE_PATH}"})
        
        # Wait ready
        for _ in range(50):
            r = await self.call("Runtime.evaluate", {"expression": "document.readyState", "returnByValue": True})
            if r.get("result", {}).get("value") == "complete":
                break
            await asyncio.sleep(0.05)
            
        # 2. Set theme
        await self.call("Runtime.evaluate", {
            "expression": f"window.setTheme('{data['theme']}')"
        })
        
        # 3. Populate data
        data_json_str = json.dumps(data, ensure_ascii=False)
        await self.call("Runtime.evaluate", {
            "expression": f"window.populateData({data_json_str})"
        })
        
        await asyncio.sleep(0.2)
        
        # 4. Extract BBoxes & Check Overflow
        res = await self.call("Runtime.evaluate", {
            "expression": "JSON.stringify(window.getBBoxes(3))",
            "returnByValue": True
        })
        meta_extracted = json.loads(res["result"]["value"])
        
        # Check overflow
        if meta_extracted.get("has_overflow"):
            print(f"Warning: Overflow detected for seed {seed}. Re-sampling message...")
            data["message"] = "Chuyen tien thanh toan"
            await self.call("Runtime.evaluate", {
                "expression": f"window.populateData({json.dumps(data, ensure_ascii=False)})"
            })
            await asyncio.sleep(0.1)
            res = await self.call("Runtime.evaluate", {
                "expression": "JSON.stringify(window.getBBoxes(3))",
                "returnByValue": True
            })
            meta_extracted = json.loads(res["result"]["value"])
            
        # 5. Capture screenshot
        shot = await self.call("Page.captureScreenshot", {
            "format": "png",
            "clip": {"x": 0, "y": 0, "width": 360, "height": 800, "scale": 1}
        })
        img_bytes = base64.b64decode(shot["data"])
        with open(output_path, "wb") as f:
            f.write(img_bytes)
            
        # 6. Assertions & Validation
        img = Image.open(output_path).convert("RGB")
        arr = np.array(img)
        h_px, w_px, _ = arr.shape
        if (w_px, h_px) != (1080, 2400):
            raise ValidationError(f"Invalid image size: {w_px}x{h_px}")
        
        # Boundary & Ink Box assertions
        for field, info in meta_extracted["elements"].items():
            b = info["bbox"]
            if not (0 <= b["xmin"] < b["xmax"] <= 1080):
                raise ValidationError(f"X boundary failed for {field}: {b}")
            if not (0 <= b["ymin"] < b["ymax"] <= 2400):
                raise ValidationError(f"Y boundary failed for {field}: {b}")
            
            if info["type"] == "text":
                # Per-line Ink Box for message (uses line_rects)
                if field == "message" and "line_rects" in info and len(info["line_rects"]) > 0:
                    for li, lr in enumerate(info["line_rects"]):
                        lc = arr[lr["ymin"]:lr["ymax"], lr["xmin"]:lr["xmax"]]
                        if lc.size == 0:
                            raise ValidationError(f"Empty line_rect[{li}] for {field}: {lr}")
                        corners = np.vstack([lc[0, 0], lc[0, -1], lc[-1, 0], lc[-1, -1]])
                        bg = np.median(corners, axis=0)
                        diff = np.abs(lc.astype(float) - bg).max(axis=2)
                        ink_mask = diff > 25
                        if ink_mask.sum() == 0:
                            raise ValidationError(f"No ink in message line {li}: {lr}")
                        ys, xs = np.where(ink_mask)
                        ink_w = xs.max() - xs.min() + 1
                        ink_h = ys.max() - ys.min() + 1
                        w_ratio = ink_w / max(lr["w"], 1)
                        h_ratio = ink_h / max(lr["h"], 1)
                        if w_ratio < 0.60:
                            raise ValidationError(f"Width ratio failed for {field} line {li}: {w_ratio:.2f} < 0.60")
                        if h_ratio < 0.50:
                            raise ValidationError(f"Height ratio failed for {field} line {li}: {h_ratio:.2f} < 0.50")
                else:
                    # Single-line text fields
                    crop = arr[b["ymin"]:b["ymax"], b["xmin"]:b["xmax"]]
                    corners = np.vstack([crop[0, 0], crop[0, -1], crop[-1, 0], crop[-1, -1]])
                    bg = np.median(corners, axis=0)
                    diff = np.abs(crop.astype(float) - bg).max(axis=2)
                    ink_mask = diff > 25
                    if ink_mask.sum() == 0:
                        raise ValidationError(f"No ink found in text field {field}")
                    ys, xs = np.where(ink_mask)
                    ink_w = xs.max() - xs.min() + 1
                    ink_h = ys.max() - ys.min() + 1
                    w_ratio = ink_w / b["w"]
                    h_ratio = ink_h / b["h"]
                    if w_ratio < 0.80:
                        raise ValidationError(f"Width ratio failed for {field}: {w_ratio:.2f} < 0.80")
                    if h_ratio < 0.50:
                        raise ValidationError(f"Height ratio failed for {field}: {h_ratio:.2f} < 0.50")

        # 7. Hashes
        sha256_pixels = hashlib.sha256(arr.tobytes()).hexdigest()
        sha256_file = hashlib.sha256(img_bytes).hexdigest()
        
        record = {
            "sample_id": sample_id,
            "seed": seed,
            "theme": data["theme"],
            "device_scale_factor": 3,
            "viewport_css": [360, 800],
            "image_size_px": [1080, 2400],
            "image_path": os.path.relpath(output_path, SCRIPT_DIR).replace("\\", "/"),
            "sha256_pixels": sha256_pixels,
            "sha256_file": sha256_file,
            "environment": {
                "browser_name": "Google Chrome",
                "browser_version": self.browser_version,
                "platform": platform.platform(),
                "python_version": sys.version.split()[0]
            },
            "elements": meta_extracted["elements"]
        }
        return record

    async def close(self):
        if self.ws:
            await self.ws.close()
        if self.proc:
            self.proc.terminate()
            self.proc.wait()


async def main():
    parser = argparse.ArgumentParser(description="Pristine Synthetic Bill Generator")
    parser.add_argument("--count", type=int, default=5, help="Number of pristine bills to generate")
    parser.add_argument("--start-seed", type=int, default=42, help="Starting seed")
    parser.add_argument("--port", type=int, default=9224, help="Chrome debugging port")
    args = parser.parse_args()

    os.makedirs(IMAGES_DIR, exist_ok=True)
    failures_path = os.path.join(SCRIPT_DIR, "failures.jsonl")
    renderer = ChromeCDPRenderer(port=args.port)
    renderer.start()
    
    print(f"=== PRISTINE BILL GENERATOR (V-DigiBank) ===")
    print(f"Target count: {args.count} | Start seed: {args.start_seed} | Output: {IMAGES_DIR}")
    
    records = []
    failures = []
    total_attempted = 0
    try:
        await renderer.connect()
        for i in range(args.count):
            seed = args.start_seed + i
            sample_id = f"pristine_{i+1:04d}"
            output_png = os.path.join(IMAGES_DIR, f"{sample_id}.png")
            total_attempted += 1
            
            data = generate_transaction_data(seed)
            try:
                rec = await renderer.render_bill(sample_id, seed, data, output_png)
                records.append(rec)
                print(f"[{len(records)}/{args.count}] {sample_id} ({data['theme'].upper()}) -> {data['amount']} to {data['recipient_name']} | sha256_px: {rec['sha256_pixels'][:12]}...")
            except ValidationError as e:
                reason = str(e)
                failures.append({"sample_id": sample_id, "seed": seed, "reason": reason})
                print(f"[SKIP] {sample_id} (seed={seed}): {reason}")
                # Clean up failed image
                if os.path.exists(output_png):
                    os.remove(output_png)
                continue
            
        # Write manifest
        with open(MANIFEST_PATH, "a", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        
        # Write failures log
        if failures:
            with open(failures_path, "a", encoding="utf-8") as f:
                for fail in failures:
                    f.write(json.dumps(fail, ensure_ascii=False) + "\n")
        
        # Summary
        fail_rate = len(failures) / total_attempted if total_attempted > 0 else 0
        print(f"\n=== GENERATION SUMMARY ===")
        print(f"Attempted: {total_attempted} | Passed: {len(records)} | Failed: {len(failures)} | Failure rate: {fail_rate:.1%}")
        if failures:
            print(f"Failure log: {failures_path}")
            for f in failures:
                print(f"  - {f['sample_id']}: {f['reason']}")
        if fail_rate > 0.05:
            print(f"\n[WARNING] Failure rate {fail_rate:.1%} exceeds 5% threshold!")
            print(f"This may indicate a systematic template issue. Review failure reasons above.")
        else:
            print(f"Manifest saved to: {MANIFEST_PATH}")
    finally:
        await renderer.close()

if __name__ == "__main__":
    asyncio.run(main())
