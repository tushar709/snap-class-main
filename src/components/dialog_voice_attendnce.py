import streamlit as st

from src.piplines.voice_pipline import process_bulk_audio
from src.database.config import supabase
from datetime import datetime

from src.components.dialog_attendance_results import show_attendance_results

import pandas as pd

@st.dialog('Voice Attendance')
def voice_attendace_dialog(selected_subject_id):
    st.write('Record audio of student saying I am present. Then i will recognize the students')

    audio_data = None

    audio_data = st.audio_input("Record classroom audio")

    if st.button('Analyze Audio' , width='stretch' , type='primary'):
        with st.spinner('Processing Audion data'):
            enrolled_res = supabase.table('subjects_student').select("* , students(*)").eq('subject_id' , selected_subject_id).execute()  
            enrolled_students = enrolled_res.data

            if not enrolled_students:
                st.warning("No students enrolled in this course")
                return 
            candidate_dict ={
                s['students']['student_id'] : s['students']['voice_embedding']
                for s in enrolled_students if s['students'].get('voice_embedding')
            }

            if not candidate_dict:
                st.error('No enrolled student have voice profiles registered')
                return
            
            audio_bytes = audio_data.read()

            detected_scores = process_bulk_audio(audio_bytes , candidate_dict)

            result , attendance_to_log = [] , []
            current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") 

            for node in enrolled_students:
                student = node['students']
                scores = detected_scores.get(student['student_id'] , 0.0)
                is_present = bool(scores>0)

                result.append({
                        "Name" : student['name'],
                        "ID" : student['student_id'],
                        "Source" : scores if is_present else "-",
                        "Status" : "✅ Present" if is_present else "❌ Absent"         
                })

                attendance_to_log.append({
                        'student_id' : student['student_id'],
                        'subject_id' : selected_subject_id,
                        'timestamp' : current_timestamp,
                        'is_present' : bool(is_present)
                })
            st.session_state.voice_attendance_results = (pd.DataFrame(result) , attendance_to_log)

    if st.session_state.get('voice_attendance_results'):
        st.divider()
        df_results , logs = st.session_state.voice_attendance_results
        show_attendance_results(df_results , logs)
