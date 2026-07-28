import unittest

from app.rag.knowledge_base import rag


class RagFallbackTests(unittest.TestCase):
    def test_answer_returns_a_response_without_model_download(self):
        response = rag.answer('How to irrigate sugarcane?')

        self.assertIn('answer', response)
        self.assertIn('sugarcane', response['answer'].lower())
        self.assertIsInstance(response['sources'], list)


if __name__ == '__main__':
    unittest.main()
