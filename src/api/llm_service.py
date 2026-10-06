import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_NAME = os.getenv("LLM_MODEL", "google/gemini-2.5-flash")

SYSTEM_PROMPT = """You are an expert SQL Assistant for PostgreSQL.
Your job is to translate user natural language questions into valid PostgreSQL SELECT queries.

Database Schemas & Tables:
- analytics.monthly_revenue_summary (year_month, total_orders, total_revenue, total_product_sales, total_freight_fees, avg_order_value)
- analytics.revenue_by_location (customer_state, customer_city, total_orders, total_revenue)
- analytics.delivery_performance (order_id, order_purchase_at, order_delivered_at, order_estimated_delivery_at, delivery_days, delivery_status)
- core.fct_orders (order_id, customer_id, order_status, grand_total, total_order_value, total_freight_value)
- core.dim_customers (customer_id, customer_unique_id, customer_city, customer_state)

Rules:
1. Return ONLY the raw SQL query. Do NOT use markdown code blocks or extra text.
2. Read-only SELECT queries only.
"""

def generate_sql_from_prompt(user_prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set in environment variables.")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "OpenStore Analytics"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 200
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter API call failed ({response.status_code}): {response.text}")

    sql_query = response.json()["choices"][0]["message"]["content"].strip()
    
    if sql_query.startswith("```"):
        lines = sql_query.split("\n")
        sql_query = "\n".join([line for line in lines if not line.startswith("```")]).strip()
        
    return sql_query
