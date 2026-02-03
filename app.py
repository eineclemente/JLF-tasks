"""
Streamlit App with OpenRouter AI
"""
import os
import json
import base64
from datetime import datetime
import requests
import streamlit as st
from streamlit_mic_recorder import speech_to_text
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHATS_FILE = "chat_history.json"


def load_all_chats():
    """Load all saved chats from file."""
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_all_chats(chats):
    """Save all chats to file."""
    with open(CHATS_FILE, "w") as f:
        json.dump(chats, f, indent=2)


def ask_ai(messages: list, model: str = "openai/gpt-3.5-turbo") -> str:
    """Send messages to OpenRouter and return the response."""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": messages
        }
    )
    data = response.json()
    return data["choices"][0]["message"]["content"]


# --- Streamlit UI ---

# Modern UI Styling - Green & White Theme
st.markdown("""
<style>
    /* ===== GLOBAL - Light Background ===== */
    .stApp {
        background: linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%);
    }

    /* ===== SIDEBAR - Green Glassmorphism ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(20, 83, 45, 0.97) 0%, rgba(22, 101, 52, 0.98) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.1);
    }

    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-size: 0.75rem;
        color: rgba(255,255,255,0.6);
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }

    /* ===== SIDEBAR BUTTONS ===== */
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(34, 197, 94, 0.35);
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(34, 197, 94, 0.5);
    }

    /* History item buttons */
    [data-testid="stSidebar"] [data-testid="column"] .stButton > button {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: none;
        font-weight: 400;
        font-size: 0.85rem;
        padding: 0.6rem 1rem;
        border-radius: 10px;
    }

    [data-testid="stSidebar"] [data-testid="column"] .stButton > button:hover {
        background: rgba(255,255,255,0.15);
        transform: none;
        box-shadow: none;
    }

    /* Delete button styling */
    [data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button {
        background: rgba(239, 68, 68, 0.2);
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #fca5a5;
    }

    [data-testid="stSidebar"] [data-testid="column"]:last-child .stButton > button:hover {
        background: rgba(239, 68, 68, 0.3);
    }

    /* ===== CHAT MESSAGES ===== */
    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.8);
        border: 1px solid rgba(34, 197, 94, 0.1);
        border-radius: 20px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    }

    [data-testid="stChatMessage"] p {
        color: #1f2937 !important;
    }

    /* ===== CHAT INPUT - Floating Pill ===== */
    [data-testid="stChatInput"] {
        border-radius: 28px !important;
        border: 2px solid rgba(34, 197, 94, 0.2) !important;
        background: rgba(255,255,255,0.95) !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.08), 0 0 0 1px rgba(34, 197, 94, 0.05) inset;
        padding: 4px !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: rgba(34, 197, 94, 0.5) !important;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1), 0 0 0 3px rgba(34, 197, 94, 0.15);
    }

    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        padding: 12px 20px !important;
        color: #1f2937 !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #9ca3af !important;
    }

    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        margin: 4px !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stChatInput"] button:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 4px 20px rgba(34, 197, 94, 0.5) !important;
    }

    /* ===== SELECTBOX ===== */
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 14px;
        padding: 2px;
    }

    .stSelectbox [data-baseweb="select"] {
        background: transparent;
    }

    /* ===== CHECKBOX ===== */
    .stCheckbox {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
    }

    /* ===== CONTAINERS ===== */
    [data-testid="stContainer"] {
        background: rgba(255,255,255,0.7);
        border: 1px solid rgba(34, 197, 94, 0.1);
        border-radius: 20px;
        padding: 1.25rem;
    }

    /* ===== DIVIDERS ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        margin: 1.75rem 0;
    }

    /* ===== GENERAL ===== */
    .block-container {
        padding-top: 2rem;
        max-width: 900px;
    }

    /* ===== WELCOME TITLE ===== */
    h1 {
        font-weight: 800;
        font-size: 2.5rem;
        background: linear-gradient(135deg, #16a34a 0%, #22c55e 40%, #4ade80 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    /* ===== SUGGESTION CARDS ===== */
    .suggestion-card {
        background: rgba(255,255,255,0.8);
        border: 1px solid rgba(34, 197, 94, 0.15);
        border-radius: 16px;
        padding: 1.25rem;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
    }

    .suggestion-card:hover {
        background: rgba(255,255,255,0.95);
        border-color: rgba(34, 197, 94, 0.4);
        transform: translateY(-2px);
    }

    .suggestion-card h4 {
        color: #1f2937;
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .suggestion-card p {
        color: #6b7280;
        font-size: 0.8rem;
        margin: 0;
    }

    /* ===== CAPTIONS ===== */
    .stCaption {
        color: rgba(255,255,255,0.5) !important;
    }

    /* ===== SUGGESTION BUTTONS ===== */
    .block-container > div > div > div > .stButton > button {
        background: rgba(255,255,255,0.85) !important;
        border: 1px solid rgba(34, 197, 94, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.5rem 1.25rem !important;
        text-align: left !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
        transition: all 0.3s ease !important;
        min-height: 90px !important;
    }

    .block-container > div > div > div > .stButton > button:hover {
        background: rgba(255,255,255,0.98) !important;
        border-color: rgba(34, 197, 94, 0.4) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(34, 197, 94, 0.12) !important;
    }

    .block-container > div > div > div > .stButton > button p {
        margin: 0 !important;
        line-height: 1.5 !important;
        color: #6b7280 !important;
    }

    .block-container > div > div > div > .stButton > button strong {
        color: #1f2937 !important;
        font-size: 0.95rem !important;
    }

    /* ===== TOOLBAR STYLING ===== */
    .input-toolbar {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 8px;
        padding: 8px 0;
        margin-bottom: 4px;
    }

    /* ===== ACTION BUTTON STYLING ===== */
    div[data-testid="stPopover"] > button {
        background: rgba(255,255,255,0.9) !important;
        border: 1px solid rgba(34, 197, 94, 0.2) !important;
        border-radius: 12px !important;
        width: auto !important;
        height: 38px !important;
        min-width: 38px !important;
        padding: 0 12px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        font-size: 1rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
        transition: all 0.2s ease !important;
        color: #374151 !important;
    }

    div[data-testid="stPopover"] > button:hover {
        background: rgba(34, 197, 94, 0.1) !important;
        border-color: rgba(34, 197, 94, 0.4) !important;
        color: #16a34a !important;
    }

    /* ===== MIC BUTTON ===== */
    .mic-btn button {
        background: rgba(255,255,255,0.9) !important;
        border: 1px solid rgba(34, 197, 94, 0.2) !important;
        border-radius: 12px !important;
        height: 38px !important;
        min-width: 38px !important;
        padding: 0 12px !important;
        color: #374151 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
        transition: all 0.2s ease !important;
        font-size: 1rem !important;
    }

    .mic-btn button:hover {
        background: rgba(34, 197, 94, 0.1) !important;
        border-color: rgba(34, 197, 94, 0.4) !important;
        color: #16a34a !important;
    }

    /* Recording state */
    .mic-btn button[kind="secondary"] {
        background: rgba(239, 68, 68, 0.1) !important;
        border-color: rgba(239, 68, 68, 0.4) !important;
        color: #dc2626 !important;
        animation: pulse-rec 1.2s ease-in-out infinite;
    }

    @keyframes pulse-rec {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }

    /* Speech to text iframe */
    iframe[title="streamlit_mic_recorder.speech_to_text"] {
        height: 38px !important;
        width: auto !important;
        min-width: 38px !important;
        border: none !important;
    }

    /* ===== FILE INDICATOR ===== */
    .file-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(34, 197, 94, 0.1);
        border: 1px solid rgba(34, 197, 94, 0.25);
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 0.85rem;
        color: #16a34a;
    }

    /* ===== CLEAR FILE BUTTON ===== */
    .clear-file-btn button {
        background: transparent !important;
        border: none !important;
        color: #6b7280 !important;
        padding: 2px 6px !important;
        font-size: 0.9rem !important;
        min-height: 0 !important;
        height: auto !important;
        box-shadow: none !important;
    }

    .clear-file-btn button:hover {
        color: #1f2937 !important;
        background: transparent !important;
    }

    /* ===== WELCOME TEXT ===== */
    .welcome-text {
        color: #6b7280 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("AI Chat")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_all_chats()
if "uploaded_file_content" not in st.session_state:
    st.session_state.uploaded_file_content = None
if "voice_text" not in st.session_state:
    st.session_state.voice_text = None

# Sidebar
with st.sidebar:
    st.markdown("### Settings")

    available_models = [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4o",
        "anthropic/claude-3.5-sonnet",
        "meta-llama/llama-3-70b-instruct",
        "google/gemini-pro-1.5",
    ]

    st.markdown("#### Compare Chatbots")
    compare_mode = st.checkbox("Enable comparison mode")

    if compare_mode:
        model_1 = st.selectbox("Chatbot 1", available_models, index=0)
        model_2 = st.selectbox("Chatbot 2", available_models, index=1)
    else:
        model = st.selectbox("Select Chatbot", available_models)

    st.divider()

    # New chat button
    if st.button("New Chat", use_container_width=True):
        # Save current chat before starting new one
        if st.session_state.messages and st.session_state.current_chat_id:
            st.session_state.all_chats[st.session_state.current_chat_id]["messages"] = st.session_state.messages
            save_all_chats(st.session_state.all_chats)

        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.divider()
    st.markdown("### History")

    # Display saved chats
    if st.session_state.all_chats:
        for chat_id, chat_data in sorted(st.session_state.all_chats.items(), reverse=True):
            chat_title = chat_data.get("title", "Untitled")[:30]
            col1, col2 = st.columns([4, 1])

            with col1:
                if st.button(f"{chat_title}", key=f"load_{chat_id}", use_container_width=True):
                    # Save current chat first
                    if st.session_state.messages and st.session_state.current_chat_id:
                        st.session_state.all_chats[st.session_state.current_chat_id]["messages"] = st.session_state.messages
                        save_all_chats(st.session_state.all_chats)

                    # Load selected chat
                    st.session_state.current_chat_id = chat_id
                    st.session_state.messages = chat_data.get("messages", [])
                    st.rerun()

            with col2:
                if st.button("X", key=f"del_{chat_id}"):
                    del st.session_state.all_chats[chat_id]
                    save_all_chats(st.session_state.all_chats)
                    if st.session_state.current_chat_id == chat_id:
                        st.session_state.messages = []
                        st.session_state.current_chat_id = None
                    st.rerun()
    else:
        st.caption("No saved chats yet")

# Display chat history or welcome message
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 3rem 0;">
        <p style="color: #6b7280; font-size: 1.1rem; font-weight: 400;">
            How may I help you today?
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Suggestion cards
    col1, col2 = st.columns(2)

    suggestions = [
        ("Explain a concept", "Break down complex topics simply"),
        ("Write code", "Generate code in any language"),
        ("Analyze data", "Help interpret and visualize data"),
        ("Draft content", "Write emails, docs, or creative text"),
    ]

    with col1:
        for i in [0, 2]:
            if st.button(
                f"**{suggestions[i][0]}**\n\n{suggestions[i][1]}",
                key=f"sug_{i}",
                use_container_width=True
            ):
                st.session_state.pending_prompt = suggestions[i][0]
                st.rerun()

    with col2:
        for i in [1, 3]:
            if st.button(
                f"**{suggestions[i][0]}**\n\n{suggestions[i][1]}",
                key=f"sug_{i}",
                use_container_width=True
            ):
                st.session_state.pending_prompt = suggestions[i][0]
                st.rerun()
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Toolbar with action buttons
toolbar_cols = st.columns([1, 1, 8])

with toolbar_cols[0]:
    with st.popover("📎 Attach"):
        st.markdown("**Upload a file**")
        uploaded_file = st.file_uploader(
            "Upload",
            type=["txt", "pdf", "png", "jpg", "jpeg", "gif", "csv", "json", "py", "md"],
            key="file_uploader",
            label_visibility="collapsed"
        )
        if uploaded_file:
            if uploaded_file.type.startswith("image/"):
                st.image(uploaded_file, width=200)
                file_bytes = uploaded_file.read()
                b64_image = base64.b64encode(file_bytes).decode()
                st.session_state.uploaded_file_content = {
                    "type": "image",
                    "name": uploaded_file.name,
                    "data": b64_image,
                    "mime": uploaded_file.type
                }
                st.success("Ready to send!")
            else:
                try:
                    content = uploaded_file.read().decode("utf-8")
                    st.session_state.uploaded_file_content = {
                        "type": "text",
                        "name": uploaded_file.name,
                        "data": content
                    }
                    st.success("Ready to send!")
                except:
                    st.error("Could not read file")

with toolbar_cols[1]:
    st.markdown('<div class="mic-btn">', unsafe_allow_html=True)
    voice_text = speech_to_text(
        language="en",
        start_prompt="🎙️ Voice",
        stop_prompt="⏹️ Stop",
        just_once=True,
        key="voice_input"
    )
    if voice_text:
        st.session_state.voice_text = voice_text
    st.markdown('</div>', unsafe_allow_html=True)

# Show file attachment indicator
if st.session_state.uploaded_file_content:
    file_info = st.session_state.uploaded_file_content
    icon = "🖼️" if file_info["type"] == "image" else "📄"
    indicator_cols = st.columns([8, 1])
    with indicator_cols[0]:
        st.markdown(f'<div class="file-indicator">{icon} {file_info["name"]}</div>', unsafe_allow_html=True)
    with indicator_cols[1]:
        st.markdown('<div class="clear-file-btn">', unsafe_allow_html=True)
        if st.button("✕", key="clear_file", help="Remove"):
            st.session_state.uploaded_file_content = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Handle suggestion card clicks
prompt = None
if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

# Handle voice input
if st.session_state.voice_text:
    prompt = st.session_state.voice_text
    st.session_state.voice_text = None

# Chat input
if not prompt:
    prompt = st.chat_input("Message...")

if prompt:
    if not OPENROUTER_API_KEY:
        st.error("OpenRouter API key not found. Add it to your .env file.")
    else:
        # Create new chat if needed
        if st.session_state.current_chat_id is None:
            chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state.current_chat_id = chat_id
            st.session_state.all_chats[chat_id] = {
                "title": prompt[:50],
                "created": datetime.now().isoformat(),
                "messages": []
            }

        # Add file content to prompt if available
        if st.session_state.uploaded_file_content:
            file_info = st.session_state.uploaded_file_content
            if file_info["type"] == "text":
                prompt = f"{prompt}\n\n📎 **Attached: {file_info['name']}**\n```\n{file_info['data'][:5000]}\n```"
            elif file_info["type"] == "image":
                prompt = f"{prompt}\n\n🖼️ **Attached: {file_info['name']}**"
            st.session_state.uploaded_file_content = None

        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.write(prompt)

        # Get AI response(s)
        if compare_mode:
            # Comparison mode - show two responses side by side
            col1, col2 = st.columns(2)

            with col1:
                with st.container(border=True):
                    st.markdown(f"### {model_1.split('/')[-1]}")
                    with st.spinner("Thinking..."):
                        try:
                            response_1 = ask_ai(st.session_state.messages, model_1)
                            st.write(response_1)
                        except Exception as e:
                            st.error(f"Error: {e}")
                            response_1 = None

            with col2:
                with st.container(border=True):
                    st.markdown(f"### {model_2.split('/')[-1]}")
                    with st.spinner("Thinking..."):
                        try:
                            response_2 = ask_ai(st.session_state.messages, model_2)
                            st.write(response_2)
                        except Exception as e:
                            st.error(f"Error: {e}")
                            response_2 = None

            # Save first model's response to history
            if response_1:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"**{model_1.split('/')[-1]}:** {response_1}\n\n**{model_2.split('/')[-1]}:** {response_2 or 'Error'}"
                })
                st.session_state.all_chats[st.session_state.current_chat_id]["messages"] = st.session_state.messages
                save_all_chats(st.session_state.all_chats)
        else:
            # Single model mode
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = ask_ai(st.session_state.messages, model)
                        st.write(response)
                        # Add assistant response to history
                        st.session_state.messages.append({"role": "assistant", "content": response})

                        # Save chat
                        st.session_state.all_chats[st.session_state.current_chat_id]["messages"] = st.session_state.messages
                        save_all_chats(st.session_state.all_chats)
                    except Exception as e:
                        st.error(f"Error: {e}")
