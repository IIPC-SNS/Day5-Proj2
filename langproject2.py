import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from PyPDF2 import PdfReader
import docx
from gtts import gTTS
import tempfile
import os

# --- API Key (Hardcoded as requested) ---
GOOGLE_API_KEY = "AIzaSyCu0xOzKGNJi1NDuBYGiqT-4ytjwQu-G94"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# --- Page Config ---
st.set_page_config(page_title="📄 Doc Translator + Q&A", page_icon="🗣️")

# --- Title ---
st.title("📄🔁 Doc Translator + Q&A Assistant")
st.markdown("Upload a **PDF or Word document**, translate to **French audio**, and ask questions about its content.")

# --- File Upload ---
uploaded_file = st.file_uploader("📁 Upload PDF or DOCX file", type=["pdf", "docx"])

doc_text = ""

# --- Extract Text from PDF or DOCX ---
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            doc_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif uploaded_file.name.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            doc_text = "\n".join([p.text for p in doc.paragraphs])
        else:
            st.error("Unsupported file format.")
    except Exception as e:
        st.error(f"Error reading file: {e}")

# --- Display Text Summary ---
if doc_text:
    st.success("✅ Text extracted successfully!")
    st.text_area("📄 Extracted Text (Editable)", value=doc_text, height=200)

# --- Translate to French and generate audio ---
if st.button("🔊 Translate to French & Generate Audio"):
    if not doc_text.strip():
        st.warning("Please upload a valid file first.")
    else:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.7)

            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a translator that converts English to French."),
                ("user", "Translate the following content into French: {sentence}")
            ])
            chain: Runnable = prompt | llm
            response = chain.invoke({"sentence": doc_text})
            translated = response.content.strip()

            st.success("✅ Translation complete!")
            st.markdown(f"**French Translation:**\n\n{translated}")

            # Text to Speech
            tts = gTTS(text=translated, lang='fr')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tts.save(tmp_file.name)
                st.audio(tmp_file.name, format="audio/mp3")

        except Exception as e:
            st.error(f"Translation or audio generation failed: {e}")

# --- Query Box ---
st.divider()
st.header("❓ Ask something about your document")
query = st.text_input("🔍 Enter your question here")

if st.button("💬 Answer"):
    if not doc_text:
        st.warning("Please upload and extract a document first.")
    elif not query.strip():
        st.warning("Please enter a valid question.")
    else:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.3)

            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant. Use the given document to answer questions."),
                ("user", "Document: {document}\n\nQuestion: {question}")
            ])
            chain: Runnable = prompt | llm
            response = chain.invoke({"document": doc_text, "question": query})
            st.success("✅ Answer retrieved!")
            st.markdown(f"**Answer:**\n\n{response.content.strip()}")

        except Exception as e:
            st.error(f"Error answering question: {e}")
