from backend.database import run_query
from backend.openai_usage import log_openai_usage
from backend.rag import query_rag
from langchain.tools import tool

@tool
def sql_query_tool(question: str) -> str:
    """
    Use this tool to answer questions about NYC taxi trip data using SQL.
    Generates and runs a DuckDB SQL query on the trips table.
    Columns: VendorID, tpep_pickup_datetime, tpep_dropoff_datetime,
    passenger_count, trip_distance, pickup_longitude, pickup_latitude,
    RatecodeID, store_and_fwd_flag, dropoff_longitude, dropoff_latitude,
    payment_type, fare_amount, extra, mta_tax, tip_amount, tolls_amount,
    improvement_surcharge, total_amount
    """
    # Generate SQL from question
    from openai import OpenAI
    api_key = log_openai_usage("sql-tool", "chat.completions.create", "gpt-4o")
    client = OpenAI(api_key=api_key)
    print(f"[sql-tool] question={question!r}")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a DuckDB SQL expert. 
            Generate ONLY a valid SQL query for the 'trips' table with these columns:
            VendorID, tpep_pickup_datetime, tpep_dropoff_datetime, passenger_count, 
            trip_distance, pickup_longitude, pickup_latitude, RatecodeID, 
            store_and_fwd_flag, dropoff_longitude, dropoff_latitude, payment_type, 
            fare_amount, extra, mta_tax, tip_amount, tolls_amount, 
            improvement_surcharge, total_amount.
            Return ONLY the SQL query, nothing else. Always add LIMIT 100."""},
            {"role": "user", "content": question}
        ]
    )
    
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    print(f"[sql-tool] sql={sql!r}")
    
    results = run_query(sql)
    
    if results and "error" not in results[0]:
        return f"SQL: {sql}\n\nResults: {str(results[:10])}"
    else:
        return f"Query error: {results}"

@tool
def rag_knowledge_tool(question: str) -> str:
    """
    Use this tool to answer conceptual questions about NYC taxi data,
    payment types, vendor IDs, rate codes, surcharges, and general taxi knowledge.
    """
    context = query_rag(question)
    return f"Relevant knowledge:\n{context}"
