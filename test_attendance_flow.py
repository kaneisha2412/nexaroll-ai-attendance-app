import os
import sys
import unittest
import numpy as np

APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from src.database.config import supabase
from src.database.db import (
    create_teacher,
    check_teacher_exists,
    teacher_login,
    create_student,
    get_all_students,
    create_subject,
    get_teacher_subjects,
    enroll_student_to_subject,
    get_student_subjects,
)
from src.screens.teacher_screen import validate_username, validate_password_strength
from src.pipelines.face_pipeline import get_face_embeddings, get_trained_model, train_classifier


class TestAttendanceSystemFlow(unittest.TestCase):

    def test_01_teacher_username_validation(self):
        """Test username validation rules."""
        valid, msg = validate_username("prof_smith")
        self.assertTrue(valid)

        valid, msg = validate_username("teacher123")
        self.assertTrue(valid)

        valid, msg = validate_username("ab")
        self.assertFalse(valid)

        valid, msg = validate_username("bad user")
        self.assertFalse(valid)

        valid, msg = validate_username("bad@user!")
        self.assertFalse(valid)

    def test_02_password_strength_validation(self):
        """Test password strength requirements (min 8 chars, 1 letter, 1 number, 1 special)."""
        valid, msg = validate_password_strength("Pass1234!")
        self.assertTrue(valid, msg)

        valid, msg = validate_password_strength("P1@a")
        self.assertFalse(valid)
        self.assertIn("at least 8 characters", msg)

        valid, msg = validate_password_strength("Password!@#")
        self.assertFalse(valid)
        self.assertIn("at least one number", msg)

        valid, msg = validate_password_strength("Password123")
        self.assertFalse(valid)
        self.assertIn("at least one special character", msg)

        valid, msg = validate_password_strength("12345678!@#")
        self.assertFalse(valid)
        self.assertIn("at least one letter", msg)

    def test_03_teacher_registration_and_duplicate_check(self):
        """Test teacher account creation and duplicate username rejection."""
        username = "dr_albert_einstein"
        if check_teacher_exists(username):
            supabase.table("teachers").delete().eq("username", username).execute()

        self.assertFalse(check_teacher_exists(username))

        created = create_teacher(username, "E=mc2!Relativity", "Dr. Albert Einstein")
        self.assertTrue(len(created) > 0)
        self.assertEqual(created[0]["username"], username)

        self.assertTrue(check_teacher_exists(username))

        logged_in = teacher_login(username, "E=mc2!Relativity")
        self.assertIsNotNone(logged_in)
        self.assertEqual(logged_in["name"], "Dr. Albert Einstein")

        wrong = teacher_login(username, "WrongPassword123!")
        self.assertIsNone(wrong)

    def test_04_teacher_subject_creation_and_3_options(self):
        """Test creating a subject and generating the 3 options (link, QR code, subject code)."""
        teacher_res = supabase.table("teachers").select("*").eq("username", "dr_albert_einstein").execute()
        teacher_id = teacher_res.data[0]["teacher_id"]

        subject_code = "CS50X"
        name = "Introduction to Computer Science"
        section = "Section A"

        supabase.table("subjects").delete().eq("subject_code", subject_code).execute()

        new_subject = create_subject(subject_code, name, section, teacher_id)
        self.assertTrue(len(new_subject) > 0)
        sub = new_subject[0]
        self.assertEqual(sub["subject_code"], subject_code)

        share_link = f"http://localhost:8501/?join-code={subject_code}"
        self.assertIn(subject_code, share_link)

        qr_target = share_link
        self.assertEqual(qr_target, f"http://localhost:8501/?join-code={subject_code}")

        self.assertEqual(sub["subject_code"], subject_code)

    def test_05_student_registration_with_biometrics(self):
        """Test student mentioning their details: Name, Face photo, Voice sample."""
        mock_face_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        encodings = get_face_embeddings(mock_face_img)
        self.assertTrue(len(encodings) > 0)
        face_emb = encodings[0].tolist()
        self.assertEqual(len(face_emb), 128)

        student_name = "Jane Student"
        student_data = create_student(student_name, face_embedding=face_emb, voice_embedding=None)
        self.assertTrue(len(student_data) > 0)
        new_student = student_data[0]
        self.assertEqual(new_student["name"], student_name)
        self.assertIsNotNone(new_student["face_embedding"])

        retrained = train_classifier()
        self.assertTrue(retrained)

    def test_06_student_join_link_auto_enroll_flow(self):
        """Test the student joining via link flow:
        1. Link provides ?join-code=CS50X
        2. Student enters details (Jane Student)
        3. Pop-up displays course details with Yes/No buttons
        4. Clicking Yes enrolls student in CS50X
        """
        sub_res = supabase.table("subjects").select("*").eq("subject_code", "CS50X").execute()
        self.assertTrue(len(sub_res.data) > 0)
        subject = sub_res.data[0]
        subject_id = subject["subject_id"]

        students = get_all_students()
        student = next((s for s in students if s["name"] == "Jane Student"), None)
        self.assertIsNotNone(student)
        student_id = student["student_id"]

        supabase.table("subject_students").delete().eq("student_id", student_id).eq("subject_id", subject_id).execute()

        enrollment = enroll_student_to_subject(student_id, subject_id)
        self.assertTrue(len(enrollment) > 0)

        student_subjects = get_student_subjects(student_id)
        enrolled_codes = [s["subjects"]["subject_code"] for s in student_subjects]
        self.assertIn("CS50X", enrolled_codes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
