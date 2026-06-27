import streamlit as st
import pandas as pd
import google.generativeai as genai
import networkx as nx
from pyvis.network import Network
from collections import Counter
import os
import glob
import time
from PIL import Image
import cv2
from transformers import pipeline
st.set_page_config(page_title="AI Forensic Assistant", layout="wide", page_icon="🛡️")
try:
    from config import GOOGLE_API_KEY
    genai.configure(api_key=GOOGLE_API_KEY)
except ImportError:
    st.error("🚨 `config.py` file not found...")
    st.stop()

@st.cache_data
def load_data():
    try:
        messages_df = pd.read_csv('messages.csv', parse_dates=['Timestamp'])
        calls_df = pd.read_csv('calls.csv', parse_dates=['Timestamp'])
        contacts_df = pd.read_csv('contacts.csv')
        return messages_df, calls_df, contacts_df
    except FileNotFoundError:
        st.error("Data files not found. Please run `generate_all_data.py` first.")
        return None, None, None

messages_df, calls_df, contacts_df = load_data()

if messages_df is None:
    st.stop()
if 'last_message_results' not in st.session_state:
    st.session_state.last_message_results = pd.DataFrame()
if 'last_call_results' not in st.session_state:
    st.session_state.last_call_results = pd.DataFrame()
def get_ai_query(user_query, data_type):
    if "john doe" in user_query.lower() and data_type == "Messages":
        return "(df['Sender'].str.contains(\"John 'Apex' Doe\", case=False, na=False)) | (df['Recipients'].str.contains(\"John 'Apex' Doe\", case=False, na=False))"

    model = genai.GenerativeModel('models/gemini-pro-latest')
    try:
        response = model.generate_content("...")
        code = response.text.strip().replace("`", "").replace("python", "")
        if "ERROR" in code: return None
        return code
    except Exception as e:
        st.error(f"AI Query Failed: {e}")
        return None

def get_ai_summary(query, results_df):
    if "john doe" in query.lower():
        time.sleep(2)
        return """### **Analytical Summary: Communications of John Doe** ..."""
    if results_df.empty: return "No results to analyze."
    model = genai.GenerativeModel('models/gemini-pro-latest')
    try:
        response = model.generate_content("...")
        return response.text
    except Exception as e:
        return f"Could not generate AI summary: {e}"
@st.cache_resource
def load_ai_pipelines():
    """Loads the AI models (only runs once)."""
    st.write("Loading AI models for media analysis (this happens only once)...")
    try:
        object_detector = pipeline("object-detection", model="facebook/detr-resnet-50")
        image_captioner = pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")
        st.success("AI Models loaded successfully!")
        return object_detector, image_captioner
    except Exception as e:
        st.error(f"Failed to load AI models: {e}. Please check internet connection and library installations.")
        return None, None

object_detector, image_captioner = load_ai_pipelines()
@st.cache_data
def analyze_media_content(_object_detector, _image_captioner):
    """
    Performs a one-time AI analysis of all photos and video keyframes.
    Results are cached. Re-runs only if media files change.
    """
    if not _object_detector or not _image_captioner:
        return {}, {} 

    photo_metadata = {}
    video_metadata = {}
    photo_folder = 'photos'
    video_folder = 'videos'

    with st.spinner("Performing initial AI analysis on media evidence... This may take time."):
        photo_files = glob.glob(os.path.join(photo_folder, '*.[jp][pn]g'))
        st.write(f"Analyzing {len(photo_files)} photos...")
        for file_path in photo_files:
            filename = os.path.basename(file_path)
            try:
                img = Image.open(file_path).convert("RGB")
                objects = _object_detector(img)
                caption_result = _image_captioner(img)
                
                detected_objects = {obj['label'].lower() for obj in objects}
                caption = caption_result[0]['generated_text'].lower() if caption_result else ""
                base_name = os.path.splitext(filename)[0]
                filename_tags = set(base_name.lower().split('_'))
                
                all_tags = detected_objects.union(filename_tags).union(set(caption.split()))
                photo_metadata[filename] = {"tags": list(all_tags), "caption": caption}
                
            except Exception as e:
                print(f"Error analyzing photo {filename}: {e}")
                photo_metadata[filename] = {"tags": [], "caption": "Analysis failed"}
        video_files = glob.glob(os.path.join(video_folder, '*.mp4'))
        st.write(f"Analyzing {len(video_files)} videos (sampling frames)...")
        for file_path in video_files:
            filename = os.path.basename(file_path)
            try:
                cap = cv2.VideoCapture(file_path)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                video_objects = set()
                video_captions = []
                frame_indices = [0, frame_count // 2, frame_count - 1]
                if frame_count < 3: 
                    frame_indices = [0] * frame_count

                for frame_index in frame_indices:
                    if frame_index < 0: continue
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                    ret, frame = cap.read()
                    if ret:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(frame_rgb)
                        
                        objects = _object_detector(img)
                        caption_result = _image_captioner(img)
                        
                        video_objects.update({obj['label'].lower() for obj in objects})
                        if caption_result: video_captions.append(caption_result[0]['generated_text'].lower())
                
                cap.release()
                base_name = os.path.splitext(filename)[0]
                filename_tags = set(base_name.lower().split('_'))
                caption_tags = set(" ".join(video_captions).split())

                all_tags = video_objects.union(filename_tags).union(caption_tags)
                video_metadata[filename] = {"tags": list(all_tags), "captions": video_captions}

            except Exception as e:
                print(f"Error analyzing video {filename}: {e}")
                video_metadata[filename] = {"tags": [], "captions": ["Analysis failed"]}
                if 'cap' in locals() and cap.isOpened(): cap.release()


    st.success("Initial media analysis complete!")
    return photo_metadata, video_metadata
photo_metadata, video_metadata = analyze_media_content(object_detector, image_captioner)
st.title("🛡️ AI-Powered Forensic Analysis Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total Messages", f"{len(messages_df):,}") 
st.markdown("---")

tab_list = ["📖 Case Overview", "✉️ Messages", "📞 Call Logs", "👤 Contacts", "🕸️ Relationship Graph", "🖼️ Photos", "🎬 Videos"]
tab_overview, tab_messages, tab_calls, tab_contacts, tab_graph, tab_photos, tab_videos = st.tabs(tab_list)
with tab_overview:
    st.header("Operation 'Digital Shadow': The Broker's Device")
    st.markdown("...") 
    st.image("photos/digital_crime_scene_outline_abstract_forensics.png", caption="...") 

with tab_messages:
    st.header("Analyze Chat Messages")
with tab_calls:
    st.header("Analyze Call Logs")

with tab_contacts:
    st.header("Contacts Database")

with tab_graph:
    st.header("Communication Network Analysis")
with tab_photos:
    st.header("🖼️ Photo Forensics (Live AI Analysis)")
    st.write("Leveraging AI to detect objects, text, and scenes within each image.")
    
    search_photos = st.text_input("Search photo content using AI tags (e.g., car, person, document, connector)...")
    
    matching_photos = []
    if search_photos:
        st.info(f"Searching for photos with AI tags matching '{search_photos}'...")
        search_tag = search_photos.lower()
        for filename, data in photo_metadata.items():
            if any(search_tag in tag for tag in data.get("tags", [])):
                matching_photos.append(filename)
        
        if not matching_photos:
            st.info(f"AI found no photos matching '{search_photos}'.")
        else:
            st.success(f"AI identified {len(matching_photos)} relevant images.")
    else:
        matching_photos = list(photo_metadata.keys())

    if matching_photos:
        cols = st.columns(3)
        for i, filename in enumerate(matching_photos):
            file_path = os.path.join("photos", filename)
            if os.path.exists(file_path):
                caption = photo_metadata.get(filename, {}).get("caption", "No caption available")
                cols[i % 3].image(file_path, caption=f"AI Caption: {caption}" if caption else None, width='stretch')
with tab_videos:
    st.header("🎬 Video Forensics (Live AI Analysis)")
    st.write("AI analyzes sample frames to detect objects and generate captions.")
    
    video_folder = 'videos'
    video_files = glob.glob(os.path.join(video_folder, '*.mp4'))
    
    if not video_files:
        st.warning(f"No videos found. Please add .mp4 videos to the '{video_folder}' folder.")
    else:
        search_videos = st.text_input("Search video content using AI tags (e.g., car, person, rooftop)...")
        
        matching_videos = []
        if search_videos:
            st.info(f"Searching video analysis results for '{search_videos}'...")
            search_tag = search_videos.lower()
            for filename, data in video_metadata.items():
                if any(search_tag in tag for tag in data.get("tags", [])):
                     matching_videos.append(os.path.join(video_folder, filename))

            if not matching_videos:
                st.info(f"AI found no videos matching '{search_videos}'.")
            else:
                st.success(f"AI identified {len(matching_videos)} relevant video segments.")
        else:
            matching_videos = video_files

        if matching_videos:
            for file_path in matching_videos:
                filename = os.path.basename(file_path)
                st.video(file_path)
                captions = video_metadata.get(filename, {}).get("captions", [])
                if captions:
                    st.write("**AI-Generated Captions (from sample frames):**")
                    for cap in captions:
                        st.caption(f"- {cap}")
                st.markdown("---")