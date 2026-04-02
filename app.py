import streamlit as st
import PyPDF2
from pymongo import MongoClient
from google import genai
from google.genai import types

st.set_page_config(page_title="Souhail ai", page_icon="🎓", layout="centered")

# --- COLOR PALETTE THEMING ---
suptech_cyan = "#01B6CF"   
suptech_blue = "#1F8EA0"   

# 1. Initialize the theme state
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# 2. Add the toggle switch to the sidebar
with st.sidebar:
    is_dark = st.toggle("🌙 Dark Mode", value=(st.session_state.theme == "dark"))
    if is_dark:
        st.session_state.theme = "dark"
    else:
        st.session_state.theme = "light"

# 3. Define your Suptech Colors
suptech_cyan = "#BB4D1A"   
suptech_blue = "#9AE630"   

# 4. Inject different CSS depending on the toggle state
if st.session_state.theme == "light":
    # --- LIGHT MODE CSS ---
    st.markdown(f"""
    <style>
    /* Main Backgrounds & Text */
    .stApp {{ background-color: #FFFFFF !important; color: #31333F !important; }}
    p, div[data-testid="stChatMessageContent"], .stMarkdown {{ color: #31333F !important; }}
    [data-testid="stSidebar"] {{ background-color: #F8FDFF !important; }}
    h1, h2, h3 {{ color: {suptech_blue} !important; }}
    
    /* Buttons */
    [data-testid="stAppViewContainer"] div[role="radiogroup"] {{ accent-color: {suptech_cyan}; }}
    div.stButton > button {{ background-color: {suptech_cyan} !important; color: white !important; border: none !important; }}
    div.stButton > button:hover {{ background-color: {suptech_blue} !important; color: white !important; }}
    
    /* FIX: Top Header */
    [data-testid="stHeader"] {{ background-color: #FFFFFF !important; }}
    
    /* FIX: Input Boxes (Password) */
    div[data-baseweb="input"] {{ background-color: #F0F2F6 !important; border-color: #D5D8E2 !important; }}
    div[data-baseweb="input"] input {{ color: #31333F !important; }}
    
    /* FIX: Bottom Container (The black bar around chat input) */
    [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {{ background-color: #FFFFFF !important; }}
    
    /* FIX: Chat Input Area */
    [data-testid="stChatInput"] {{ background-color: #FFFFFF !important; }}
    [data-testid="stChatInput"] > div {{ background-color: #F0F2F6 !important; border-color: #D5D8E2 !important; }}
    [data-testid="stChatInput"] textarea {{ color: #31333F !important; -webkit-text-fill-color: #31333F !important; }}
    [data-testid="stChatInput"] button {{ color: #31333F !important; }}
    
    /* FIX: File Uploader */
    [data-testid="stFileUploader"] section {{ background-color: #F0F2F6 !important; }}
    [data-testid="stFileUploader"] section * {{ color: #31333F !important; }}
    [data-testid="stFileUploader"] button {{ background-color: #FFFFFF !important; color: #31333F !important; border: 1px solid #D5D8E2 !important; }}
    </style>
    """, unsafe_allow_html=True)

else:
    # --- DARK MODE CSS ---
    st.markdown(f"""
    <style>
    /* Main Backgrounds & Text */
    .stApp {{ background-color: #0E1117 !important; color: #FAFAFA !important; }}
    p, div[data-testid="stChatMessageContent"], .stMarkdown {{ color: #FAFAFA !important; }}
    [data-testid="stSidebar"] {{ background-color: #262730 !important; }}
    h1, h2, h3 {{ color: {suptech_cyan} !important; }}
    
    /* Buttons */
    [data-testid="stAppViewContainer"] div[role="radiogroup"] {{ accent-color: {suptech_cyan}; }}
    div.stButton > button {{ background-color: {suptech_cyan} !important; color: white !important; border: none !important; }}
    div.stButton > button:hover {{ background-color: {suptech_blue} !important; color: white !important; }}
    
    /* FIX: Top Header */
    [data-testid="stHeader"] {{ background-color: #0E1117 !important; }}
    
    /* FIX: Input Boxes (Password) */
    div[data-baseweb="input"] {{ background-color: #262730 !important; border-color: #4B4C53 !important; }}
    div[data-baseweb="input"] input {{ color: #FAFAFA !important; }}
    
    /* FIX: Bottom Container (The black bar around chat input) */
    [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {{ background-color: #0E1117 !important; }}
    
    /* FIX: Chat Input Area */
    [data-testid="stChatInput"] {{ background-color: #0E1117 !important; }}
    [data-testid="stChatInput"] textarea {{ color: #FAFAFA !important; }}
    
    /* FIX: File Uploader */
    [data-testid="stFileUploader"] section {{ background-color: #262730 !important; }}
    [data-testid="stFileUploader"] section * {{ color: #FAFAFA !important; }}
    [data-testid="stFileUploader"] button {{ background-color: #0E1117 !important; color: #FAFAFA !important; border: 1px solid #4B4C53 !important; }}
    </style>
    """, unsafe_allow_html=True)
    
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center;'>🔒 Souhail AI Access</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please enter the class password to access the AI tutor.</p>", unsafe_allow_html=True)
    
    pwd = st.text_input("Password", type="password", placeholder="Enter password here...")
    
    if st.button("Login", use_container_width=True):
        if pwd == st.secrets["pwd"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password. Try again.")
            
    st.stop() 

MONGO_URI = st.secrets["MONGO_URI"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

@st.cache_resource
def init_db():
    client = MongoClient(MONGO_URI)
    return client["suptech_courses"]["materials"]

collection = init_db()
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

st.title("🎓 Souhail's Suptech AI Tutor")
st.markdown("ask the database or upload your own notes below.")

with st.sidebar:
    try:
        st.image("logo_new.png", width="stretch")
    except FileNotFoundError:
        pass
        
    st.divider()
    
    st.header("📂 your notes")
    uploaded_file = st.file_uploader("pdf only", type="pdf")
    
    user_pdf_text = ""
    if uploaded_file:
        uploaded_file.seek(0)
        with st.spinner("reading..."):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                ext = page.extract_text()
                if ext:
                    user_pdf_text += ext + "\n"
        st.success("done")
    
    st.divider()

    if st.button("📝 generate quiz"):
        with st.spinner("creating quiz..."):
            if user_pdf_text:
                quiz_prompt = f"generate a 5-question multiple choice quiz based strictly on these uploaded notes: {user_pdf_text}. provide answers at the end without citations."
            else:
                results = collection.find().limit(10)
                quiz_context = "\n".join([doc["text"] for doc in results])
                quiz_prompt = f"generate a 5-question multiple choice quiz based on these course notes: {quiz_context}. provide answers at the end without citations."

            try:
                quiz_res = gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=quiz_prompt
                )
                st.session_state.messages.append({"role": "assistant", "content": quiz_res.text, "sources": ""})
                st.rerun()
            except Exception as e:
                if "429" in str(e):
                    st.error("google api speed limit hit! wait about 30 seconds and try again.")
                else:
                    st.error(f"error: {e}")

    st.divider()

    if st.button("🗑️ clear chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "welcome to the suptech ai tutor! 👋 upload your notes on the left or ask me a question about the course to get started.", "sources": ""}
        ]
        st.rerun()

    st.divider()
    
    st.markdown("""
        <div style='text-align: center; color: gray; font-size: 13px; margin-top: 20px;'>
            © 2026 souhail hafidi<br>
            filière: <b>GDIAS</b>
        </div>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "welcome to the suptech ai tutor! 👋 upload your notes on the left or ask me a question about the course to get started.", "sources": ""}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 Sources used"):
                st.markdown(f"<div style='font-size: 12px; color: gray;'>{msg['sources']}</div>", unsafe_allow_html=True)

quick_prompt = None
c1, c2, c3 = st.columns(3)
if c1.button("📝 summarize notes", use_container_width=True): 
    quick_prompt = "Please summarize the core concepts from the notes."
if c2.button("🧠 explain like i'm 5", use_container_width=True): 
    quick_prompt = "Explain the main topic of these notes simply, like I'm 5 years old."
if c3.button("🗂️ create flashcards", use_container_width=True): 
    quick_prompt = "Create 3 study flashcards based on the notes (Q & A format)."

user_query = st.chat_input("ask something...")
final_query = user_query or quick_prompt

if final_query:
    with st.chat_message("user"):
        st.markdown(final_query)
    st.session_state.messages.append({"role": "user", "content": final_query})

    with st.chat_message("assistant"):
        with st.spinner("thinking..."):
            try:
                embed_response = gemini_client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=final_query,
                )
                query_vector = embed_response.embeddings[0].values

                results = collection.aggregate([
                    {
                        "$vectorSearch": {
                            "index": "default", 
                            "path": "embedding",
                            "queryVector": query_vector,
                            "numCandidates": 50,
                            "limit": 3
                        }
                    }
                ])
                
                context_text = "\n\n".join([doc["text"] for doc in results])

                history_string = ""
                for msg in st.session_state.messages[-5:-1]: 
                    history_string += f"{msg['role']}: {msg['content']}\n"

                prompt = f"""
                you are a chill tutor for suptech students.
                use the provided notes to answer. 
                
                IMPORTANT: 
                - DO NOT mention professors' names, page numbers, or file names.
                - DO NOT cite sources for 'db notes'. Just give the answer naturally.
                - ONLY if you use 'uploaded notes', you can say 'based on your file'.
                - keep the tone helpful and direct.
                
                db notes:
                {context_text}
                
                uploaded notes:
                {user_pdf_text}

                recent chat history:
                {history_string}
                
                question: {final_query}
                """
                
                response = gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[{"google_search": {}}],
                    )
                )
                
                st.markdown(response.text)
                
                if context_text.strip():
                    with st.expander("📚 Sources used"):
                        st.markdown(f"<div style='font-size: 12px; color: gray;'>{context_text}</div>", unsafe_allow_html=True)
                        
                st.session_state.messages.append({"role": "assistant", "content": response.text, "sources": context_text})
                
            except Exception as e:
                if "429" in str(e):
                    st.warning("whoa, too many questions too fast! google's free tier needs a quick breather. try again in 30 seconds.")
                else:
                    st.error(f"app error: {e}")
