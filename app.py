import streamlit as st
import PyPDF2
from pymongo import MongoClient
from google import genai
from google.genai import types

st.set_page_config(page_title="suptech ai", page_icon="🎓", layout="centered")

MONGO_URI = st.secrets["MONGO_URI"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

@st.cache_resource
def init_db():
    client = MongoClient(MONGO_URI)
    return client["suptech_courses"]["materials"]

collection = init_db()
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

st.title("🎓 suptech ai tutor")
st.markdown("ask the database or upload your own notes below.")

with st.sidebar:
    try:
        st.image("log_suptech.png", use_container_width=True)
    except FileNotFoundError:
        pass
        
    st.divider()
    
    st.header("📂 your notes")
    uploaded_file = st.file_uploader("pdf only", type="pdf")
    
    user_pdf_text = ""
    if uploaded_file:
        with st.spinner("reading..."):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                ext = page.extract_text()
                if ext:
                    user_pdf_text += ext + "\n"
        st.success("done")
        
    st.divider()
    
    st.markdown("""
        <div style='text-align: center; color: gray; font-size: 13px; margin-top: 20px;'>
            © 2026 souhail hafidi<br>
            filière: <b>[GDIAS]</b>
        </div>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input("ask something...")

if user_query:
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("assistant"):
        with st.spinner("thinking..."):
            embed_response = gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=user_query,
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

            prompt = f"""
            answer the student's question using the course notes. 
            prioritize the user's uploaded notes if they exist.
            use google search if needed.
            
            db notes:
            {context_text}
            
            uploaded notes:
            {user_pdf_text}
            
            question: {user_query}
            """
            
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],
                )
            )
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
