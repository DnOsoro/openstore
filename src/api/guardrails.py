import os
import re
import psycopg2
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/openstore")

FORBIDDEN_KEYWORDS = [
    r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b",
    r"\bTRUNCATE\b", r"\bALTER\b", r"\bCREATE\b", r"\bGRANT\b",
    r"\bREVOKE\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bPG_\w+"
]

def validate_sql_query(sql_query: str) -> str:
    clean_sql = sql_query.strip()

    # 1. Reject multi-statement queries
    if ";" in clean_sql[:-1]:
        raise HTTPException(
            status_code=400,
            detail="Security Violation: Multiple SQL statements in a single query are not allowed."
        )

    # 2. Force Read-Only (SELECT only)
    if not clean_sql.lower().startswith("select"):
        raise HTTPException(
            status_code=400,
            detail="Security Violation: Only SELECT queries are permitted."
        )

    # 3. Check forbidden DDL/DML keywords
    for pattern in FORBIDDEN_KEYWORDS:
        if re.search(pattern, clean_sql, re.IGNORECASE):
            raise HTTPException(
                status_code=400,
                detail=f"Security Violation: Query contains unauthorized keyword/pattern matching '{pattern}'."
            )

    # 4. Enforce mandatory safety LIMIT clause
    if not re.search(r"\bLIMIT\s+\d+", clean_sql, re.IGNORECASE):
        clean_sql = f"{clean_sql.rstrip(';')} LIMIT 100;"

    return clean_sql

def execute_safe_query(sql_query: str):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results, columns
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Database Query Error: {str(e)}")
