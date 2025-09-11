import streamlit as st
import requests
from bs4 import BeautifulSoup
import anthropic
import google.generativeai as genai
from openai import OpenAI

st.set_page_config(
    page_title="HW2 – URL Summarizer",
    page_icon="🧠",
    layout="wide"
)
st.title("HW2 – URL Summarizer using various LLMs")
st.caption("Enter a URL, choose summary type, output language, and LLM provider.")

def read_url_content(url: str):
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text(separator=" ", strip=True)
    except requests.RequestException as e:
        st.error(f"Error reading {url}: {e}")
        return None

def generate_openai_summary(text, language, summary_type, advanced=False):
    try:
        api_key = st.secrets.get("openai_api_key")
        if not api_key:
            st.error("OpenAI API key not found in secrets.toml")
            return None
        client = OpenAI(api_key=api_key)
        model = "gpt-4o" if advanced else "gpt-4o-mini"
        prompt = f"""
        Summarize the following web content in {language}.
        Summary type: {summary_type}

        Content:
        {text[:12000]}

        Provide the summary in {language} language.
        """
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        return None

def generate_gemini_summary(text, language, summary_type, advanced=False):
    try:
        api_key = st.secrets.get("gemini_api_key")
        if not api_key:
            st.error("Gemini API key not found in secrets.toml")
            return None
        genai.configure(api_key=api_key)
        model = "gemini-2.5-pro" if advanced else "gemini-2.5-flash"
        prompt = f"""
        Summarize the following web content in {language}.
        Summary type: {summary_type}

        Content:
        {text[:12000]}

        Provide the summary in {language} language.
        """
        model_obj = genai.GenerativeModel(model)
        resp = model_obj.generate_content(prompt)
        return resp.text if hasattr(resp, "text") else str(resp)
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return None

def generate_claude_summary(text, language, summary_type, advanced=False):
    try:
        api_key = st.secrets.get("claude_api_key") or st.secrets.get("anthropic", {}).get("api_key")
        if not api_key:
            st.error("Claude API key not found in secrets.toml")
            return None
        client = anthropic.Anthropic(api_key=api_key)
        model = "claude-opus-4-20250514" if advanced else "claude-3-haiku-20240307"
        prompt = f"""
        Summarize the following web content in {language}.
        Summary type: {summary_type}

        Content:
        {text[:12000]}

        Provide the summary in {language} language.
        """
        message = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0.7,
            system="You are a helpful assistant that provides concise summaries.",
            messages=[{"role": "user", "content": prompt}]
        )
        return "".join([c.text for c in message.content if c.type == "text"])
    except Exception as e:
        st.error(f"Claude API Error: {e}")
        return None

def call_llm(provider: str, text: str, language: str, summary_type: str, advanced: bool) -> str:
    if provider == "OpenAI":
        return generate_openai_summary(text, language, summary_type, advanced)
    elif provider == "Gemini":
        return generate_gemini_summary(text, language, summary_type, advanced)
    elif provider == "Claude":
        return generate_claude_summary(text, language, summary_type, advanced)
    else:
        return "Unknown provider"

with st.sidebar:
    summary_type = st.selectbox(
        "Summary type",
        ["TL;DR (3–5 sentences)", "Bulleted key takeaways", "Executive brief"]
    )
    use_advanced = st.checkbox("Use advanced model", value=True)
    provider = st.selectbox("LLM Provider", ["OpenAI", "Gemini", "Claude"])

url = st.text_input("🔗 Enter a web page URL", placeholder="https://example.com/article")

out_lang = st.selectbox("Output language", ["English", "French", "Spanish", "German", "Hindi"])

if url:
    content = read_url_content(url)
    if content:
        st.write(f"### Using {provider} – {'advanced' if use_advanced else 'simple'}")
        if st.button("Generate Summary"):
            with st.spinner("Generating summary..."):
                summary = call_llm(provider, content, out_lang, summary_type, use_advanced)
                if summary:
                    st.subheader("📄 Summary")
                    st.write(summary)
