
import dlib
import numpy as np
from sklearn.svm import SVC
import face_recognition_models
import streamlit as st

from src.database.db import get_all_students


@st.cache_resource
def load_dlib_models():

    detector = dlib.get_frontal_face_detector()

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec


def get_face_embedding(image_np):

    detector, sp, facerec = load_dlib_models()

    # Validate image
    image_np = np.asarray(image_np)

    if image_np.dtype != np.uint8:
        image_np = np.clip(image_np, 0, 255).astype(np.uint8)

    if image_np.ndim != 3 or image_np.shape[2] != 3:
        raise ValueError("Expected an RGB image with 3 channels")

    # Convert RGB to grayscale for face detection
    gray = np.ascontiguousarray(
        np.mean(image_np, axis=2).astype(np.uint8)
    )

    image_np = np.ascontiguousarray(image_np)

    # Increase upsampling to detect smaller faces
    faces = detector(gray, 2)

    encodings = []

    for face in faces:

        shape = sp(image_np, face)

        face_descriptor = facerec.compute_face_descriptor(
            image_np,
            shape,
            1
        )

        encodings.append(np.array(face_descriptor))

    return encodings


@st.cache_resource
def get_trained_model():

    X = []
    y = []

    student_db = get_all_students()

    if not student_db:
        return None

    for student in student_db:

        embeddings = student.get('face_embedding')

        if embeddings is None:
            continue

        try:
            embedding = np.asarray(
                embeddings,
                dtype=np.float64
            )

            if embedding.shape != (128,):
                continue

            if not np.all(np.isfinite(embedding)):
                continue

            X.append(embedding)
            y.append(student.get('student_id'))

        except (TypeError, ValueError):
            continue

    if len(X) == 0:
        return None

    # Remove invalid student IDs
    valid_data = [
        (embedding, sid)
        for embedding, sid in zip(X, y)
        if sid is not None
    ]

    if not valid_data:
        return None

    X = [item[0] for item in valid_data]
    y = [item[1] for item in valid_data]

    clf = None

    # Train SVC only when at least two students exist
    if len(set(y)) >= 2:

        clf = SVC(
            kernel='linear',
            probability=True,
            class_weight='balanced'
        )

        clf.fit(np.array(X), np.array(y))

    return {
        'clf': clf,
        'X': X,
        'y': y
    }


def train_classifier():

    st.cache_resource.clear()

    model_data = get_trained_model()

    return bool(model_data)


def predict_attendance(class_image_np):

    encodings = get_face_embedding(class_image_np)

    detected_students = {}

    model_data = get_trained_model()

    if not model_data:
        return detected_students, [], len(encodings)

    clf = model_data['clf']

    X_train = model_data['X']
    y_train = model_data['y']

    all_students = list(dict.fromkeys(y_train))

    for encoding in encodings:

        # Predict student ID
        if clf is not None:
            predict_id = clf.predict([encoding])[0]

        else:
            predict_id = all_students[0]

        # Find all embeddings belonging to predicted student
        student_embeddings = [
            emb for emb, sid in zip(X_train, y_train)
            if sid == predict_id
        ]

        if not student_embeddings:
            continue

        # Find minimum Euclidean distance
        best_match_score = min(
            np.linalg.norm(emb - encoding)
            for emb in student_embeddings
        )

        resemblance_threshold = 0.6

        if best_match_score <= resemblance_threshold:

            detected_students[predict_id] = True

    return detected_students, all_students, len(encodings)




    




