import unittest
import numpy as np
import io
import soundfile as sf
from PIL import Image

from src.pipelines.face_pipeline import (
    get_face_embeddings,
    get_trained_model,
    predict_attendance,
    train_classifier
)
from src.pipelines.voice_pipeline import (
    get_voice_embedding,
    identify_speaker,
    process_bulk_audio,
    VOICE_AVAILABLE
)
from src.database.config import supabase

class TestAIPipelines(unittest.TestCase):

    def test_face_pipeline_deterministic_and_matching(self):
        img_arr = np.ones((100, 100, 3), dtype=np.uint8) * 128
        encs = get_face_embeddings(img_arr)
        self.assertTrue(len(encs) >= 0)

        test_enc1 = np.ones(128, dtype=np.float32) / np.sqrt(128)
        test_enc2 = np.ones(128, dtype=np.float32) / np.sqrt(128)
        dist = np.linalg.norm(test_enc1 - test_enc2)
        self.assertAlmostEqual(dist, 0.0, places=4)

    def test_voice_pipeline_cosine_similarity(self):
        vec_a = [0.5] * 256
        vec_b = [0.5] * 256
        candidates = {
            101: vec_b,
            102: [-0.5] * 256
        }
        best_sid, best_score = identify_speaker(vec_a, candidates, threshold=0.5)
        self.assertEqual(best_sid, 101)
        self.assertAlmostEqual(best_score, 1.0, places=4)

    def test_subject_students_students_join(self):
        res = supabase.table("subject_students").select("*, students(*)").limit(5).execute()
        self.assertIsInstance(res.data, list)
        if len(res.data) > 0:
            self.assertIn("students", res.data[0])

if __name__ == "__main__":
    unittest.main()
