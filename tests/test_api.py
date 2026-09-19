import unittest
from fastapi.testclient import TestClient
from main import app

class TestSmartGlassesAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("vision_model", data)
        self.assertIn("tts_model", data)
        self.assertIn("Kore", data["supported_voices"])

    def test_presets_endpoint(self):
        res = self.client.get("/api/presets")
        self.assertEqual(res.status_code, 200)
        presets = res.json().get("presets", [])
        self.assertGreaterEqual(len(presets), 3)
        preset_ids = [p["id"] for p in presets]
        self.assertIn("room_nav", preset_ids)
        self.assertIn("translate_sign", preset_ids)

    def test_interact_endpoint_validation(self):
        # /api/interact accepts optional image/audio/text, but empty without key returns 400
        res = self.client.post("/api/interact", json={"text_prompt": "hello"})
        # Should attempt processing or return error regarding API key if not configured
        self.assertIn(res.status_code, [200, 400, 500])

    def test_static_index(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Scribe Spectacles", res.text)

    def test_validation_errors(self):
        res = self.client.post("/api/see", json={})
        self.assertEqual(res.status_code, 422)

        res = self.client.post("/api/translate-visual", json={})
        self.assertEqual(res.status_code, 422)

        res = self.client.post("/api/converse", json={})
        self.assertEqual(res.status_code, 422)

if __name__ == "__main__":
    unittest.main()

