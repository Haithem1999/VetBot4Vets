

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
        .main {
            padding: 2rem;
        }
        
        /* Header styling */
        .stTitle {
            color: #2c3e50;
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 500;
            margin-bottom: 2rem;
        }
        
        /* Chat message styling */
        .stChatMessage {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        
        /* File uploader styling */
        .stFileUploader {
            border: 2px dashed #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        /* Button styling */
        .stButton>button {
            background-color: #3498db;
            color: white;
            border-radius: 4px;
            border: none;
            padding: 0.5rem 1rem;
            transition: background-color 0.3s;
        }
        
        .stButton>button:hover {
            background-color: #2980b9;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #f8f9fa;
            padding: 1rem;
        }
            
        /* Download button styling */
        .stDownloadButton>button {
            background-color: #3498db !important;
            color: white;
            border-radius: 4px;
            border: none;
            padding: 0.5rem 1rem;
            transition: background-color 0.3s;
    }
    
    .stDownloadButton>button:hover {
        background-color: #2980b9 !important;
    }
        

        .stTitle>h1 {
            font-size: 2.5rem;
            color: #2c3e50;
            font-weight: 600;
            margin-bottom: 0.5rem;
            font-family: 'Helvetica Neue', sans-serif;
        }

        .stMarkdown>p {
            font-size: 1.2rem;
            color: #7f8c8d;
            font-weight: 400;
            margin-bottom: 2rem;
            font-family: 'Helvetica Neue', sans-serif;
        }
        
        /* Chat input styling */
        .stTextInput>div>div>input {
            border-radius: 20px;
            border: 1px solid #e0e0e0;
            padding: 0.5rem 1rem;
        }

    </style>
""", unsafe_allow_html=True)


# Initialize conversation history in session state if not present
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = {}
if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = []
if 'selected_conversation' not in st.session_state:
    st.session_state.selected_conversation = None


# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = []


# Set up the OpenAI API key
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)


# Store uploaded documents in session state
if 'documents' not in st.session_state:
    st.session_state.documents = {}
    st.session_state.current_context = ""  # Initialize as empty string
    st.session_state.uploaded_file = None  # Initialize uploaded file as None

# Create a unique session ID for the current user
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# File upload
uploaded_file = st.file_uploader("Upload a file", type=["pdf", "docx", "txt"], key="file_uploader")

# If a file is uploaded, process it and store its content
if uploaded_file:
    st.session_state.uploaded_file = uploaded_file  # Store uploaded file in session state
    if uploaded_file.type == "application/pdf":
        pdf_reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() for page in pdf_reader.pages])
        st.session_state.current_context = text  # Store parsed text for chatbot use
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
        st.session_state.current_context = text  # Store parsed text for chatbot use
    elif uploaded_file.type == "text/plain":
        text = uploaded_file.read().decode("utf-8")
        st.session_state.current_context = text  # Store parsed text for chatbot use
    else:
        text = "Unsupported file format."

# Initialize toggle state in session state
if "show_content" not in st.session_state:
    st.session_state.show_content = False

# Layout for buttons in a single row using container
with st.container():
    col1, spacer, col2 = st.columns([1, 1.77, 1])  # Equal-width columns to align buttons

    with col1:
        # Toggle button to display or hide content
        if st.button(" 📝 Show/Hide File Content", key="show_hide_button"):
            st.session_state.show_content = not st.session_state.show_content

    with col2:
        # Download button for conversation
        st.download_button(
            " ⬇️ Download Conversation",
            data=json.dumps(st.session_state.messages, indent=2),
            file_name= f"Conversation_{st.session_state.session_id[:7]}.json",
            mime="application/json", 
            key="download_button"
        )

    
# Display or hide content based on the toggle state
if uploaded_file and st.session_state.show_content:
    st.write(text)


# Add space between buttons and chat section
st.write("")  
st.write("") 
st.write("") 


# Function to generate response
def generate_response(prompt):
    # Define the system prompt
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

    if st.session_state.current_context:
        user_prompt = f"{prompt}\n\nDocument content for reference: {st.session_state.current_context}"
    else:
        user_prompt = prompt

    response = client.chat.completions.create(
        #model="ft:gpt-4o-mini-2024-07-18:personal::ATCwbTAA",
        model= "ft:gpt-4o-mini-2024-07-18:personal::AfCmkpUj",
        messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages + [{"role": "user", "content": user_prompt}],
    )
    
    return response.choices[0].message.content

# Load previous conversations from a file
def load_conversations():
    try:
        with open('conversations.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save conversations to a file
def save_conversations(conversations):
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f)

# Load previous conversations
conversations = load_conversations()

# Load previous messages for this session, if any
if st.session_state.session_id in conversations:
    st.session_state.messages = conversations[st.session_state.session_id]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initialize sidebar for conversation history
st.sidebar.title("Add a New Conversation")

# Create a "New Conversation" button
if st.sidebar.button("➕ New Conversation"):
    # Clear the current conversation
    st.session_state.messages = []
    # Generate new session ID
    st.session_state.session_id = str(uuid.uuid4())
    # Clear current context and uploaded file when starting a new conversation
    st.session_state.current_context = ""  # Clear document content
    st.session_state.uploaded_file = None  # Clear uploaded file
    st.rerun()
    
st.sidebar.write("")

st.sidebar.title("Conversation History")

# Display past conversations in sidebar
for session_id, msgs in conversations.items():
    if msgs:  # Only show sessions that have messages
        # Get first user message as title, or use session ID if no messages
        # title = next((msg["content"][:30] + "..." for msg in msgs if msg["role"] == "user"), f"Conversation {session_id[:8]}")
        title = f"Conversation_{session_id[:7]}"
        if st.sidebar.button(title, key=session_id):
            st.session_state.session_id = session_id
            st.session_state.messages = msgs
            st.rerun()

# Chat input
if prompt := st.chat_input("You:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = generate_response(prompt)
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Save the updated conversation
    conversations[st.session_state.session_id] = st.session_state.messages
    save_conversations(conversations)
    
