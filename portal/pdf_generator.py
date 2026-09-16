"""
Robust Headless Browser PDF Generator for Quantellix Automated EDA Reports.
Uses Chrome / Edge headless Blink engine for pixel-perfect CSS Grid & Flexbox rendering,
with automatic fallback to PyMuPDF.
"""

import os
import shutil
import subprocess
import logging
from typing import Optional

logger = logging.getLogger("quantellix.pdf_generator")

def find_browser_executable() -> Optional[str]:
    """Finds Chrome, Edge, or Chromium on the host system."""
    candidates = [
        # Standard 64-bit Chrome & Edge on Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        # Local AppData installations
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
        # PATH-based executables
        shutil.which("chrome"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("msedge"),
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None

def convert_html_to_pdf(html_path: str, pdf_path: str, timeout_sec: int = 30) -> bool:
    """
    Converts an HTML file to PDF using headless Chrome/Edge.
    Falls back to PyMuPDF if no browser is available or if execution fails.
    """
    html_abs = os.path.abspath(html_path)
    pdf_abs = os.path.abspath(pdf_path)

    if not os.path.exists(html_abs):
        logger.error(f"HTML source file not found: {html_abs}")
        return False

    os.makedirs(os.path.dirname(pdf_abs), exist_ok=True)

    browser = find_browser_executable()
    if browser:
        try:
            cmd = [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--no-pdf-header-footer",
                "--run-all-compositor-stages-before-draw",
                f"--print-to-pdf={pdf_abs}",
                html_abs
            ]
            logger.info(f"Generating PDF with headless browser: {browser}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            if os.path.exists(pdf_abs) and os.path.getsize(pdf_abs) > 1000:
                logger.info(f"Successfully generated PDF ({os.path.getsize(pdf_abs)} bytes) via {browser}")
                return True
            else:
                logger.warning(f"Browser PDF generation produced invalid file (code {result.returncode}): {result.stderr}")
        except Exception as e:
            logger.error(f"Headless browser PDF conversion failed: {e}")

    # Fallback to PyMuPDF
    logger.info("Falling back to PyMuPDF HTML conversion...")
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        doc = fitz.open(html_abs)
        pdf_bytes = doc.convert_to_pdf()
        with open(pdf_abs, "wb") as f:
            f.write(pdf_bytes)
        doc.close()
        return os.path.exists(pdf_abs) and os.path.getsize(pdf_abs) > 0
    except Exception as e:
        logger.error(f"PyMuPDF fallback failed: {e}")
        return False
