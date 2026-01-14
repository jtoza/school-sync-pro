import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

def ensure_chromium():
    """
    Ensure Playwright Chromium is installed.
    On free Render tier, browsers may not persist between deploys.
    """
    browser_cache_path = Path("/opt/render/.cache/ms-playwright/chromium")
    if not browser_cache_path.exists():
        print("Chromium not found. Installing Playwright Chromium...")
        subprocess.run(["playwright", "install", "chromium"], check=True)

def generate_pdf_from_html_content(html_content, output_path):
    """
    Generate a PDF from raw HTML content using Playwright.
    """
    ensure_chromium()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content)
        page.pdf(path=output_path)
        browser.close()
