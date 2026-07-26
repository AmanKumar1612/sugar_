from app.services.ingestion.embeddings import (
    EmbeddingService
)

vector = EmbeddingService.encode(
    "Sugarcane Industries Department"
)

print(len(vector))