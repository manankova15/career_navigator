FROM python:3.12-slim

# No apt packages: poppler/tesseract require Debian mirrors at build time and often fail
# offline or behind strict firewalls. PDF text uses pypdf + PyMuPDF wheels only.
# Optional OCR: add a custom stage with `apt-get install poppler-utils tesseract-ocr tesseract-ocr-rus`
# and keep pdf2image+pytesseract in requirements if you need scanned-PDF fallback.

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/storage/resumes

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8002

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
