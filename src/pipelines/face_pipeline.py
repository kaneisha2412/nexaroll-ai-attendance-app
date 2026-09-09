

import json
import numpy as np
from src.database.db import get_all_students

try:
    import streamlit as st
except ImportError:
    class _DummyCache:
        def __call__(self, fn=None, **kwargs):
            if fn is None:
                return lambda f: f
            return fn
        def clear(self):
            pass
    class _DummyStreamlit:
        cache_resource = _DummyCache()
    st = _DummyStreamlit()

try:
    from sklearn.svm import SVC
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False

try:
    import dlib
    import face_recognition_models
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False


@st.cache_resource
def load_dlib_models():
    if not DLIB_AVAILABLE:
        return None, None, None
    detector = dlib.get_frontal_face_detector() 
    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )
    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )
    return detector, sp, facerec


def _sanitize_image(image_np):
    if image_np is None:
        return None
    if not isinstance(image_np, np.ndarray):
        image_np = np.array(image_np)
    if image_np.size == 0:
        return None
    # If RGBA, drop alpha channel
    if len(image_np.shape) == 3 and image_np.shape[2] == 4:
        image_np = image_np[:, :, :3]
    elif len(image_np.shape) == 2:  # Grayscale
        image_np = np.stack((image_np,) * 3, axis=-1)
    if image_np.dtype != np.uint8:
        image_np = np.clip(image_np, 0, 255).astype(np.uint8)
    return image_np


def get_face_embeddings(image_np):
    img = _sanitize_image(image_np)
    if img is None:
        return []

    # 1. Primary: Use high-level face_recognition library
    if FACE_REC_AVAILABLE:
        try:
            encodings = face_recognition.face_encodings(img)
            if encodings:
                return [np.array(e, dtype=np.float32) for e in encodings]
        except Exception:
            pass

    # 2. Secondary: Direct dlib models
    if DLIB_AVAILABLE:
        try:
            detector, sp, facerec = load_dlib_models()
            if detector and sp and facerec:
                faces = detector(img, 1)
                encodings = []
                for face in faces:
                    shape = sp(img, face)
                    desc = facerec.compute_face_descriptor(img, shape, 1)
                    encodings.append(np.array(desc, dtype=np.float32))
                if encodings:
                    return encodings
        except Exception:
            pass

    # 3. Fallback: Deterministic 128-d vector if no ML models available
    thumb = np.mean(img, axis=2) if len(img.shape) == 3 else img
    vec = np.resize(thumb, 128).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return [vec]


@st.cache_resource
def get_trained_model():
    X = []
    y = []

    student_db = get_all_students()
    if not student_db:
        return None

    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            if isinstance(embedding, str):
                try:
                    embedding = json.loads(embedding)
                except Exception:
                    continue
            if isinstance(embedding, (list, tuple, np.ndarray)) and len(embedding) == 128:
                X.append(np.array(embedding, dtype=np.float32))
                y.append(student.get('student_id'))

    if len(X) == 0:
        return None

    X_arr = np.array(X, dtype=np.float32)

    clf = None
    if SKLEARN_AVAILABLE and len(set(y)) >= 2:
        try:
            clf = SVC(kernel='linear', probability=True, class_weight='balanced')
            clf.fit(X_arr, y)
        except Exception:
            clf = None

    return {'clf': clf, 'X': X_arr, "y": y}


def train_classifier():
    st.cache_resource.clear()
    model_data = get_trained_model()
    return bool(model_data)


def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)
    detected_student = {}

    model_data = get_trained_model()
    if not model_data or not encodings:
        return detected_student, [], len(encodings)

    X_train = model_data['X']
    y_train = model_data['y']
    all_students = sorted(list(set(y_train)))

    if len(X_train) == 0:
        return detected_student, all_students, len(encodings)

    resemblance_threshold = 0.65

    for encoding in encodings:
        encoding = np.array(encoding, dtype=np.float32)
        # Compute Euclidean distance to all enrolled embeddings
        distances = np.linalg.norm(X_train - encoding, axis=1)
        best_idx = int(np.argmin(distances))
        best_distance = float(distances[best_idx])

        if best_distance <= resemblance_threshold:
            matched_id = y_train[best_idx]
            detected_student[matched_id] = True

    return detected_student, all_students, len(encodings)


