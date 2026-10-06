from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.api.llm_service import generate_sql_from_prompt
from src.api.guardrails import validate_sql_query, execute_safe_query

app = FastAPI(title="OpenStore AI Analytics API")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    prompt: str


@app.post("/api/v1/ai-query")
async def ai_query(request: QueryRequest):
    try:
        raw_sql = generate_sql_from_prompt(request.prompt)
        validated_sql = validate_sql_query(raw_sql)
        results, columns = execute_safe_query(validated_sql)

        return {
            "status": "success",
            "prompt": request.prompt,
            "validated_sql": validated_sql,
            "rows_returned": len(results),
            "data": [dict(zip(columns, row)) for row in results],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/analytics/monthly-revenue")
async def get_monthly_revenue():
    try:
        sql = """
            SELECT 
                year_month,
                total_revenue
            FROM analytics.monthly_revenue_summary
            ORDER BY year_month ASC
            LIMIT 100;
        """
        results, columns = execute_safe_query(sql)
        return {
            "status": "success",
            "data": [dict(zip(columns, row)) for row in results],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
