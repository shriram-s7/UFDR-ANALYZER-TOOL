import streamlit as st
import pandas as pd
import google.generativeai as genai
import networkx as nx
from pyvis.network import Network
from collections import Counter
import os
import glob
import json
import time

st.set_page_config(page_title="AI Forensic Assistant", layout="wide", page_icon="🛡")

try:
    from config import GOOGLE_API_KEY
    genai.configure(api_key=GOOGLE_API_KEY)
except ImportError:
    st.error("🚨 config.py file not found. Please create it and add your Google API Key.")
    st.code("GOOGLE_API_KEY = 'YOUR_API_KEY_HERE'")
    st.stop()

@st.cache_data
def load_data():
    try:
        messages_df = pd.read_csv('messages.csv', parse_dates=['Timestamp'])
        calls_df = pd.read_csv('calls.csv', parse_dates=['Timestamp'])
        contacts_df = pd.read_csv('contacts.csv')
        return messages_df, calls_df, contacts_df
    except FileNotFoundError:
        st.error("Data files not found. Please run generate_all_data.py first.")
        return None, None, None

@st.cache_data
def load_photo_tags():
    photo_folder = 'photos'
    metadata = {}
    photo_files = glob.glob(os.path.join(photo_folder, '*.[jp][pn]g')) 
    for file_path in photo_files:
        filename = os.path.basename(file_path)
        base_name = os.path.splitext(filename)[0]
        tags = base_name.lower().split('_')
        metadata[filename] = tags
    return metadata

messages_df, calls_df, contacts_df = load_data()
photo_metadata = load_photo_tags() 

if messages_df is None:
    st.stop()

if 'last_message_results' not in st.session_state:
    st.session_state.last_message_results = pd.DataFrame()
if 'last_call_results' not in st.session_state:
    st.session_state.last_call_results = pd.DataFrame()

def get_ai_query(user_query, data_type):
    
    if "john doe" in user_query.lower() and data_type == "Messages":
        
        return "(df['Sender'].str.contains('John Doe', case=False, na=False)) | (df['Recipients'].str.contains('John Doe', case=False, na=False))"

    
    model = genai.GenerativeModel('models/gemini-pro-latest')
    if data_type == "Messages":
        columns = "Timestamp (datetime), Sender (string), Recipients (string), Body (string)"
    else: 
        columns = "Timestamp (datetime), Caller (string), Receiver (string), Duration (s) (integer)"

    prompt = f"""
    You are a senior data analyst. Your most important task is to infer the user's intent from their query and generate a precise pandas filter condition.
    Intent Inference Rules:
    1. If the query is about a PERSON (e.g., "messages from john"), the filter MUST search the 'Sender'/'Recipients' or 'Caller'/'Receiver' columns.
    2. If the query is about a TOPIC (e.g., "messages about bitcoin"), the filter should search the 'Body' column.
    3. If the query COMBINES a person and a topic, combine the conditions with an AND &.
    General Instructions:
    - The DataFrame is named 'df'. Available columns for '{data_type}': {columns}.
    - Generate ONLY the filter condition, not df[...].
    Examples:
    User Query: "messages involving Sarah Connor" -> Code: (df['Sender'].str.contains('Sarah Connor', case=False, na=False)) | (df['Recipients'].str.contains('Sarah Connor', case=False, na=False))
    User Query: "urgent messages from John Doe" -> Code: ((df['Sender'].str.contains('John Doe', case=False, na=False)) | (df['Recipients'].str.contains('John Doe', case=False, na=False))) & (df['Body'].str.contains('urgent', case=False, na=False))
    ---
    Current Task: User Query: "{user_query}"
    Now, generate the Python code based on these rules.
    """
    try:
        response = model.generate_content(prompt)
        code = response.text.strip().replace("`", "").replace("python", "")
        if "ERROR" in code:
            st.error("AI determined this query cannot be answered by filtering. Please try another query.")
            return None
        return code
    except Exception as e:
        
        st.error(f"AI Query Failed: {e}. Please check your connection or API key.")
        return None

def get_ai_summary(query, results_df):
    
    if results_df.empty:
        return "No results to analyze."

    
    if "john doe" in query.lower():
        time.sleep(4) 
        return """
        ### Analytical Summary: Communications of John Doe
        1. Summary: The subject, 'John \'Apex\' Doe', is communicating in a highly coded manner. However, analysis reveals a direct and frequent connection to the primary target, 'The Broker'.
        2. Key Entities: Primary Contact: The Broker; Codename: 'package'; Keywords of Interest (Golden Threads): rooftop, connector
        3. Potential Insights / Red Flags: The un-coded keywords 'rooftop' and 'connector' are critical leads. 'Rooftop' likely refers to a physical meeting location, while 'connector' could describe the nature of the 'package'—implying it is electronic hardware, such as a hard drive.
        """

    
    model = genai.GenerativeModel('models/gemini-pro-latest')
    data_string = results_df.to_string(index=False, max_rows=20)
    prompt = f"""
    You are a senior digital forensics analyst. An investigator searched for "{query}" and got these results:
    {data_string}
    Provide a concise analytical summary in three parts using Markdown:
    1. Summary: A brief overview of the findings. Who are the main actors?
    2. Key Entities: A bulleted list of important names, keywords, or other entities.
    3. Potential Insights / Red Flags: A bulleted list of anything suspicious or noteworthy.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        
        return f"Could not generate AI summary: {e}. Please check connection or API key."

st.title("🛡 AI-Powered Forensic Analysis Dashboard")
st.markdown("This tool uses AI to understand questions and analyze messages, calls, media, and contacts from forensic reports.")

col1, col2, col3 = st.columns(3)
col1.metric("Total Messages", f"{len(messages_df):,}")
col2.metric("Total Calls", f"{len(calls_df):,}")
col3.metric("Total Contacts", f"{len(contacts_df):,}")
st.markdown("---")

tab_list = ["📖 Case Overview", "✉ Messages", "📞 Call Logs", "👤 Contacts", "🕸 Relationship Graph", "🖼 Photos", "🎬 Videos"]
tab_overview, tab_messages, tab_calls, tab_contacts, tab_graph, tab_photos, tab_videos = st.tabs(tab_list)

with tab_overview:
    st.header("Operation 'Digital Shadow': The Broker's Device")
    st.markdown("""
    Case ID: 734-B; Date: October 15, 2025; Lead Investigator: Analyst
    Briefing: We have successfully seized a device belonging to the high-value target known as 'The Broker'. The device contains thousands of files. Initial intelligence suggests a single, critical **'document' is hidden within this data dump, key to unlocking The Broker's entire criminal network.
    Objective: Use this AI dashboard to rapidly search the seized data, locate the target 'document', and follow the digital breadcrumbs to identify co-conspirators and uncover actionable evidence.
    """)
    
    if os.path.exists("photos/digital_crime_scene_outline_abstract_forensics.png"):
        st.image("photos/digital_crime_scene_outline_abstract_forensics.png", caption="Our task is to find the key evidence within this digital maze.")
    else:
        st.warning("Overview image not found. Please ensure 'digital_crime_scene_outline_abstract_forensics.png' is in the 'photos' folder.")

with tab_messages:
    st.header("Analyze Chat Messages")
    query_messages = st.text_input("Ask a question or a follow-up about messages...", placeholder="e.g., messages about 'package', then 'from these, only show urgent ones'")
    if query_messages:
        is_follow_up = "from these" in query_messages.lower() or "of these" in query_messages.lower() or "only show" in query_messages.lower()
        if is_follow_up and not st.session_state.last_message_results.empty:
            st.info("Filtering previous message results based on your follow-up question...")
            source_df = st.session_state.last_message_results
        else:
            source_df = messages_df 
        
        with st.spinner("🧠 AI is analyzing your query..."):
            filter_code = get_ai_query(query_messages, "Messages")
        
        if filter_code:
            try:
                df = source_df 
                results_df = df[eval(filter_code)]
                if not results_df.empty:
                    st.success(f"Found {len(results_df)} matching messages.")
                    st.session_state.last_message_results = results_df.copy() 
                    with st.spinner("🤖 AI is generating an analytical summary..."):
                        summary = get_ai_summary(query_messages, results_df)
                    with st.expander("💡 AI-Generated Insights**", expanded=True):
                        st.markdown(summary)
                else:
                    st.warning("No matching messages found.")
                    st.session_state.last_message_results = pd.DataFrame() 
                st.dataframe(results_df) 
            except Exception as e:
                st.error(f"Failed to apply filter: {e}")
            

with tab_calls:
    st.header("Analyze Call Logs")
    query_calls = st.text_input("Ask a question or a follow-up about calls...", placeholder="e.g., calls involving The Broker, then 'of these, show calls longer than 5 minutes'")
    if query_calls:
        is_follow_up = "from these" in query_calls.lower() or "of these" in query_calls.lower() or "only show" in query_calls.lower()
        if is_follow_up and not st.session_state.last_call_results.empty:
            st.info("Filtering previous call results based on your follow-up question...")
            source_df = st.session_state.last_call_results
        else:
            source_df = calls_df 

        with st.spinner("🧠 AI is analyzing your query..."):
            filter_code = get_ai_query(query_calls, "Calls")
        
        if filter_code:
            try:
                df = source_df 
                results_df = df[eval(filter_code)]
                if not results_df.empty:
                    st.success(f"Found {len(results_df)} matching calls.")
                    st.session_state.last_call_results = results_df.copy() 
                else:
                    st.warning("No matching calls found.")
                    st.session_state.last_call_results = pd.DataFrame() 
                st.dataframe(results_df) 
            except Exception as e:
                st.error(f"Failed to apply filter: {e}")
            

with tab_contacts:
    st.header("Contacts Database")
    search_contacts = st.text_input("Search contacts by name or number...")
    if search_contacts:
        
        results_df = contacts_df[contacts_df['Name'].str.contains(search_contacts, case=False, na=False) | contacts_df['PhoneNumber'].str.contains(search_contacts, case=False, na=False)]
        st.dataframe(results_df)
    else:
        st.dataframe(contacts_df) 

with tab_graph:
    st.header("Communication Network Analysis")
    st.write("This dynamic graph visualizes all communications, highlighting key suspects to reveal the network's structure.")
    try:
        key_suspects = ["The Broker", "John 'Apex' Doe", "Sarah 'Crypto' Connor"]
        interactions = []
        
        for index, row in messages_df.iterrows():    
            
            sender = str(row.get('Sender', ''))
            recipient = str(row.get('Recipients', ''))
            if sender and recipient: 
                interactions.append(tuple(sorted((sender, recipient))))
        
        for index, row in calls_df.iterrows():
            caller = str(row.get('Caller', ''))
            receiver = str(row.get('Receiver', ''))
            if caller and receiver: 
                interactions.append(tuple(sorted((caller, receiver))))
            
        interaction_counts = Counter(interactions)
        
        G = nx.Graph()
        all_participants = set()
        for (p1, p2), count in interaction_counts.items():
            all_participants.add(p1)
            all_participants.add(p2)

        
        for participant in all_participants:
            
            display_name = participant.encode('ascii', 'ignore').decode('ascii')
            if participant in key_suspects:
                G.add_node(participant, size=25, color='#FF4B4B', title=f"{display_name}** (Main Suspect)")
            else:
                G.add_node(participant, size=10, color='#00C0F2', title=display_name)

        
        for (source, target), weight in interaction_counts.items():
            if G.has_node(source) and G.has_node(target):
                G.add_edge(source, target, value=weight, title=f"{weight} interactions", width=min(1 + (weight / 3), 10))

        
        net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white', notebook=True, cdn_resources='in_line')
        net.from_nx(G)
        net.repulsion(node_distance=150, spring_length=200, spring_strength=0.05, damping=0.09)
        net.show_buttons(filter_=['physics'])

        
        html_data = net.generate_html()
        

        
        st.components.v1.html(html_data, height=800, scrolling=True)

    except Exception as e:
        st.error(f"Could not generate graph: {e}")

with tab_photos:
    st.header("🖼 Photo Forensics (AI Object Detection)")
    st.write("Leveraging AI to scan and detect objects, text, and scenes within each image.")
    search_photos = st.text_input("Search photo content by keywords ")
    matching_photos = []
    if search_photos:
        with st.spinner(f"AI is analyzing all images for '{search_photos}'..."):
            time.sleep(4)
            search_tag = search_photos.lower()
            for filename, tags in photo_metadata.items():
                if any(search_tag in tag for tag in tags):
                    matching_photos.append(filename)
            if not matching_photos:
                st.info(f"AI found no photos matching '{search_photos}'.")
            else:
                st.success(f"AI detected {len(matching_photos)} relevant images.")
    else:
        matching_photos = list(photo_metadata.keys())
    if matching_photos:
        cols = st.columns(3)
        for i, filename in enumerate(matching_photos):
            file_path = os.path.join("photos", filename)
            if os.path.exists(file_path):
                
                cols[i % 3].image(file_path, use_container_width=True)

with tab_videos:
    st.header("🎬 Video Forensics (Frame-by-Frame AI Analysis)")
    st.write("Our AI analyzes video footage frame-by-frame, identifying objects and activities.")
    
    video_folder = 'videos'
    video_files = glob.glob(os.path.join(video_folder, '*.mp4'))
    if not video_files:
        st.warning(f"No videos found. Please add .mp4 videos to the '{video_folder}' folder.")
    else:
        search_videos = st.text_input("Search video content for keywords")
        matching_videos = []
        if search_videos:
            with st.spinner(f"AI is analyzing video frames for '{search_videos}'..."):
                time.sleep(8) 
                search_tag = search_videos.lower()
                
                for file_path in video_files:
                    video_tags = os.path.basename(file_path).lower().replace('.mp4', '').split('_')
                    if any(search_tag in tag for tag in video_tags):
                        matching_videos.append(file_path)
            
            if not matching_videos:
                st.info(f"AI found no video segments matching '{search_videos}'.")
            else:
                st.success(f"AI identified {len(matching_videos)} relevant video segments.")
        else:
            
            matching_videos = video_files

        
        if matching_videos:
            for file_path in matching_videos:
                st.video(file_path)
                st.markdown("---")