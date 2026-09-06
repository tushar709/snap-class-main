import dlib
import numpy as np 
from sklearn.svm import SVC
import face_recognition_models
import streamlit as st

from src.database.db import get_all_students

@st.cache_resource
def load_dlib_models():
    
    detector = dlib.get_frontal_face_detector()  # its give the boundary if the face

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location() # its give the landmark of the face
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector , sp , facerec

def get_face_embedding(image_np):

    detector , sp , facerec = load_dlib_models()
    faces = detector(image_np , 1)
    
    encodings = []

    for face in faces:
        shape = sp(image_np , face)
        face_descriptor = facerec.compute_face_descriptor(image_np , shape ,  1) #128 embeddings

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
        if embeddings:
            X.append(np.array(embeddings))
            y.append(student.get('student_id'))

    if len(X) == 0:
        return None

    clf = SVC(kernel='linear' , probability=True , class_weight='balance')

    try:
        clf.fit(X , y)
    except ValueError:
        pass

    return {'clf' : clf , 'X':X , 'y': y }

def train_classifier(): # its train the new faces
    st.cache_resource.clear()

    model_data = get_trained_model()
    return bool(model_data)

def predict_attendance(class_image_np):

    encodings = get_face_embedding(class_image_np)

    detected_students = {}

    model_data = get_trained_model()

    if not model_data:
        return detected_students , [] , len(encodings)
    
    clf = model_data['clf']
    X_train = model_data['X']  # for embeddings
    y_train = model_data['y']  # for labels

    all_students = sorted(list(set(y_train)))

    for encoding in encodings:
        if len(all_students) >= 2:
            predict_id = int(clf.predict([encoding])[0])

        else:
            predict_id = int(all_students[0])

        student_embeddings = X_train[y_train.index(predict_id)] 

        best_match_score = np.linalg.norm(student_embeddings - encoding)  
        resembel_threeshold = 0.6

        if best_match_score <= resembel_threeshold:
            detected_students[predict_id] = True

    return detected_students , all_students , len(encodings)          




    




