# create the instance to run the query 
import streamlit as st
from supabase import create_client , Client


supabase : Client = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)