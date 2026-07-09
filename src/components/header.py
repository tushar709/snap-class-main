import streamlit as st

def header_home():

    logo_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRZlQvzBXybVkxpSW_tFc6n5s_MkWZzp1S5zdKdfNRuP-0VwlLmcpv-EN8&s=10"
    st.markdown(f"""
       <div style ="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom:30px; margin-top:30px">
           <img src='{logo_url}' style='height:100px;' />
           <h1 style ='text-align:centre; color:#E0E3FF'>SNAP<br/>CLASS</h1>
        </div>

    """ , unsafe_allow_html=True)