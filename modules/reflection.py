from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

model = ChatGoogleGenerativeAI(
    model=os.getenv('MODEL'),
    temperature=0,
    google_api_key=os.getenv('GOOGLE_AI_API_KEY')
)

def low_level_reflection(news_summary: str, price_trend: str):
    """
    Analyze correlation between news and price.
    """
    prompt = f"""
    Perform a Low-Level Reflection on the following data:
    
    Market News Summary:
    {news_summary}
    
    Price Trend:
    {price_trend}
    
    Question: Why did the price move (or not move) in this way given the news? 
    Is there a direct correlation?
    """
    res = model.invoke(prompt)
    return res.content

def high_level_reflection(past_decisions: list):
    """
    Review past decisions. 
    (For this MVP, we analyze the retrieved memories of past actions).
    """
    if not past_decisions:
        return "No past decisions available for reflection."

    past_text = "\n".join(past_decisions)
    
    prompt = f"""
    Perform a High-Level Reflection on these past trading decisions:
    
    {past_text}
    
    Identify any patterns of mistakes or success. 
    For example, did we buy too early? Did we ignore negative news?
    Provide a "Lesson" for the current decision.
    """
    res = model.invoke(prompt)
    return res.content
