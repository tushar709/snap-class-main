from resemblyzer import VoiceEncoder , preprocess_wav
import numpy as np 
import io # its for load the audio file in the librosa
import librosa
import streamlit as st

@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()

def get_voice_embeddings(audio_bytes):
    try:
        encoder = load_voice_encoder(audio_bytes)
        audio , sr = librosa.load(io.BytesIO(audio_bytes) , sr = 16000)  # librosa take to params audio and sr 
        wav = preprocess_wav(audio) 
        embeddings = encoder.embed_utterance(wav)
        return embeddings.tolist()
    
    except Exception as e:
        st.error('Voice Recog error')
        return None

# its for give the audio find embedding and compare all the voice of student     
def identify_speaker(new_embeddings , candidate_dict , threeshold = 0.65): 
    if new_embeddings is None or not candidate_dict:
        return None , 0.0

    best_sid = None
    best_score = -1

    for sid , stored_embedding in candidate_dict.items():
        if stored_embedding:
            similarity = np.dot(new_embeddings , stored_embedding)
            if similarity > best_score:
                best_score = similarity
                best_sid = sid

    if best_score >= threeshold:
        return  best_sid , best_score
    
    return None , best_score

# this function for like there is a long audio so it divide it into small parts
def process_bulk_audio(audio_bytes ,  candidate_dict , threeshold = 0.65):

    try:
        encoder = load_voice_encoder()
        audio , sr = librosa.load(io.BytesIO(audio_bytes) , sr = 16000)
        segments = librosa.effects.split(audio , top_db=30) #its our voice its lasrge so its divide into small parts

        identified_results = {}

        for start , end in segments:

            if(end-start) < sr*0.5:
                continue
            segmented_audio = audio[start:end]
            wav = preprocess_wav(segmented_audio)
            embedding = encoder.embed_utterance(wav)

            sid , score = identify_speaker(embedding , candidate_dict , threeshold)

            if sid:
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = sid 

        return identified_results
    
    except Exception as e:
        st.error('Bulk Process error')
        return None , {}
    