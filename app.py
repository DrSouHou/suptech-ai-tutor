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

st.title("🎓 Souhail's Suptech AI Tutor")
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

    if st.button("📝 generate quiz"):
        with st.spinner("creating quiz..."):
            if user_pdf_text:
                quiz_prompt = f"generate a 5-question multiple choice quiz based strictly on these uploaded notes: {user_pdf_text}. provide answers at the end without citations."
            else:
                results = collection.find().limit(10)
                quiz_context = "\n".join([doc["text"] for doc in results])
                quiz_prompt = f"generate a 5-question multiple choice quiz based on these course notes: {quiz_context}. provide answers at the end without citations."

            quiz_res = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=quiz_prompt
            )
            st.session_state.messages.append({"role": "assistant", "content": quiz_res.text})
            st.rerun()

    st.divider()
    
    st.markdown("""
        <div style='text-align: center; color: gray; font-size: 13px; margin-top: 20px;'>
            © 2026 souhail hafidi<br>
            filière: <b>GDIAS</b>
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

            history_string = ""
            for msg in st.session_state.messages[-5:-1]: 
                history_string += f"{msg['role']}: {msg['content']}\n"

            prompt = f"""
            you are a chill tutor for suptech students.
            use the provided notes to answer. 
            
            IMPORTANT: 
            - DO NOT mention 'Pr I.DEBBARH', page numbers, or specific file names.
            - DO NOT cite sources for 'db notes'. Just give the answer naturally.
            - ONLY if you use 'uploaded notes', you can say 'based on your file'.
            - keep the tone helpful and direct.
            
            db notes:
            {context_text}
            
            uploaded notes:
            {user_pdf_text}

            recent chat history:
            {history_string}
            
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
