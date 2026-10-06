import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

engine = create_engine(DATABASE_URL)

def create_analytics_views():
    print("Creating Analytical Views in PostgreSQL...")
    
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics;"))
        
        # 1. Monthly Revenue & Order Metrics
        print("Creating analytics.monthly_revenue_summary...")
        conn.execute(text("DROP VIEW IF EXISTS analytics.monthly_revenue_summary CASCADE;"))
        conn.execute(text("""
            CREATE VIEW analytics.monthly_revenue_summary AS
            SELECT 
                TO_CHAR(order_purchase_at, 'YYYY-MM') AS year_month,
                COUNT(order_id) AS total_orders,
                SUM(grand_total) AS total_revenue,
                SUM(total_order_value) AS total_product_sales,
                SUM(total_freight_value) AS total_freight_fees,
                ROUND(AVG(grand_total), 2) AS avg_order_value
            FROM core.fct_orders
            WHERE order_status = 'delivered'
            GROUP BY TO_CHAR(order_purchase_at, 'YYYY-MM')
            ORDER BY year_month ASC;
        """))

        # 2. Revenue & Order Volume by Customer Location
        print("Creating analytics.revenue_by_location...")
        conn.execute(text("DROP VIEW IF EXISTS analytics.revenue_by_location CASCADE;"))
        conn.execute(text("""
            CREATE VIEW analytics.revenue_by_location AS
            SELECT 
                c.customer_state,
                c.customer_city,
                COUNT(o.order_id) AS total_orders,
                SUM(o.grand_total) AS total_revenue
            FROM core.fct_orders o
            JOIN core.dim_customers c ON o.customer_id = c.customer_id
            WHERE o.order_status = 'delivered'
            GROUP BY c.customer_state, c.customer_city
            ORDER BY total_revenue DESC;
        """))

        # 3. Delivery SLA Performance
        print("Creating analytics.delivery_performance...")
        conn.execute(text("DROP VIEW IF EXISTS analytics.delivery_performance CASCADE;"))
        conn.execute(text("""
            CREATE VIEW analytics.delivery_performance AS
            SELECT 
                order_id,
                order_purchase_at,
                order_delivered_at,
                order_estimated_delivery_at,
                EXTRACT(DAY FROM (order_delivered_at - order_purchase_at)) AS delivery_days,
                CASE 
                    WHEN order_delivered_at <= order_estimated_delivery_at THEN 'On Time'
                    ELSE 'Delayed'
                END AS delivery_status
            FROM core.fct_orders
            WHERE order_status = 'delivered' AND order_delivered_at IS NOT NULL;
        """))

    print("\n✓ Analytics views created successfully in 'analytics' schema!")

if __name__ == "__main__":
    create_analytics_views()
