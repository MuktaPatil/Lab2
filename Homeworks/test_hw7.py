import pandas as pd
from hw_7 import NewsBot, NewsItem, LegalRelevanceScorer

if __name__ == "__main__":
    df = pd.read_csv("/workspaces/Lab2/Example_news_info_for_testing.csv")
    bot = NewsBot(df)
    
    print("\n" + "="*50)
    print("QUICK VALIDATION TEST")
    print("="*50)
    
    top_items = bot.rag.get_most_interesting(10)
    for i, item in enumerate(top_items, 1):
        print(f"\n#{i} - Score: {item.relevance_score}")
        print(f"Company: {item.company}")
        print(f"Title: {item.title}")