#!/usr/bin/env python3
#
# Generates a PDF containing:
#  - The access URL (and QR code) for a Pulse for ESPHome device
#  - A QR code for the Improv WiFi setup page
#
# Uses WeasyPrint for HTML → PDF conversion.
#
# Required:
#   pip install weasyprint jinja2 qrcode pillow

import sys
import re
import io
import base64
import qrcode
from qrcode.image.pil import PilImage
from jinja2 import Environment
from weasyprint import HTML

DEVICE_NAME_PREFIX = "pulse-for-esphome-"
DEFAULT_MAC = "11:22:33:44:55:66"
IMPROV_URL = "https://www.improv-wifi.com/"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <style>
      body {
        font-family: Helvetica, Arial, sans-serif;
        margin: 40px;
        line-height: 1.5;
      }
      h1 {
        color: #333;
        text-align: center;
      }
      p {
        margin-bottom: 15px;
      }
      .section {
        margin-top: 40px;
        text-align: center;
      }
      .qr {
        width: 200px;
        height: 200px;
      }
      .url {
        font-weight: bold;
        margin-top: 10px;
        word-break: break-all;
      }
      .label {
        font-size: 1.1em;
        margin-bottom: 10px;
      }
    </style>
  </head>
  <body>
    <h1>Pulse for ESPHome Access Details</h1>

    <p>
      You have gotten your hands on a <b>Pulse for ESPHome</b> device.
    </p>

    <p>
      You can configure the WiFi on the device by using the QRCode or Link below.
    </p>

    <div class="section">
      <div class="label">Improv Wi-Fi Setup</div>
      <img class="qr" src="data:image/png;base64,{{ qr_improv_base64 }}" alt="Improv QR" />
      <div class="url">{{ improv_url }}</div>
    </div>

    <p>
      Once it has been connected to the WiFi network you should be able to
      connect to it with any device on the same WiFi network by scanning the QR code below,
or    using the Link:
    </p>

    <div class="section">
      <div class="label">Device Access URL</div>
      <img class="qr" src="data:image/png;base64,{{ qr_device_base64 }}" alt="Device QR" />
      <div class="url">{{ device_url }}</div>
    </div>
  </body>
</html>
"""

def clean_and_extract_mac_suffix(mac_address: str) -> str:
    cleaned_mac = re.sub(r'[^0-9a-fA-F]', '', mac_address).upper()
    if len(cleaned_mac) < 6:
        raise ValueError("MAC address must contain at least 6 hex characters.")
    return cleaned_mac[-6:]

def make_qr_base64(data: str) -> str:
    """Generate a QR code for the given data and return it as base64."""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def generate_access_pdf(mac_address: str):
    mac_suffix = clean_and_extract_mac_suffix(mac_address)
    device_url = f"http://{DEVICE_NAME_PREFIX}{mac_suffix}.local"
    pdf_output_filename = f"pulse_esphome_access_{mac_suffix}.pdf"

    # Generate QR codes
    qr_device_base64 = make_qr_base64(device_url)
    qr_improv_base64 = make_qr_base64(IMPROV_URL)

    # Render HTML template
    template = Environment().from_string(HTML_TEMPLATE)
    html_content = template.render(
        device_url=device_url,
        qr_device_base64=qr_device_base64,
        improv_url=IMPROV_URL,
        qr_improv_base64=qr_improv_base64
    )

    # Convert HTML → PDF
    HTML(string=html_content).write_pdf(pdf_output_filename)
    print(f"✅ Created {pdf_output_filename}")

if __name__ == "__main__":
    mac = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MAC
    if len(sys.argv) == 1:
        print(f"No MAC provided, using default: {DEFAULT_MAC}")
    generate_access_pdf(mac)
