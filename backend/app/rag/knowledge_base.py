import os
import json
from typing import List
from sentence_transformers import SentenceTransformer
from chromadb import Client
from chromadb.config import Settings
from app.database.database import SessionLocal
from app.models.knowledge import Knowledge

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
CHROMA_PATH = os.getenv('CHROMA_PATH', './chroma_db')


class DummyRAG:
    def __init__(self):
        self.embedder = None
        self.collection = None
        self._initialize()

    def _initialize(self):
        try:
            self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        except Exception:
            self.embedder = None

        try:
            client = Client(Settings(persist_directory=CHROMA_PATH, anonymized_telemetry=False))
            self.collection = client.get_or_create_collection('sugarcane_knowledge')
        except Exception:
            self.collection = None

    def seed_knowledge(self):
        db = SessionLocal()
        count = db.query(Knowledge).count()
        db.close()
        if count > 0:
            return

        docs = []
        topics = [
            ('Sugarcane varieties', 'Variety', 'Which sugarcane variety gives high yield?', 'High-yielding sugarcane varieties such as Co 0238, Co 86032, and CoJ 64 are suitable depending on soil and climate.', 'variety yield sugarcane high yield'),
            ('Fertilizers', 'Fertilizer', 'Best fertilizer for sugarcane?', 'Balanced application of nitrogen, phosphorus, and potassium along with organic manure improves cane growth and quality.', 'fertilizer nitrogen phosphorus potassium sugarcane'),
            ('Irrigation', 'Irrigation', 'How often should sugarcane be irrigated?', 'Sugarcane needs regular irrigation during germination and grand growth phases, especially in dry spells.', 'irrigation sugarcane water schedule'),
            ('Pest control', 'Pest', 'How to manage sugarcane pests?', 'Use integrated pest management with field monitoring, resistant varieties, and timely biological or chemical control.', 'pest management sugarcane control'),
            ('Red rot disease', 'Disease', 'How to prevent red rot disease?', 'Prevent red rot through disease-free seed cane, field sanitation, crop rotation, and resistant varieties.', 'red rot disease prevention sugarcane'),
            ('Weed management', 'Weed', 'How to manage weeds in sugarcane?', 'Regular interculturing and herbicide use at early stages help reduce weed competition.', 'weed management sugarcane'),
            ('Harvesting', 'Harvest', 'When is sugarcane ready for harvest?', 'Harvest when the cane is mature, with high brix and clear juice, usually before over-ripening.', 'harvest sugarcane maturity'),
            ('Soil preparation', 'Soil', 'How to prepare soil for sugarcane?', 'Deep ploughing, leveling, and basal fertilizer application improve root growth and establishment.', 'soil preparation sugarcane'),
            ('Government schemes', 'Scheme', 'What government schemes help sugarcane farmers?', 'Farmers can access subsidies, loans, and support schemes through state agriculture departments and sugar mills.', 'government scheme subsidy sugarcane'),
            ('Organic farming', 'Organic', 'How to grow sugarcane organically?', 'Organic sugarcane uses compost, biofertilizers, green manuring, and integrated pest management.', 'organic sugarcane farming')
        ]

        for index, (title, category, question, answer, keywords) in enumerate(topics * 10, start=1):
            entry = Knowledge(
                title=f'{title} {index}',
                category=category,
                question=question,
                answer=answer,
                keywords=keywords,
            )
            docs.append(entry)

        db = SessionLocal()
        db.add_all(docs)
        db.commit()
        for item in docs:
            self.add_document(item)
        db.close()

    def add_document(self, knowledge: Knowledge):
        if self.embedder is None or self.collection is None:
            return None

        text = f"{knowledge.title} {knowledge.question} {knowledge.answer} {knowledge.keywords}"
        embedding = self.embedder.encode([text])[0].tolist()
        id_value = self.collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[{'id': knowledge.id, 'title': knowledge.title, 'category': knowledge.category}],
            ids=[f"doc-{knowledge.id}"],
        )
        return id_value

    def search(self, query: str, top_k: int = 4):
        if self.embedder is None or self.collection is None:
            return {'documents': [['No local knowledge available.']], 'metadatas': [[{'title': 'fallback'}]]}

        embedding = self.embedder.encode([query])[0].tolist()
        results = self.collection.query(query_embeddings=[embedding], n_results=top_k)
        return results

    def answer(self, question: str):
        results = self.search(question)
        context = '\n'.join([str(item) for item in results.get('documents', [[]])[0]])
        return {
            'answer': f"Based on the available sugarcane knowledge, here is a practical response: {question}\n\n{context}",
            'sources': results.get('metadatas', [[]])[0],
        }


rag = DummyRAG()
