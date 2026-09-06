import streamlit as st
from src.ui.base_layout import style_background_dashboard , style_base_layout
from src.components.header import header_dashboard
from src.database.db import create_teacher , check_teacher_exists , teacher_login , get_teacher_subjects
from src.components.dialogue_create_subject  import create_subject_dialogue 
from src.components.dialogue_share_subject import share_subject_dialog
from src.components.subject_card import subject_card
from src.components.dialog_add_photos import add_photos_dialog
from src.piplines.face_pipline import predict_attendance

from src.components.dialog_attendance_results import attendance_result_dialog
import pandas as pd


from src.database.config import supabase

from src.database.db import get_attendance_for_teacher
from datetime import datetime
import numpy as np 

from src.components.dialog_voice_attendnce import voice_attendace_dialog

def teacher_screen():
    style_background_dashboard()
    style_base_layout()
    # teacher_screen_login()

    if "teacher_data" in st.session_state:
        teacher_dashboard()
    elif 'teacher_login_type' not in st.session_state or st.session_state.teacher_login_type =="login":
        teacher_screen_login()
    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()

def  register_teacher(teacher_name , teacher_password , teacher_username , teacher_pass_confrm):

    if not teacher_name or not teacher_password or not teacher_username:
        return False , "All fields are required"
    
    if check_teacher_exists(teacher_username):
        return False , "Username already taken"

    if teacher_password != teacher_pass_confrm:
        return False , "Password does not match"

    try:
        create_teacher(teacher_username , teacher_password , teacher_name)
        return True , "Sucessfully Created , Now Login!" 
    except Exception as e:
        return False , "Unexpected error"
    
def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1 , c2 = st.columns(2 , vertical_alignment='center' , gap='xxlarge')

    with c1:
        header_dashboard()

    with c2:
        st.subheader(f"""Welcome , {teacher_data['name']}""")
        if st.button("Logout" , type='secondary' , key='loginbackbtn' , shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            del st.session_state.teacher_data 
            st.rerun()

    st.space()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = 'take_attendance'

    tab1 , tab2 , tab3 = st.columns(3)

    with tab1:
        type1 = "primary" if st.session_state.current_teacher_tab == 'take_attendance' else "tertiary"
        if st.button('Take Attendance' , type= type1 ,  width='stretch' , icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = 'take_attendance'
            st.rerun()

    with tab2:
        type2 = "primary" if st.session_state.current_teacher_tab == 'manage_subjects' else "tertiary"
        if st.button('Managed subject' , type=type2 , width='stretch' , icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'manage_subjects'
            st.rerun()

    with tab3:
        type3 = "primary" if st.session_state.current_teacher_tab == 'attendance_record' else "tertiary"
        if st.button('Attendance record' ,type=type3 ,  width='stretch' , icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'attendance_record'
            st.rerun() 

    st.divider()        

    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_managed_subjects()

    if st.session_state.current_teacher_tab == "attendance_record":
        teacher_tab_attendance_record()

    

def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take AI attendace')

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning('You havent created any subjects yet! Please create one for begin!')
        return

    subject_options = {f"{s['name']} - {s['subject_code']}" : s['subject_id'] for s in subjects} 

    col1 , col2 = st.columns([3,1] , vertical_alignment='bottom')

    with col1:
        selected_subject_label = st.selectbox('Select Subject' , options= list(subject_options.keys()))

    with col2:
        if st.button('Add photos' , type='primary' , icon=':material/photo_prints:' , width='stretch'):
            add_photos_dialog()    

    selected_subject_id = subject_options[selected_subject_label]       

    st.divider()

    if st.session_state.attendance_images:
        st.header('Added photos')
        gallery_cols = st.columns(4)

        for idx , img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img , width='stretch' , caption=f'Photo {idx+1}')

    c1 , c2 , c3 = st.columns(3)
    has_photos = bool(st.session_state.attendance_images)
    with c1:
           if st.button('Clear all photos' , width='stretch' , type='tertiary' , icon=':material/delete:' , disabled= not has_photos):
               st.session_state.attendance_images = []
               st.rerun()

    with c2:

        if st.button('Run face analysis' , width = 'stretch' , type='secondary' , disabled= not has_photos):
            with st.spinner('Deep scaning classroom photos....'):
                all_detected_ids = {}

                for idx , img in enumerate(st.session_state.attendance_images):
                    img_np = np.array(img.convert('RGB'))
                    detected , _ , _ = predict_attendance(img_np)


                    if detected:
                        for sid in detected.keys():
                            student_id = int(sid)

                            all_detected_ids.setdefault(student_id , []).append(f"Photo {idx+1}")

                enrolled_res = supabase.table('subjects_student').select("* , students(*)").eq('subject_id' , selected_subject_id).execute()  
                enrolled_students = enrolled_res.data

                if not enrolled_students:
                    st.warning("No students enrolled in this course")

                else:

                    result , attendance_to_log = [] , []
                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") 

                    for node in enrolled_students:
                        student = node['students']
                        sources = all_detected_ids.get(int(student['student_id']) , [])
                        is_present = len(sources) > 0

                        result.append({
                                "Name" : student['name'],
                                "ID" : student['student_id'],
                                "Source" : ", ".join(sources) if is_present else "-",
                                "Status" : "✅ Present" if is_present else "❌ Absent"         
                        })

                        attendance_to_log.append({
                                'student_id' : student['student_id'],
                                'subject_id' : selected_subject_id,
                                'timestamp' : current_timestamp,
                                'is_present' : bool(is_present)
                        })

                attendance_result_dialog(pd.DataFrame(result) , attendance_to_log) 

    with c3:
            if st.button('Use Voice Attendance' , type='primary' , width='stretch' , icon= ':material/mic:'):
                voice_attendace_dialog(selected_subject_id)
                                  


        


def teacher_tab_managed_subjects():

    teacher_id = st.session_state.teacher_data['teacher_id']
    col1 , col2 = st.columns(2)
        
    with col1: 
        st.header('Manage subjects' , width='stretch')
            
        
    with col2:
        if st.button('Create New Subject' , width='stretch'):
            create_subject_dialogue(teacher_id)

    # List all the subjects
    subjects = get_teacher_subjects(teacher_id)
    if subjects:
        for sub in subjects:
            stats = [
                ("🫂" , "Students" , sub['total_students']),
                ("🕰️" , "Classes" , sub['total_classes']),
            ]
        def share_button():
            if st.button(f"Share Code : {sub['name']}" , key=f"share_{sub['subject_code']}" , icon=":material/share:"):
                share_subject_dialog(sub['name'] , sub['subject_code'])
            st.space()

        subject_card(
            name = sub['name'],
            code =  sub['subject_code'],
            section = sub['section'],
            stats = stats,
            footer_callback = share_button
        )
    else:
        st.info("No Subject Found , Create One Above")        
 

def teacher_tab_attendance_record():
    st.header('Attendace Record')

    teacher_id = st.session_state.teacher_data['teacher_id']

    record = get_attendance_for_teacher(teacher_id)

    # clean the timestamp data 

    if not record:
        return 

    data = []

    for r in record:
        ts = r.get('timestamp')

        data.append({

            "ts_group" : ts.split(".")[0] if ts else None,
            "Time" : datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N'A",
            "Subject" : r['subjects']['name'],
            "Subject Code" : r['subjects']['subject_code'],
            "is_present" : bool(r.get('is_present' , False))

        })

    df = pd.DataFrame(data)

    summary = (

        df.groupby(['ts_group' , 'Time' , 'Subject' , 'Subject Code'])
        .agg(
            Present_Count = ('is_present' , 'sum'),
            Total_count = ('is_present' , 'count')
        ).reset_index()

    ) 

    summary['Attendance_stats'] = (
                                        
        "✅ " + summary['Present_Count'].astype(str) + " /"
        + summary['Total_count'].astype(str) + 'Students'

    )   

    display_df = (summary.sort_values(by='ts_group' , ascending=False)

                   [['Time' , 'Subject' , 'Subject Code' , 'Attendance_stats']]
                  )

    st.dataframe(display_df , width='stretch' , hide_index=True)




def login_teacher(username , password):
    if not username or not password:
        return False
    
    teacher = teacher_login(username , password)

    if teacher:
        st.session_state.user_role = 'teacher'
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True

    return False    

def teacher_screen_login():
    c1 , c2 = st.columns(2 , vertical_alignment='center' , gap='xxlarge')

    with c1:
        header_dashboard()

    with c2:
        
        if st.button("Go back to home" , type='secondary' , key='loginbackbtn' , shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Login using password', text_alignment='center')  

    st.space()
    st.space()

    teacher_username = st.text_input("Enter username" , placeholder='ananyaroy')

    teacher_password = st.text_input("Enter password" , type="password" , placeholder="Enter password")

    st.divider()

    btn1 , btn2 = st.columns(2)

    with btn1:
        if st.button('Login' , icon=':material/passkey:' , shortcut='control+enter' , width='stretch'):
            if login_teacher(teacher_username , teacher_password):
                st.toast("Welcome Back" , icon="👋")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username and password combo")    
  
    with btn2:
        if st.button('Register Instead' , icon=':material/passkey:', width='stretch'):
            st.session_state.teacher_login_type = 'register'    

def teacher_screen_register():
    c1 , c2 = st.columns(2 , vertical_alignment='center' , gap='xxlarge')

    with c1:
        header_dashboard()

    with c2:
        if st.button("Go back to home" , type='secondary' , key='loginbackbtn' , shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Register your teacher profile' , text_alignment='center')  

    st.space()
    st.space()

    teacher_username = st.text_input("Enter username" , placeholder='ananyaroy')

    teacher_name = st.text_input("Enter name" , placeholder='ananyaroy')

    teacher_password = st.text_input("Enter password" , type="password" , placeholder="Enter password") 

    teacher_pass_confrm = st.text_input("Confirm password" , type = "password" , placeholder="Enter pass word")

    st.divider()

    btn1 , btn2 = st.columns(2)

    with btn1:
        if st.button('Register now' , icon=':material/passkey:' , shortcut='control+enter' , width='stretch'):
            success , message = register_teacher(teacher_name , teacher_password , teacher_username , teacher_pass_confrm)

            if success:
                st.success(message) 
                import time 
                time.sleep(2)
                st.session_state.teacher_login_type = "login"
                st.rerun()
            else:
                st.error(message)    
  
    with btn2:
        if st.button('Login Instead' , icon=':material/passkey:', width='stretch'):
            st.session_state.teacher_login_type = 'login' 
 
    