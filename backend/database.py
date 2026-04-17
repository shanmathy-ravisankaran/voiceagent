import duckdb
import os

DB_PATH = "voiceagent.duckdb"
CSV_PATH = "data/yellow_tripdata_2015-01.csv"

def get_connection():
    con = duckdb.connect(DB_PATH)
    return con

def init_db():
    con = get_connection()
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS trips AS
        SELECT * FROM read_csv_auto('{CSV_PATH}', ignore_errors=True)
    """)
    print("✅ DuckDB loaded successfully!")
    con.close()

def run_query(sql: str) -> list[dict]:
    con = get_connection()
    try:
        result = con.execute(sql).fetchdf()
        return result.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        con.close()


def get_trip_stats() -> dict:
    con = get_connection()
    try:
        row = con.execute(
            """
            SELECT
                COUNT(*) AS total_trips,
                ROUND(AVG(fare_amount), 2) AS avg_fare,
                ROUND(AVG(trip_distance), 2) AS avg_distance
            FROM trips
            """
        ).fetchone()
        return {
            "total_trips": int(row[0] or 0),
            "avg_fare": float(row[1] or 0),
            "avg_distance": float(row[2] or 0),
        }
    finally:
        con.close()


def get_dashboard_snapshot() -> dict:
    con = get_connection()
    try:
        payment_rows = con.execute(
            """
            SELECT
                CASE payment_type
                    WHEN 1 THEN 'Credit card'
                    WHEN 2 THEN 'Cash'
                    WHEN 3 THEN 'No charge'
                    WHEN 4 THEN 'Dispute'
                    WHEN 5 THEN 'Unknown'
                    WHEN 6 THEN 'Voided trip'
                    ELSE 'Other'
                END AS payment_label,
                COUNT(*) AS trips
            FROM trips
            GROUP BY 1
            ORDER BY trips DESC
            LIMIT 6
            """
        ).fetchall()

        vendor_rows = con.execute(
            """
            SELECT
                CONCAT('Vendor ', VendorID) AS vendor_label,
                COUNT(*) AS trips
            FROM trips
            GROUP BY 1
            ORDER BY trips DESC
            """
        ).fetchall()

        hourly_rows = con.execute(
            """
            SELECT
                EXTRACT(hour FROM tpep_pickup_datetime) AS pickup_hour,
                COUNT(*) AS trips
            FROM trips
            GROUP BY 1
            ORDER BY 1
            """
        ).fetchall()

        card_tip_row = con.execute(
            """
            SELECT ROUND(AVG(tip_amount), 2)
            FROM trips
            WHERE payment_type = 1
            """
        ).fetchone()

        airport_row = con.execute(
            """
            SELECT COUNT(*)
            FROM trips
            WHERE RatecodeID IN (2, 3)
            """
        ).fetchone()

        return {
            "payment_mix": [
                {"label": str(label), "value": int(value or 0)}
                for label, value in payment_rows
            ],
            "vendor_mix": [
                {"label": str(label), "value": int(value or 0)}
                for label, value in vendor_rows
            ],
            "hourly_demand": [
                {"hour": int(hour or 0), "trips": int(value or 0)}
                for hour, value in hourly_rows
            ],
            "insights": {
                "avg_card_tip": float(card_tip_row[0] or 0),
                "airport_trip_count": int(airport_row[0] or 0),
            },
        }
    finally:
        con.close()
