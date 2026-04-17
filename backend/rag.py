import os

import chromadb
from chromadb.utils import embedding_functions

from backend.openai_usage import log_openai_usage


CHROMA_PATH = "chroma_store"

TAXI_KNOWLEDGE = [
    "VendorID identifies the taxi technology provider. 1 = Creative Mobile Technologies (CMT), 2 = VeriFone Inc.",
    "tpep_pickup_datetime is the date and time when the taxi meter was started for the trip.",
    "tpep_dropoff_datetime is the date and time when the taxi meter was turned off at the destination.",
    "passenger_count is the number of passengers in the vehicle as entered by the driver.",
    "trip_distance is the elapsed trip distance in miles as recorded by the taximeter.",
    "pickup_longitude and pickup_latitude are the GPS coordinates where the trip started.",
    "dropoff_longitude and dropoff_latitude are the GPS coordinates where the trip ended.",
    "RatecodeID is the final rate code applied at the end of the trip.",
    "store_and_fwd_flag indicates if the trip record was held in vehicle memory before sending. Y = stored, N = live.",
    "payment_type: 1 = Credit card, 2 = Cash, 3 = No charge, 4 = Dispute, 5 = Unknown, 6 = Voided trip.",
    "fare_amount is the time-and-distance fare calculated by the taximeter.",
    "extra includes miscellaneous extras and surcharges, currently $0.50 and $1 rush hour and overnight charges.",
    "mta_tax is a $0.50 MTA tax automatically triggered based on the metered rate in use.",
    "tip_amount is automatically populated for credit card tips. Cash tips are not captured.",
    "tolls_amount is the total amount of all tolls paid during the trip.",
    "improvement_surcharge is a $0.30 surcharge assessed on hailed trips at flag drop.",
    "total_amount is the total charged to passengers, not including cash tips.",
    "RatecodeID 1 = Standard city rate. RatecodeID 2 = JFK Airport flat rate. RatecodeID 3 = Newark Airport.",
    "RatecodeID 4 = Nassau or Westchester county. RatecodeID 5 = Negotiated fare. RatecodeID 6 = Group ride.",
    "JFK Airport trips from Manhattan have a flat fare of $52 plus tolls and surcharges.",
    "NYC Yellow Taxis operate in all five boroughs: Manhattan, Brooklyn, Queens, The Bronx, and Staten Island.",
    "Yellow taxis are the only taxis allowed to pick up street-hail passengers in Manhattan and at NYC airports.",
    "Peak taxi demand hours in NYC are 7-9 AM and 5-8 PM on weekdays due to commuter traffic.",
    "The NYC Taxi and Limousine Commission (TLC) regulates all yellow taxi operations.",
    "NYC taxis are metered - fare starts at $3.00 flag drop, then $0.50 per 1/5 mile or per 60 seconds in slow traffic.",
    "Tipping 15-20% is standard for NYC taxi rides when paying by credit card.",
    "The dataset covers yellow taxi trips in 2015 and 2016 recorded by the NYC TLC.",
    "Trips to/from LaGuardia Airport use standard metered rates with no flat fare.",
    "Most NYC taxi trips occur in Manhattan, especially Midtown, Downtown, and the Upper East Side.",
    "Late night trips (10 PM to 6 AM) include a $0.50 overnight surcharge.",
    "Rush hour surcharge of $1.00 applies on weekdays from 4:00 PM to 8:00 PM.",
]


def init_rag():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    api_key = log_openai_usage("rag-init", "OpenAIEmbeddingFunction", "text-embedding-3-small")
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )
    try:
        client.delete_collection("taxi_knowledge")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name="taxi_knowledge",
        embedding_function=ef,
    )
    collection.add(
        documents=TAXI_KNOWLEDGE,
        ids=[f"doc_{i}" for i in range(len(TAXI_KNOWLEDGE))],
    )
    print("✅ ChromaDB RAG loaded successfully!")
    return collection


def query_rag(question: str, n_results: int = 3) -> str:
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    api_key = log_openai_usage("rag-query", "OpenAIEmbeddingFunction", "text-embedding-3-small")
    ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small",
    )
    collection = client.get_or_create_collection(
        name="taxi_knowledge",
        embedding_function=ef,
    )
    results = collection.query(query_texts=[question], n_results=n_results)
    docs = results["documents"][0]
    return "\n".join(docs)
