import streamlit as st
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

st.title("Suptech AI Tutor 🎓")
st.caption("Answers using your course PDFs + live Google Search")

# store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# chat input
user_query = st.chat_input("ask something about the course...")

if user_query:
    # show user message
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    with st.chat_message("assistant"):
        with st.spinner("thinking..."):
            # 1. turn the user's question into a vector
            embed_response = gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=user_query,
            )
            query_vector = embed_response.embeddings[0].values

            # 2. search mongo for the 3 most relevant chunks
            # NOTE: your atlas search index must be named "default"
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
            
            # 3. bundle the pdf text together
            context_text = "\n\n".join([doc["text"] for doc in results])

            # 4. ask gemini (with google search enabled!)
            prompt = f"""
            You are a helpful tutor for Suptech students. 
            Use the following course notes to answer the question. 
            If the notes don't have the answer, use Google Search.
            
            Course Notes:
            {context_text}
            
            Student Question: {user_query}
            """
            
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}], # turns on live web search
                )
            )
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})