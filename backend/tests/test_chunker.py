from app.services.ingestion.chunker import Chunker

text = """
Ganna Kisan Panjikaran is done online through the department portal.
""" * 100

chunks = Chunker.split(text)

print("Total Chunks:", len(chunks))

for i, chunk in enumerate(chunks[:3]):
    print(f"\nChunk {i+1}")
    print(chunk)