import streamlit as st
import os
from openai import OpenAI
import uuid 
import json 
from PyPDF2 import PdfReader
from docx import Document

# Set page configuration for a clean, professional look
st.set_page_config(
    page_title="VetExpert Chat",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Center the title
st.markdown("<h1 style='text-align: center;'>Chatbot For Vet Experts 🐾</h1>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center;'>Welcome to the Vetbot for Vet Experts and Professionals</h6>", unsafe_allow_html=True)

# Custom CSS for minimal, professional styling
st.markdown("""
    <style>
        /* Main content styling */
        .main { padding: 2rem; }
        .stTitle { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; font-weight: 500; margin-bottom: 2rem; }
        .stChatMessage { background-color: #f8f9fa; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; }
        .stFileUploader { border: 2px dashed #e0e0e0; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
        .stButton>button { background-color: #3498db; color: white; border-radius: 4px; padding: 0.5rem 1rem; }
        .stButton>button:hover { background-color: #2980b9; }
        .css-1d391kg { background-color: #f8f9fa; padding: 1rem; }
        .stDownloadButton>button { background-color: #3498db !important; color: white; border-radius: 4px; padding: 0.5rem 1rem; }
        .stDownloadButton>button:hover { background-color: #2980b9 !important; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for chat history and documents
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_context' not in st.session_state:
    st.session_state.current_context = ""
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Set up OpenAI API key
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# File upload
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"], key="file_uploader")
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
    else:
        text = "Unsupported file format."
    st.session_state.current_context = text

# Toggle file content visibility
if "show_content" not in st.session_state:
    st.session_state.show_content = False
if st.button("📝 Show/Hide File Content"):
    st.session_state.show_content = not st.session_state.show_content
if uploaded_file and st.session_state.show_content:
    st.write(st.session_state.current_context)

# Function to generate response
def generate_response(prompt):
    system_prompt = """You are an advanced veterinary assistant designed to assist veterinary professionals, including doctors and experts, with diagnosing, analyzing, and managing complex medical cases.

    Key guidelines:
    - Provide thorough, evidence-based, and structured responses.
    - Use the uploaded document as context only when specifically relevant.
    - Maintain a professional but approachable tone.
    - Do not repeat document analysis unnecessarily after it has been addressed.
    """

    user_prompt = prompt
    if st.session_state.current_context and "analyze" in prompt.lower():
        user_prompt += f"\n\nDocument content for reference:\n{st.session_state.current_context}"

    response = client.chat.completions.create(
        model="ft:gpt-4o-mini-2024-07-18:personal:vetexpert:AcT2W57z",
        messages=[{"role": "system", "content": system_prompt}] +
                 st.session_state.messages +
                 [{"role": "user", "content": user_prompt}]
    )
    return response.choices[0].message.content

# Load and save conversations
def load_conversations():
    try:
        with open('conversations.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_conversations(conversations):
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f)

conversations = load_conversations()
if st.session_state.session_id in conversations:
    st.session_state.messages = conversations[st.session_state.session_id]

# Sidebar for managing conversations
st.sidebar.title("Add a New Conversation")
if st.sidebar.button("➕ New Conversation"):
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.current_context = ""  # Clear document content
    st.session_state.uploaded_file = None
    st.rerun()

st.sidebar.title("Conversation History")
for session_id, msgs in conversations.items():
    if msgs:
        title = f"Conversation_{session_id[:7]}"
        if st.sidebar.button(title, key=session_id):
            st.session_state.session_id = session_id
            st.session_state.messages = msgs
            st.rerun()

# Chat input
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("You:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = generate_response(prompt)
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    conversations[st.session_state.session_id] = st.session_state.messages
    save_conversations(conversations)
