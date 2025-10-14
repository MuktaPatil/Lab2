"""
Legal News Intelligence Bot - Streamlit Integration
pip install streamlit pandas numpy openai anthropic scikit-learn sentence-transformers
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import openai
import anthropic


class LLMVendor(Enum):
    OPENAI_EXPENSIVE = "gpt-4o"
    OPENAI_CHEAP = "gpt-4o-mini"
    ANTHROPIC_EXPENSIVE = "claude-sonnet-4-20250514"
    ANTHROPIC_CHEAP = "claude-3-5-haiku-20241022"


@dataclass
class NewsItem:
    id: int
    company: str
    date: str
    title: str
    description: str
    url: str
    embedding: np.ndarray = None
    relevance_score: float = 0.0


class NewsEmbedder:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def embed_text(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_news_items(self, news_items: List[NewsItem]) -> List[NewsItem]:
        texts = [f"{item.title} {item.description} {item.company}" 
                 for item in news_items]
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        
        for item, embedding in zip(news_items, embeddings):
            item.embedding = embedding
        
        return news_items


class LegalRelevanceScorer:
    LEGAL_KEYWORDS = {
        'litigation': 5.0, 'lawsuit': 5.0, 'class action': 5.0,
        'investigation': 4.5, 'regulatory': 4.5, 'sec': 4.5,
        'doj': 4.5, 'ftc': 4.5, 'cfpb': 4.5, 'settlement': 4.0,
        'penalty': 4.0, 'fine': 4.0, 'fraud': 4.5, 'breach': 4.0,
        'antitrust': 4.5, 'securities': 4.0, 'compliance': 3.5,
        'merger': 3.5, 'acquisition': 3.5, 'm&a': 3.5,
        'court': 3.0, 'judge': 3.0, 'verdict': 3.5,
        'plaintiff': 3.0, 'defendant': 3.0, 'legal': 2.5,
        'risk': 2.0, 'governance': 2.0, 'audit': 2.0,
        'disclosure': 2.5, 'shareholder': 2.5, 'contract': 2.5,
        'intellectual property': 3.0, 'patent': 2.5, 'trademark': 2.0
    }
    
    def calculate_relevance(self, news_item: NewsItem) -> float:
        text = f"{news_item.title} {news_item.description}".lower()
        score = 0.0
        
        for keyword, weight in self.LEGAL_KEYWORDS.items():
            if keyword in text:
                score += weight
        
        # Financial institution boost
        if any(term in text for term in ['bank', 'financial', 'securities', 'investment']):
            score *= 1.2
        
        # Recency boost
        try:
            days_old = (datetime.now() - datetime.fromisoformat(
                news_item.date.replace('+00:00', ''))).days
            recency_factor = max(0.5, 1.0 - (days_old / 365))
            score *= recency_factor
        except:
            pass
        
        return round(score, 2)


class NewsRAGSystem:
    def __init__(self, df: pd.DataFrame):
        self.news_items = self._load_news(df)
        self.embedder = NewsEmbedder()
        self.scorer = LegalRelevanceScorer()
        
        with st.spinner('🧠 Creating embeddings...'):
            self.news_items = self.embedder.embed_news_items(self.news_items)
        
        with st.spinner('⚖️ Calculating legal relevance...'):
            for item in self.news_items:
                item.relevance_score = self.scorer.calculate_relevance(item)
    
    def _load_news(self, df: pd.DataFrame) -> List[NewsItem]:
        news_items = []
        for idx, row in df.iterrows():
            title = row.get('Document', row.get('Title', ''))
            description = row.get('Description', '')
            
            if 'Description:' in title:
                parts = title.split('Description:', 1)
                title = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else description
            
            news_items.append(NewsItem(
                id=idx,
                company=row.get('company_name', row.get('Company', '')),
                date=str(row.get('Date', '')),
                title=title,
                description=description,
                url=row.get('URL', '')
            ))
        
        return news_items
    
    def retrieve_relevant_news(self, query: str, top_k: int = 10) -> List[NewsItem]:
        query_embedding = self.embedder.embed_text(query)
        embeddings = np.array([item.embedding for item in self.news_items])
        similarities = cosine_similarity([query_embedding], embeddings)[0]

        scored_items = []
        for similarity, item in zip(similarities, self.news_items):
            combined = (0.6 * similarity) + (0.4 * min(item.relevance_score / 10, 1.0))
            scored_items.append((combined, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)

        seen = set()
        unique_items = []
        for score, item in scored_items:
            key = getattr(item, "url", item.title).strip().lower()
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
            if len(unique_items) >= top_k:
                break

        return unique_items
    def get_most_interesting(self, top_k: int = 10):
        """
        Returns top_k most interesting news items based on relevance scores.
        """
        sorted_items = sorted(self.news_items, key=lambda x: x.relevance_score, reverse=True)
        seen_titles = set()
        unique_items = []
        for item in sorted_items:
            if item.title not in seen_titles:
                seen_titles.add(item.title)
                unique_items.append(item)
            if len(unique_items) >= top_k:
                break
        return unique_items

class LLMQueryEngine:
    def __init__(self, vendor: LLMVendor, api_key: str):
        self.vendor = vendor
        
        if vendor.name.startswith('OPENAI'):
            self.client = openai.OpenAI(api_key=api_key)
        elif vendor.name.startswith('ANTHROPIC'):
            self.client = anthropic.Anthropic(api_key=api_key)
    
    def query(self, context: str, question: str) -> Dict:
        system_prompt = """You are a legal news analyst for a global law firm. 
Analyze news articles and provide insights on legal implications, regulatory risks, 
and potential impact on clients. Be concise but thorough."""
        
        user_prompt = f"""Based on the following news articles, {question}

NEWS ARTICLES:
{context}

Provide a clear, actionable analysis for law firm partners."""
        
        if self.vendor.name.startswith('OPENAI'):
            response = self.client.chat.completions.create(
                model=self.vendor.value,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return {
                'response': response.choices[0].message.content,
                'tokens': {
                    'input': response.usage.prompt_tokens,
                    'output': response.usage.completion_tokens,
                    'total': response.usage.total_tokens
                },
                'model': self.vendor.value
            }
        
        elif self.vendor.name.startswith('ANTHROPIC'):
            response = self.client.messages.create(
                model=self.vendor.value,
                max_tokens=1500,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            return {
                'response': response.content[0].text,
                'tokens': {
                    'input': response.usage.input_tokens,
                    'output': response.usage.output_tokens,
                    'total': response.usage.input_tokens + response.usage.output_tokens
                },
                'model': self.vendor.value
            }


class NewsBot:
    def __init__(self, df: pd.DataFrame):
        self.rag = NewsRAGSystem(df)
        
    def _format_news_context(self, news_items: List[NewsItem]) -> str:
        context = []
        for i, item in enumerate(news_items, 1):
            context.append(f"""
Article {i}:
Company: {item.company}
Date: {item.date}
Title: {item.title}
Description: {item.description}
Legal Relevance Score: {item.relevance_score}
URL: {item.url}
""")
        return "\n".join(context)
    
    def find_interesting_news(self, vendor: LLMVendor, api_key: str, top_k: int = 10) -> Dict:
        news_items = self.rag.get_most_interesting(top_k)
        context = self._format_news_context(news_items)
        
        engine = LLMQueryEngine(vendor, api_key)
        question = "rank and explain why these are the most legally significant news items."
        
        result = engine.query(context, question)
        result['news_items'] = news_items
        return result
    
    def find_news_about(self, topic: str, vendor: LLMVendor, api_key: str, top_k: int = 10) -> Dict:
        news_items = self.rag.retrieve_relevant_news(topic, top_k)
        context = self._format_news_context(news_items)
        
        engine = LLMQueryEngine(vendor, api_key)
        question = f"analyze the news related to '{topic}' and highlight key legal considerations."
        
        result = engine.query(context, question)
        result['news_items'] = news_items
        return result


# ===== STREAMLIT APP =====

def main():
    st.set_page_config(page_title="Legal News Bot", page_icon="⚖️", layout="wide")
    
    st.title("⚖️ Legal News Intelligence Bot")
    st.markdown("*AI-powered news analysis for global law firms*")
    
    # Sidebar for configuration
    with st.sidebar:

        st.header("Model Selection")

        vendor_options = {
            "OpenAI GPT-4o (Most Powerful)": LLMVendor.OPENAI_EXPENSIVE,
            "OpenAI GPT-4o-mini (Fast & Cheap)": LLMVendor.OPENAI_CHEAP,
            "Claude 4 Latest (Best Legal Analysis)": LLMVendor.ANTHROPIC_EXPENSIVE,
            "Claude 3.5 Haiku (Balanced)": LLMVendor.ANTHROPIC_CHEAP,
        }

        selected_model = st.selectbox("Choose Model", list(vendor_options.keys()))
        vendor = vendor_options[selected_model]

        st.markdown("---")
        st.header("📊 Settings")
        top_k = st.slider("Number of articles to analyze", 3, 20, 10)
    
    # Hardcoded CSV path - change this to your file path
    CSV_PATH = "/workspaces/Lab2/Example_news_info_for_testing.csv" 
    
    try:
        df = pd.read_csv(CSV_PATH)
        df = df.drop_duplicates(subset=["URL"], keep="first")
        if "Document" in df.columns:
            df = df.drop_duplicates(subset=["Document"], keep="first")

        st.success(f"✅ Loaded {len(df)} news articles from {CSV_PATH}")
        
        # Initialize bot
        if 'bot' not in st.session_state:
            with st.spinner('Initializing News Bot...'):
                st.session_state.bot = NewsBot(df)
        
        bot = st.session_state.bot
        
        # Main interface
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["🔥 Most Interesting", "🔍 Search by Topic", "📊 Browse All"])
        
        with tab1:
            st.header("Most Legally Significant News")
            
            if st.button("🎯 Find Most Interesting News", use_container_width=True):
                # Validate API key
                api_key = None
                if vendor.name.startswith('OPENAI'):
                    api_key = st.secrets["openai_api_key"]
                elif vendor.name.startswith('ANTHROPIC'):
                    api_key = st.secrets["claude_api_key"]
                else:
                    st.error("❌ Unsupported LLM vendor selected")
                    return
                
                with st.spinner('Analyzing news with AI...'):
                    result = bot.find_interesting_news(vendor, api_key, top_k)
                
                # Display analysis
                st.subheader("AI Analysis")
                st.markdown(result['response'])
                
                # Display tokens
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Input Tokens", result['tokens']['input'])
                with col2:
                    st.metric("Output Tokens", result['tokens']['output'])
                with col3:
                    st.metric("Total Tokens", result['tokens']['total'])
                
                # Display articles
                st.subheader("📰 Top Articles")
                for i, item in enumerate(result['news_items'], 1):
                    with st.expander(f"#{i} - {item.company}: {item.title[:80]}... (Score: {item.relevance_score})"):
                        st.markdown(f"**Company:** {item.company}")
                        st.markdown(f"**Date:** {item.date}")
                        st.markdown(f"**Relevance Score:** {item.relevance_score}")
                        st.markdown(f"**Description:** {item.description}")
                        st.markdown(f"**URL:** [{item.url}]({item.url})")
        
        with tab2:
            st.header("Search News by Topic")
            
            topic = st.text_input("🔍 Enter topic (e.g., 'regulatory investigation', 'AI in finance')", 
                                 placeholder="CFPB compliance")
            
            if st.button("🔎 Search", use_container_width=True) and topic:
                # Validate API key
                api_key = None
                if vendor.name.startswith('OPENAI'):
                    api_key = st.session_state.get('openai_key')
                    if not api_key:
                        st.error("❌ Please enter OpenAI API key in sidebar")
                        return
                elif vendor.name.startswith('ANTHROPIC'):
                    api_key = st.session_state.get('anthropic_key')
                    if not api_key:
                        st.error("❌ Please enter Anthropic API key in sidebar")
                        return
                
                with st.spinner(f'🔍 Searching for news about "{topic}"...'):
                    result = bot.find_news_about(topic, vendor, api_key, top_k)
                
                # Display analysis
                st.subheader("📝 AI Analysis")
                st.markdown(result['response'])
                
                # Display tokens
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Input Tokens", result['tokens']['input'])
                with col2:
                    st.metric("Output Tokens", result['tokens']['output'])
                with col3:
                    st.metric("Total Tokens", result['tokens']['total'])
                
                # Display articles
                st.subheader(f"📰 Articles about '{topic}'")
                for i, item in enumerate(result['news_items'], 1):
                    with st.expander(f"#{i} - {item.company}: {item.title[:80]}..."):
                        st.markdown(f"**Company:** {item.company}")
                        st.markdown(f"**Date:** {item.date}")
                        st.markdown(f"**Relevance Score:** {item.relevance_score}")
                        st.markdown(f"**Description:** {item.description}")
                        st.markdown(f"**URL:** [{item.url}]({item.url})")
        
        with tab3:
            st.header("Browse All News")
            
            # Get all items sorted by relevance
            all_items = sorted(bot.rag.news_items, 
                             key=lambda x: x.relevance_score, 
                             reverse=True)
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                companies = sorted(list(set([item.company for item in all_items])))
                selected_company = st.selectbox("Filter by Company", ["All"] + companies)
            
            with col2:
                min_score = st.slider("Minimum Relevance Score", 0.0, 10.0, 0.0)
            
            # Apply filters
            filtered_items = all_items
            if selected_company != "All":
                filtered_items = [item for item in filtered_items if item.company == selected_company]
            filtered_items = [item for item in filtered_items if item.relevance_score >= min_score]
            
            st.info(f"Showing {len(filtered_items)} articles")
            
            # Display articles
            for i, item in enumerate(filtered_items[:50], 1):  # Limit to 50 for performance
                with st.expander(f"#{i} - {item.company}: {item.title[:80]}... (Score: {item.relevance_score})"):
                    st.markdown(f"**Company:** {item.company}")
                    st.markdown(f"**Date:** {item.date}")
                    st.markdown(f"**Relevance Score:** {item.relevance_score}")
                    st.markdown(f"**Description:** {item.description}")
                    st.markdown(f"**URL:** [{item.url}]({item.url})")
    
    except FileNotFoundError:
        st.error(f"❌ Could not find CSV file at: {CSV_PATH}")
        st.info("Please update the CSV_PATH variable at the top of the main() function")
    except Exception as e:
        st.error(f"❌ Error loading CSV: {str(e)}")


if __name__ == "__main__":
    main()