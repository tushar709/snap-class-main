import streamlit as st
from src.database.db import enroll_student_to_subject
from src.database.config import supabase
from PIL import Image
import time

@st.dialog('Capture or upload photos')
def add_photos_dialog():

    st.write('Add classroom photo to scan for attendance')

    if 'photo_tab' not in st.session_state:
        st.session_state.photo_tab = 'Camera'

    t1 , t2 = st.columns(2)

    with t1:
        type_camera = "primary" if st.session_state.photo_tab == 'Camera' else 'tertiary'    
        if st.button('Camera' , type = type_camera , width='stretch'):
            st.session_state.photo_tab = 'Camera'

    with t2:
        type_upload = "primary" if st.session_state.photo_tab == 'upload' else 'tertiary'    
        if st.button('upload' , type = type_camera , width='stretch'):
            st.session_state.photo_tab = 'upload'        

    if st.session_state.photo_tab == 'Camera':
        cam_photo = st.camera_input('Take Snapshot' , key='dialog_cam')
        if cam_photo:
            st.session_state.attendance_images.append(Image.open(cam_photo))
            st.toast('Photo captured')
            st.rerun()

    if st.session_state.photo_tab == 'upload':
        upload_files = st.file_uploader('choose image files' , type=['jpg' , 'png' , 'jpeg'] , accept_multiple_files=True , key='dialoge_upload')
        if upload_files:
            for f in upload_files:
                st.session_state.attendance_images.append(Image.open(f))

            st.toast('Photo uploaded successfully')
            st.rerun()    

    st.divider()
    if st.button('Done' , type='primary' , width='stretch'):
        st.rerun()        
