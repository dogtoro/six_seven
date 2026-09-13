import base64
import os

font_dir = r"d:\grp_proj\six_seven\forensic_dataset\step1_pristine_generator\fonts"
with open(os.path.join(font_dir, "Inter-Regular.woff2"), "rb") as f:
    b64_reg = base64.b64encode(f.read()).decode("utf-8")
with open(os.path.join(font_dir, "Inter-Bold.woff2"), "rb") as f:
    b64_bold = base64.b64encode(f.read()).decode("utf-8")

html_template = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=360, height=800, initial-scale=1.0">
<title>VLB Digibank Transaction Receipt</title>
<link rel="stylesheet" id="theme-style" href="../layouts/theme_dark.css">
<style>
@font-face {
  font-family: 'V-Custom-Sans';
  src: url('data:font/woff2;base64,{{B64_REG}}') format('woff2');
  font-weight: 400;
  font-style: normal;
}
@font-face {
  font-family: 'V-Custom-Sans';
  src: url('data:font/woff2;base64,{{B64_BOLD}}') format('woff2');
  font-weight: 700;
  font-style: normal;
}
:root {
  --bg-app: #071913;
  --bg-gradient: radial-gradient(circle at 50% 12%, #0e3b2e 0%, #082119 35%, #051318 75%, #030b0e 100%);
  --bg-card: rgba(13, 27, 42, 0.72);
  --border-card: rgba(255, 255, 255, 0.07);
  --text-muted: #8ea4b0;
  --text-main: #ffffff;
  --text-heading: #a2e838;
  --accent-green: #9fe830;
  --accent-green-dark: #082116;
  --amount-color: #a2e838;
  --currency-color: #71a884;
  --datetime-color: #a5c1cb;
  --divider: rgba(255, 255, 255, 0.05);
  --btn-primary-bg: #b6f542;
  --btn-primary-text: #0b1a14;
  --status-bar-color: #ffffff;
  --toggle-bg: #1c2635;
  --toggle-knob: #ffffff;
  --home-btn-bg: rgba(255, 255, 255, 0.08);
  --home-btn-icon: #10b981;
}
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: 'V-Custom-Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
html, body {
  width: 360px;
  height: 800px;
  max-width: 360px;
  max-height: 800px;
  overflow: hidden;
  position: relative;
}
body {
  background: var(--bg-gradient);
  color: var(--text-main);
  display: flex;
  flex-direction: column;
  padding: 0 16px;
}

/* Background Dong Son drum circular watermark */
.bg-drum-pattern {
  position: absolute;
  top: -80px;
  left: 50%;
  transform: translateX(-50%);
  width: 380px;
  height: 380px;
  border-radius: 50%;
  border: 1px dashed rgba(255, 255, 255, 0.035);
  pointer-events: none;
  box-shadow:
    0 0 0 35px rgba(255, 255, 255, 0.015),
    0 0 0 75px rgba(255, 255, 255, 0.01),
    0 0 0 115px rgba(255, 255, 255, 0.007);
}

/* Status Bar */
.status-bar {
  height: 36px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 700;
  padding: 8px 6px 0;
  color: var(--status-bar-color);
  z-index: 2;
}
.status-bar-icons {
  display: flex;
  align-items: center;
  gap: 5px;
}

/* App Bar / Header */
.app-header {
  height: 46px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
  z-index: 2;
}
.vcb-logo-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.4px;
  color: #ffffff;
}
.home-btn {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--home-btn-bg);
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

/* Hero Section */
.hero-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 0 14px 0;
  text-align: center;
  z-index: 2;
}
.status-icon-circle {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background-color: var(--accent-green);
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 8px;
  box-shadow: 0 4px 16px rgba(159, 232, 48, 0.25);
}
.status-title {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 4px;
  letter-spacing: -0.2px;
}
.amount-display {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 5px;
  line-height: 1.1;
  margin-top: 2px;
}
.amount-number {
  font-size: 28px;
  font-weight: 700;
  color: var(--amount-color);
  letter-spacing: -0.5px;
}
.amount-currency {
  font-size: 13px;
  font-weight: 600;
  color: var(--currency-color);
  margin-top: 2px;
}
.datetime-display {
  font-size: 12.5px;
  font-weight: 400;
  color: var(--datetime-color);
  margin-top: 5px;
  letter-spacing: -0.1px;
}

/* Receipt Details Card */
.receipt-card {
  background-color: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 18px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 2;
}
.field-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  min-height: 32px;
}
.field-label {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-muted);
  flex-shrink: 0;
}
.field-value {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-main);
  text-align: right;
  word-break: break-word;
}

/* Bank Row Styling */
.bank-row {
  align-items: flex-start;
}
.bank-value-group {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.bank-top-line {
  display: flex;
  align-items: center;
  gap: 6px;
}
.bank-logo-badge {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 9px;
  font-weight: 700;
  color: #ef4444;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
.bank-logo-badge svg {
  width: 13px;
  height: 13px;
}
.bank-short {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-main);
}
.bank-full-sub {
  font-size: 11.5px;
  font-weight: 400;
  color: var(--text-muted);
  margin-top: 1px;
}

/* Multi-line Message Row */
.message-row {
  align-items: flex-start;
}
.message-container {
  max-width: 210px;
  text-align: right;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
  line-height: 18px;
  word-break: break-word;
}

/* Method Row */
.method-row {
  align-items: flex-start;
}
.method-value {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
  text-align: right;
  line-height: 17px;
}

/* Toggle Switch Row Below Card */
.toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 8px 6px;
  z-index: 2;
}
.toggle-label-text {
  font-size: 13.5px;
  font-weight: 400;
  color: var(--text-main);
}
.vcb-switch {
  width: 44px;
  height: 24px;
  border-radius: 24px;
  background-color: var(--toggle-bg);
  position: relative;
  transition: background-color 0.2s;
  cursor: pointer;
}
.vcb-switch-knob {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background-color: var(--toggle-knob);
  position: absolute;
  top: 3px;
  left: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s;
}

/* Bottom Action Button */
.button-section {
  margin-top: auto;
  margin-bottom: 22px;
  padding: 0 4px;
  z-index: 2;
}
.btn-vcb {
  width: 100%;
  height: 46px;
  border-radius: 23px;
  background-color: var(--btn-primary-bg);
  color: var(--btn-primary-text);
  font-size: 14.5px;
  font-weight: 700;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  box-shadow: 0 4px 18px rgba(182, 245, 66, 0.2);
}
</style>
</head>
<body>

  <!-- Decorative Dong Son drum circular watermark -->
  <div class="bg-drum-pattern"></div>

  <!-- Status Bar -->
  <div class="status-bar">
    <span id="statusbar_time">11:31</span>
    <div class="status-bar-icons">
      <!-- Signal bars -->
      <svg width="15" height="11" viewBox="0 0 15 11" fill="currentColor">
        <rect x="0" y="8" width="2.5" height="3" rx="0.5"/>
        <rect x="4" y="5.5" width="2.5" height="5.5" rx="0.5"/>
        <rect x="8" y="3" width="2.5" height="8" rx="0.5"/>
        <rect x="12" y="0" width="2.5" height="11" rx="0.5"/>
      </svg>
      <!-- 4G -->
      <span style="font-size: 11px; font-weight: 700; margin: 0 2px;">4G</span>
      <!-- Yellow Battery -->
      <svg width="22" height="11" viewBox="0 0 22 11" fill="none">
        <rect x="0.5" y="0.5" width="18" height="10" rx="3" stroke="currentColor" stroke-width="1"/>
        <rect x="2" y="2" width="13" height="7" rx="1.5" fill="#facc15"/>
        <path d="M20 3.5v4" stroke="currentColor" stroke-width="1" stroke-linecap="round"/>
      </svg>
    </div>
  </div>

  <!-- Header -->
  <div class="app-header">
    <div class="vcb-logo-title" data-field="header_brand" data-type="decorative">VLB Digibank</div>
    <div class="home-btn" data-field="header_home_btn" data-type="decorative">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--home-btn-icon)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>
    </div>
  </div>

  <!-- Hero Status -->
  <div class="hero-section">
    <div class="status-icon-circle" data-field="status_icon" data-type="decorative">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--accent-green-dark)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    </div>
    <div class="status-title"><span data-field="status_text" data-type="text" id="status_text_val">Giao dịch thành công!</span></div>
    <div class="amount-display">
      <span data-field="amount" data-type="text" id="amount_val">
        <span class="amount-number" id="amount_num_val">70,000</span>
        <span class="amount-currency" id="amount_cur_val">VND</span>
      </span>
    </div>
    <div class="datetime-display">
      <span data-field="timestamp" data-type="text" id="timestamp_val">11:31 Thứ Tư 26/08/2026</span>
    </div>
  </div>

  <!-- Details Card -->
  <div class="receipt-card" data-field="card_container" data-type="decorative">
    <div class="field-row">
      <span class="field-label">Tài khoản nhận</span>
      <span class="field-value"><span data-field="account_number" data-type="text" id="account_number_val">0967850076</span></span>
    </div>
    <div class="field-row">
      <span class="field-label">Tên người nhận</span>
      <span class="field-value"><span data-field="recipient_name" data-type="text" id="recipient_name_val">HOANG VIET DUC</span></span>
    </div>
    <div class="field-row bank-row">
      <span class="field-label">Ngân hàng nhận</span>
      <div class="bank-value-group">
        <div class="bank-top-line">
          <div class="bank-logo-badge" id="bank_badge_logo">
            <svg viewBox="0 0 24 24" fill="#ef4444"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          </div>
          <span class="bank-short" id="bank_short_val">MB</span>
        </div>
        <div class="bank-full-sub"><span data-field="bank_name" data-type="text" id="bank_name_val">Ngân hàng Quân Đội</span></div>
      </div>
    </div>
    <div class="field-row message-row">
      <span class="field-label">Nội dung</span>
      <div class="message-container" id="msg_container">
        <span data-field="message" data-type="text" id="message_val">NGUYEN DINH GIANG<br>chuyen tien</span>
      </div>
    </div>
    <div class="field-row">
      <span class="field-label">Phí chuyển tiền</span>
      <span class="field-value"><span data-field="fee" data-type="text" id="fee_val">Miễn phí</span></span>
    </div>
    <div class="field-row method-row">
      <span class="field-label">Hình thức chuyển</span>
      <div class="method-value">
        <span data-field="method" data-type="text" id="method_val">Chuyển tiền nhanh<br>24/7</span>
      </div>
    </div>
    <div class="field-row" style="border-bottom: none;">
      <span class="field-label">Mã giao dịch</span>
      <span class="field-value"><span data-field="tx_code" data-type="text" id="tx_code_val">15753979010</span></span>
    </div>
  </div>

  <!-- Toggle Switch Row -->
  <div class="toggle-row" data-field="save_template_row" data-type="decorative">
    <span class="toggle-label-text">Lưu mẫu chuyển tiền</span>
    <div class="vcb-switch" data-field="save_template_toggle" data-type="decorative">
      <div class="vcb-switch-knob"></div>
    </div>
  </div>

  <!-- Bottom Buttons -->
  <div class="button-section">
    <button class="btn-vcb" id="btn_action_val">Thực hiện giao dịch mới</button>
  </div>

  <!-- Coordinate & Range API Extraction Script -->
  <script id="extraction-script">
  window.getBBoxes = function(scaleFactor = 3) {
    const results = {};
    let hasOverflow = false;

    // Check message overflow assertion
    const msgContainer = document.getElementById('msg_container');
    if (msgContainer && msgContainer.scrollHeight > msgContainer.clientHeight) {
      hasOverflow = true;
    }

    document.querySelectorAll('[data-field]').forEach(el => {
      const field = el.getAttribute('data-field');
      const type = el.getAttribute('data-type') || 'text';

      if (type === 'text') {
        const range = document.createRange();
        range.selectNodeContents(el);
        const rect = range.getBoundingClientRect();

        const x = Math.round(rect.x * scaleFactor);
        const y = Math.round(rect.y * scaleFactor);
        const w = Math.round(rect.width * scaleFactor);
        const h = Math.round(rect.height * scaleFactor);

        const dataObj = {
          type: 'text',
          text: el.textContent.trim(),
          bbox: { x: x, y: y, w: w, h: h, xmin: x, ymin: y, xmax: x + w, ymax: y + h }
        };

        // Extract line_rects for multi-line fields
        if (field === 'message' || field === 'method') {
          const clientRects = range.getClientRects();
          const lineRects = [];
          for (let i = 0; i < clientRects.length; i++) {
            const cr = clientRects[i];
            const lx = Math.round(cr.x * scaleFactor);
            const ly = Math.round(cr.y * scaleFactor);
            const lw = Math.round(cr.width * scaleFactor);
            const lh = Math.round(cr.height * scaleFactor);
            lineRects.push({ x: lx, y: ly, w: lw, h: lh, xmin: lx, ymin: ly, xmax: lx + lw, ymax: ly + lh });
          }
          dataObj.line_rects = lineRects;
        }

        results[field] = dataObj;
      } else {
        const rect = el.getBoundingClientRect();
        const x = Math.round(rect.x * scaleFactor);
        const y = Math.round(rect.y * scaleFactor);
        const w = Math.round(rect.width * scaleFactor);
        const h = Math.round(rect.height * scaleFactor);

        results[field] = {
          type: 'decorative',
          bbox: { x: x, y: y, w: w, h: h, xmin: x, ymin: y, xmax: x + w, ymax: y + h }
        };
      }
    });

    return {
      elements: results,
      has_overflow: hasOverflow
    };
  };

  // Helper to switch theme dynamically
  window.setTheme = function(themeName) {
    const link = document.getElementById('theme-style');
    if (link) {
      link.href = `../layouts/theme_${themeName}.css`;
    }
  };

  // Helper to populate fields dynamically
  window.populateData = function(data) {
    for (const [key, val] of Object.entries(data)) {
      if (key === 'statusbar_time') {
        const el = document.getElementById('statusbar_time');
        if (el) el.textContent = val;
      } else if (key === 'amount') {
        // Parse raw amount
        const raw = String(val).replace(/[-+]/g, '').trim();
        const match = raw.match(/([0-9.,]+)\s*([A-Za-z]+)?/);
        const numEl = document.getElementById('amount_num_val');
        const curEl = document.getElementById('amount_cur_val');
        if (match) {
          if (numEl) numEl.textContent = match[1];
          if (curEl) curEl.textContent = match[2] || 'VND';
        } else {
          if (numEl) numEl.textContent = raw;
        }
      } else if (key === 'bank_name') {
        const el = document.getElementById('bank_name_val');
        const shortEl = document.getElementById('bank_short_val');
        const badgeEl = document.getElementById('bank_badge_logo');
        const str = String(val);
        if (str.includes('|')) {
          const parts = str.split('|');
          if (shortEl) shortEl.textContent = parts[0];
          if (el) el.textContent = parts[1];
        } else {
          // Detect known banks
          let shortName = 'VLB';
          let fullName = str;
          if (str.toUpperCase().includes('MB') || str.includes('Quân Đội')) {
            shortName = 'MB'; fullName = 'Ngân hàng Quân Đội';
          } else if (str.toUpperCase().includes('VLB') || str.toUpperCase().includes('VCB') || str.includes('Vietcombank') || str.includes('Ngoại Thương')) {
            shortName = 'VLB'; fullName = 'Ngân hàng Ngoại Thương VN';
          } else if (str.toUpperCase().includes('BIDV')) {
            shortName = 'BIDV'; fullName = 'Ngân hàng Đầu tư & Phát triển';
          } else if (str.toUpperCase().includes('TECHCOM') || str.toUpperCase().includes('TCB')) {
            shortName = 'Techcombank'; fullName = 'Ngân hàng Kỹ Thương';
          } else if (str.toUpperCase().includes('VIETIN')) {
            shortName = 'VietinBank'; fullName = 'Ngân hàng Công Thương';
          } else if (str.toUpperCase().includes('ACB')) {
            shortName = 'ACB'; fullName = 'Ngân hàng Á Châu';
          } else if (str.toUpperCase().includes('MOMO')) {
            shortName = 'MoMo'; fullName = 'Ví điện tử MoMo';
          } else if (str.toUpperCase().includes('DIGIBANK')) {
            shortName = 'V-DigiBank'; fullName = 'Ngân hàng số V-DigiBank';
          }
          if (shortEl) shortEl.textContent = shortName;
          if (el) el.textContent = fullName;
        }
      } else if (key === 'message') {
        const el = document.getElementById('message_val');
        if (el) {
          const text = String(val);
          el.innerHTML = text.replace(/\\n/g, '<br>');
        }
      } else if (key === 'method') {
        const el = document.getElementById('method_val');
        if (el) {
          el.innerHTML = String(val).replace(/\\n/g, '<br>');
        }
      } else {
        const el = document.getElementById(key + '_val');
        if (el) el.textContent = val;
      }
    }
  };
  </script>
</body>
</html>
"""

final_html = html_template.replace("{{B64_REG}}", b64_reg).replace("{{B64_BOLD}}", b64_bold)
target_path = r"d:\grp_proj\six_seven\forensic_dataset\step1_pristine_generator\templates\structure_card.html"
with open(target_path, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"Generated {target_path} successfully! Size: {os.path.getsize(target_path)} bytes")
