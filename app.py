import streamlit as st
import os
from openai import OpenAI
import uuid 
import json 
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="VetExpert Chat",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Centered Title and Subtitle
st.markdown("<h1 style='text-align: center;'>Chatbot For Vet Experts 🐾</h1>", unsafe_allow_html=True)
st.markdown("<h6 style='text-align: center;'>Welcome to the Vetbot for Vet Experts and Professionals</h6>", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_context' not in st.session_state:
    st.session_state.current_context = ""
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# OpenAI API Key Setup
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# File Upload Section
uploaded_file = st.file_uploader("Upload a file (PDF, DOCX, TXT, PNG, JPG)", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"])

if uploaded_file:
    st.session_state.uploaded_file = uploaded_file
    file_type = uploaded_file.type

    if file_type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        st.session_state.current_context = text
        st.success("PDF content loaded successfully.")

    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        st.session_state.current_context = text
        st.success("Word document content loaded successfully.")

    elif file_type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
        st.session_state.current_context = text
        st.success("Text file content loaded successfully.")

    elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
        image = Image.open(uploaded_file)
        st.session_state.current_context = image
        st.image(image, caption="Uploaded Image", use_column_width=True)
        st.success("Image uploaded successfully for analysis.")

# Function to generate response
def generate_response(prompt):
    system_prompt = """You are an advanced veterinary assistant designed to assist veterinary professionals, including doctors and experts, with diagnosing, analyzing, and managing complex medical cases. Your primary focus is on providing well-detailed, evidence-based information and engaging in meaningful discussions to support clinical decision-making.

    Here are your key responsibilities:
    1. Detailed and Comprehensive Responses: Always provide thorough, step-by-step answers. Include all necessary details, explanations, and the rationale behind your suggestions.
    2. After each response you give, always ask a follow-up question to keep the conversation engaging with the user.
    3. Diagnostics and Treatment: Assist with analyzing symptoms, suggesting diagnostic tests, and recommending evidence-based treatment plans, including medications, dosages, and follow-up care.
    4. Document Analysis: If a document is uploaded (e.g., lab reports or imaging results), summarize the key findings in detail and offer actionable insights.
    5. Emergency Support: Provide quick and detailed guidance for handling critical situations, including stabilization techniques and first-line treatments.
    6. Give relevant references of sources (articles, research papers, studies...etc) only when asked by the user. 
    7. Maintain a professional but approachable tone, using precise medical terminology suited for veterinary professionals.
    8. Be consistent in your responses in terms of style and structure. 
    
    Communicate in English by default, using advanced medical terminology. You need to switch to the language used by the user if needed, while maintaining clarity and scientific rigor.
    """

    messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages

    # Handle image-based context if uploaded
    if isinstance(st.session_state.current_context, Image.Image):
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages + [{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5,
            images=[{"image": st.session_state.current_context}]
        )
    else:
        # Include document content in response if available
        user_prompt = prompt
        if st.session_state.current_context:
            user_prompt += f"\n\nDocument content for reference:\n{st.session_state.current_context}"

        response = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:personal:vetexpert:AcT2W57z",
            messages=messages + [{"role": "user", "content": user_prompt}],
            max_tokens=500,
            temperature=0.5
        )
    return response.choices[0].message.content

# Sidebar for managing conversations
st.sidebar.title("Manage Conversations")

if st.sidebar.button("➕ New Conversation"):
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.current_context = ""
    st.session_state.uploaded_file = None
    st.rerun()

# Conversation History (Placeholder for future extensions)
st.sidebar.title("Conversation History")
st.sidebar.write("This section can be expanded for saved conversations.")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input and Response
if prompt := st.chat_input("You:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = generate_response(prompt)
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
