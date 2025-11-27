# PDF Generation Setup Guide

This project uses **Playwright** for PDF generation, which works great on Windows without complex system dependencies.

## Installation Steps

### 1. Install Python Package
```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers
After installing the package, you need to install the browser binaries:

```bash
playwright install chromium
```

Or install all browsers:
```bash
playwright install
```

## How It Works

- **Primary**: Uses Playwright (headless Chromium) for high-quality PDF generation
- **Fallback**: If Playwright is not available, falls back to xhtml2pdf

## Benefits of Playwright

✅ Works on Windows without GTK3 or other system dependencies  
✅ Excellent CSS support and rendering accuracy  
✅ Handles static/media files automatically  
✅ Modern, actively maintained library  

## Troubleshooting

If you get an error about missing browsers:
```bash
playwright install chromium
```

If Playwright still doesn't work, the code will automatically fall back to xhtml2pdf.

