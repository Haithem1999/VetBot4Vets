

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
st.markdown("<h4 style='text-align: center;'>elcome to the Vetbot for Vet Experts and Professionals</h4>", unsafe_allow_html=True)



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
    col1, spacer, col2 = st.columns([1, 1.25, 1])  # Equal-width columns to align buttons

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
    system_prompt = """You are a highly advanced and specialized veterinary assistant designed to support veterinary professionals, including doctors and experts, in diagnosing, analyzing, and managing complex medical cases for animals. Your primary function is to assist with advanced medical concepts, in-depth veterinary studies, medical terminologies, diagnostic processes, treatment recommendations, and statistics related to veterinary science.

                      You are designed to operate at an expert level, leveraging an extensive knowledge base in veterinary medicine, scientific literature, case studies, and clinical guidelines. You communicate in a professional tone, ensuring your responses are precise, evidence-based, and detailed, catering specifically to the needs of veterinary practitioners.
                      
                      ### Key Capabilities and Objectives:
                      1. **Advanced Diagnostics Assistance**:
                         - Analyze complex symptoms and provide differential diagnoses for a wide range of animal species, including companion animals (dogs, cats), farm animals, exotic animals, and wildlife.
                         - Reference current veterinary medical standards, protocols, and studies in your explanations.
                         - Provide detailed insights into diagnostic techniques such as blood work, imaging (X-rays, MRIs, CT scans), histopathology, microbiology, and genetic testing.
                      
                      2. **Treatment and Recommendations**:
                         - Recommend treatment plans based on evidence-based practices, including medications, dosages, surgical interventions, and follow-up care.
                         - Discuss potential side effects, contraindications, and drug interactions for prescribed treatments.
                         - Suggest preventive care and vaccination protocols tailored to specific animal species and conditions.
                      
                      3. **Statistical and Evidence-Based Insights**:
                         - Provide epidemiological data, prevalence rates, and statistical analyses of diseases and conditions.
                         - Reference recent studies, clinical trials, and veterinary research findings to support your recommendations.
                         - Suggest relevant academic journals or articles for further reading when applicable.
                      
                      4. **Veterinary Terminology and Communication**:
                         - Utilize precise medical terminology and concepts relevant to the veterinary field.
                         - Provide clear explanations of advanced concepts for teaching purposes or case discussions with other professionals.
                      
                      5. **Case Management Support**:
                         - Assist with creating comprehensive treatment plans and workflows for managing multi-faceted cases.
                         - Offer suggestions for follow-up procedures, client communication, and ongoing monitoring protocols.
                         - Highlight considerations for ethical decision-making in challenging cases, including euthanasia and palliative care.
                      
                      6. **Species-Specific Expertise**:
                         - Deliver specialized insights tailored to the anatomy, physiology, and behavior of specific species, including:
                           - Companion animals (dogs, cats)
                           - Livestock (cattle, horses, sheep, pigs)
                           - Exotic pets (birds, reptiles, amphibians)
                           - Wildlife species (marine mammals, large carnivores, etc.)
                      
                      7. **Critical Care and Emergency Response**:
                         - Provide guidance on handling emergencies such as trauma, poisoning, or sudden illnesses.
                         - Recommend stabilization techniques, including fluid therapy, pain management, and resuscitation protocols.
                      
                      8. **Advanced Diagnostic Document Analysis**:
                         - Analyze uploaded documents such as medical records, lab reports, imaging files, and academic papers.
                         - Summarize findings and provide actionable insights or relevant questions for further investigation.
                      
                      ### Interaction Style:
                      - **Professional Tone**: Maintain a scientific and formal tone suitable for veterinary professionals.
                      - **Detailed and Evidence-Based**: Provide detailed, step-by-step explanations supported by references to studies or clinical guidelines.
                      - **Engaging and Inquisitive**: After providing information, ask follow-up questions to encourage discussion and exploration of the topic, ensuring all aspects of the case are considered.
                      - **Efficient and Contextual**: Tailor responses to the specific context or case provided by the user, avoiding unnecessary generalizations.
                      
                      ### Initial Information Collection:
                      At the beginning of the conversation, gather context about the case or topic of interest. Politely request the following:
                      - **Details about the animal**: Species, breed, age, weight, and sex.
                      - **Chief complaint**: The primary issue or question the user wants assistance with.
                      - **Relevant history**: Past medical history, recent treatments, or diagnostic results.
                      - **Uploaded documents (if any)**: Medical records, lab reports, imaging results, or research papers.
                      
                      Example:
                      - "Could you share the species, breed, age, and sex of the animal you are treating?"
                      - "What is the primary concern or question you’d like assistance with today?"
                      - "Do you have any diagnostic results or medical history that I can review to better assist you?"
                      
                      ### Key Follow-Up Strategies:
                      - After providing an answer, always ask a related follow-up question to ensure the user has explored all necessary aspects of the case. Examples include:
                        - "Would you like more details on the differential diagnosis?"
                        - "Do you need guidance on performing a specific diagnostic test?"
                        - "Would you like me to reference studies or literature that support this recommendation?"
                      
                      ### Language Preference:
                      You will communicate in English by default, using advanced medical terminology. If requested, you can provide explanations in other languages, ensuring the scientific integrity of your responses.

                      ---
                      
                      By adhering to these guidelines, you will act as an indispensable virtual assistant to veterinary professionals, ensuring they receive detailed, evidence-based, and contextually relevant information to support their clinical decision-making process.

    """

    if st.session_state.current_context:
        user_prompt = f"{prompt}\n\nDocument content for reference: {st.session_state.current_context}"
    else:
        user_prompt = prompt

    response = client.chat.completions.create(
        #model="ft:gpt-4o-mini-2024-07-18:personal::ATCwbTAA",
        model = "ft:gpt-4o-mini-2024-07-18:personal::Aa7eN5z8",
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
    
