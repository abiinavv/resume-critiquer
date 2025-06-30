import streamlit as st
import PyPDF2
import io
import os
import openai
import httpx

# Use st.secrets when deployed, else fallback to local .env
api_key = st.secrets["OPENROUTER_API_KEY"] if "OPENROUTER_API_KEY" in st.secrets else os.getenv("OPENROUTER_API_KEY")

# Configure OpenAI client to use OpenRouter
client = openai.OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
   http_client=httpx.Client(
    headers={
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://resume-critiquer-5zcvi8qmd5b54l7aung8no.streamlit.app",
        "X-Title": "AI Resume Critiquer"
    }
)

)

# Streamlit UI setup
st.set_page_config(page_title="AI Resume Critiquer", page_icon="📃", layout="centered")
st.title("📃 AI Resume Critiquer")
st.markdown("Upload your resume and get AI-powered feedback tailored to your needs!")

# Upload & input
uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role you're targeting (optional)")
analyze = st.button("Analyze Resume")

# PDF extraction
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

# PDF/TXT handler
def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    return uploaded_file.read().decode("utf-8")

# Resume Analysis Logic
if analyze and uploaded_file:
    try:
        file_content = extract_text_from_file(uploaded_file)

        if not file_content.strip():
            st.error("❌ The file does not contain any readable text.")
            st.stop()

        prompt = f"""Please analyze this resume and provide constructive feedback. 
Focus on the following aspects:
1. Content clarity and impact
2. Skills presentation
3. Experience descriptions
4. Specific improvements for {job_role if job_role else 'general job applications'}

Resume content:
{file_content}

Please provide your analysis in a clear, structured format with specific recommendations."""

        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "system", "content": "You are an expert resume reviewer with years of experience in HR and recruitment."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        st.markdown("### 📝 Analysis Results")
        st.markdown(response.choices[0].message.content)

    except Exception as e:
        if "401" in str(e):
            st.error("❌ Authorization failed. Check your API key and HTTP-Referer.")
        elif "quota" in str(e).lower():
            st.error("❌ Quota exceeded. Please check your OpenRouter account.")
        else:
            st.error(f"❌ An error occurred: {str(e)}")
