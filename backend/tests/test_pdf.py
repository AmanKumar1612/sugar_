from app.services.ingestion.pdf_ingestor import PDFIngestor

text = PDFIngestor.extract_text(
    "sample.pdf"
)

print(text[:1000])