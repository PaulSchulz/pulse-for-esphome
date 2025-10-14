
#!/usr/bin/env python3

#!/usr/bin/env python3
#
# Generates a PDF document containing the access URL and a QR code
# for a Pulse for ESPHome device, based on its MAC address.
#
# Required Libraries: fpdf2, qrcode, Pillow, Jinja2
# Install using: pip install fpdf2 qrcode pillow jinja2

import sys
import os
import re
import tempfile
from fpdf import FPDF
from jinja2 import Environment
import qrcode
from qrcode.image.pil import PilImage

# --- Configuration ---

# The text template for the PDF content, using Jinja2 placeholders.
PDF_TEMPLATE = """

Congratulations!

You have gotten your hands on a Pulse for ESPHome device.

You can configure the WiFi on the device by using the Improv webpage.

https://www.improv-wifi.com/

Once it has been connected to the Wifi network via Improv, you should be able to
connect to it with any device on the same WiFi network by using the following
URL, or by scanning the QRCode.

{{ url }}
"""

# The prefix for the mDNS address
DEVICE_NAME_PREFIX = "pulse-for-esphome-"

# Default MAC address for testing purposes
DEFAULT_MAC = "11:22:33:44:55:66"

# PDF styling constants
FONT_NAME = "Helvetica"
QR_CODE_SIZE_MM = 60
MARGIN = 20

# --- Core Functions ---

def clean_and_extract_mac_suffix(mac_address: str) -> str:
    """
    Cleans the MAC address and extracts the last 3 bytes (6 characters).

    Args:
        mac_address: The input MAC string (e.g., '12:34:56:78:90:AB').

    Returns:
        The last 6 hex characters in uppercase (e.g., '7890AB').
    """
    # Remove all non-hex characters (colons, dashes, etc.)
    cleaned_mac = re.sub(r'[^0-9a-fA-F]', '', mac_address).upper()

    if len(cleaned_mac) < 6:
        raise ValueError("MAC address must contain at least 6 hex characters.")

    # Extract the last 6 characters (last 3 bytes)
    mac_suffix = cleaned_mac[-6:]

    # Format for hostname (using dashes as per common convention, though not strictly required)
    return mac_suffix

class CustomPDF(FPDF):
    """Custom FPDF class to handle text rendering."""
    def header(self):
        # We don't need a header for this simple document
        pass

    def footer(self):
        # We don't need a footer
        pass

    def text_block(self, text: str):
        """Prints a multi-line block of text with proper line breaks."""
        self.set_font(FONT_NAME, size=12)
        # Split the text into paragraphs and print them
        for paragraph in text.split('\n\n'):
            if paragraph.strip():
                # MultiCell is used here to handle automatic line breaks
                self.multi_cell(0, 8, paragraph.strip(), align='L')
                self.ln(5) # Add extra space between paragraphs

def generate_access_pdf(mac_address: str):
    """
    Generates the PDF document including the text template and QR code.
    """
    temp_filename = None
    try:
        # 1. Prepare Data
        mac_suffix = clean_and_extract_mac_suffix(mac_address)
        url = f"http://{DEVICE_NAME_PREFIX}{mac_suffix}.local"
        pdf_output_filename = f"pulse_esphome_access_{mac_suffix}.pdf"

        # 2. Render the text template using Jinja2
        template = Environment().from_string(PDF_TEMPLATE)
        rendered_text = template.render(
            mac_suffix=mac_suffix,
            url=url
        )

        # 3. Create QR Code and save it to a temporary file
        print(f"Generating temporary QR code for URL: {url}")
        qr = qrcode.QRCode(
            version=1,
#            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)

        # Use tempfile to create a guaranteed unique filename for the image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_filename = tmp.name
            img.save(temp_filename, 'PNG')

        # 4. Generate PDF
        pdf = CustomPDF('P', 'mm', 'A4')
        pdf.set_auto_page_break(auto=True, margin=MARGIN)
        pdf.add_page()
        pdf.set_margins(MARGIN,MARGIN,MARGIN)

        # Print the rendered text
        pdf.text_block(rendered_text)
        pdf.ln(10)

        # Calculate position for the QR code (centered on the page)
        page_width = pdf.w - 2 * MARGIN
        qr_x = pdf.get_x() + (page_width - QR_CODE_SIZE_MM) / 2

        # Add the QR code image using the temporary file path
        pdf.image(temp_filename, x=qr_x, y=pdf.get_y(), w=QR_CODE_SIZE_MM, h=QR_CODE_SIZE_MM)
        pdf.ln(QR_CODE_SIZE_MM + 10)

        # Output the PDF
        pdf.output(pdf_output_filename)
        print(f"\nSuccessfully created PDF: {pdf_output_filename}")

    except ValueError as e:
        print(f"Error processing MAC address: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # 5. Clean up the temporary file
        if temp_filename and os.path.exists(temp_filename):
            print(f"Cleaning up temporary file: {temp_filename}")
            os.unlink(temp_filename)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        mac = sys.argv[1]
    else:
        mac = DEFAULT_MAC
        print(f"No MAC address provided. Using default for testing: {DEFAULT_MAC}")
        print(f"To use a custom MAC, run: python {sys.argv[0]} 12:34:56:78:90:AB")

    try:
        generate_access_pdf(mac)
    except Exception as e:
        # Catch any failure during the final execution
        print(f"Script execution failed: {e}")
