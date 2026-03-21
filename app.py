import streamlit as st
import PyPDF2
from pymongo import MongoClient
from google import genai
from google.genai import types

MONGO_URI = st.secrets["MONGO_URI"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# connect to db
@st.cache_resource
def init_db():
    client = MongoClient(MONGO_URI)
    return client["suptech_courses"]["materials"]

collection = init_db()
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

st.title("suptech ai tutor")
st.caption("ask about courses or upload your own notes")

# sidebar for custom files
with st.sidebar:
    st.write("upload specific notes/slides here")
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

# chat history
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
            # get vector
            embed_response = gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=user_query,
            )
            query_vector = embed_response.embeddings[0].values

            # search db
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
