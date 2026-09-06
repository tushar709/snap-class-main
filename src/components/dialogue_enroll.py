import streamlit as st
from src.database.config import supabase
import time
from src.database.db import enroll_student_to_subject 

@st.dialog('Enroll in Subject')
def enroll_dialogue():
    st.write("Enter the subject code provided by your teacher to enroll")
    join_code = st.text_input('Subject code' , placeholder='Eg. CSE1001')

    if st.button('Enroll now' , type='primary' , width='stretch'):
        if join_code:
            res = supabase.table('subjects').select('subject_id' , 'name' , 'subject_code').eq('subject_code' , join_code).execute()
            if res.data:
                subjects = res.data[0]
                student_id = st.session_state.student_data['student_id']

                check = supabase.table('subjects_student').select('*').eq('student_id' ,student_id).eq('subject_id' , subjects['subject_id']).execute()

                if check.data:
                    st.warning("You are already enrolled in this progrrame ")
                else:
                    enroll_student_to_subject(student_id , subjects['subject_id'])
                    st.success('Sucessfully enrolled')
                    time.sleep(1)
                    st.rerun()


        else:
            st.warning('Please enter the subject code')


