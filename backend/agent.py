import os

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from openai import OpenAI

from backend.openai_usage import log_openai_usage
from backend.tools import rag_knowledge_tool, sql_query_tool


TOPIC_REJECTION = (
    "🚕 I'm your NYC Taxi Data Assistant! I can only answer questions\n"
    "about taxi trips, fares, distances, payments, and ride patterns.\n"
    "Try asking: 'What is the average fare?' or 'Which payment type is most popular?'"
)

LOW_CONFIDENCE_REPLY = (
    "I found some information but I'm not confident enough to share it.\n"
    "Please try asking a more specific question about the taxi data."
)


def get_agent():
    api_key = log_openai_usage("agent", "langchain_openai.ChatOpenAI", "gpt-4o")
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=api_key,
    )
    tools = [sql_query_tool, rag_knowledge_tool]
    return create_react_agent(llm, tools)


def _chat_completion(system_prompt: str, user_content: str) -> str:
    api_key = log_openai_usage("agent-guardrail", "chat.completions.create", "gpt-4o")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content.strip()


def is_taxi_related(question: str) -> bool:
    decision = _chat_completion(
        (
            "You are a strict topic classifier. Reply ONLY with YES or NO.\n"
            "Is this question related to any of these topics:\n"
            "NYC taxis, cab rides, trip fares, taxi drivers, trip distance,\n"
            "payment types, passenger count, taxi data analysis, transportation,\n"
            "pickup/dropoff locations, taxi surcharges, or taxi vendors?\n"
            f"Question: {question}"
        ),
        question,
    )
    return decision.upper().startswith("YES")


def has_unverified_claims(answer: str) -> bool:
    decision = _chat_completion(
        (
            "Does this answer contain any made-up numbers or unverified claims\n"
            "not supported by a SQL result or provided knowledge base? Reply YES or NO only."
        ),
        answer,
    )
    return decision.upper().startswith("YES")


def build_trace(messages) -> list[str]:
    trace = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                trace.append(f"🔧 Tool: {tool_call['name']}")
        elif hasattr(msg, "name") and msg.name:
            trace.append(f"📊 Result from {msg.name}")
    return trace


def run_agent(question: str) -> dict:
    print(f"[agent] received question={question!r}")
    if not is_taxi_related(question):
        print("[agent] topic guardrail rejected question")
        return {
            "answer": TOPIC_REJECTION,
            "trace": ["🛡️ Topic guardrail blocked a non-taxi question."],
        }

    agent = get_agent()
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict NYC Taxi data analyst. You ONLY answer questions\n"
                        "using the sql_query_tool for data questions and rag_knowledge_tool\n"
                        "for conceptual taxi questions. NEVER make up numbers or facts.\n"
                        "If you cannot find the answer using tools, say:\n"
                        "'I could not find that in the taxi dataset. Try rephrasing your question.'\n"
                        "Always cite whether your answer came from SQL data or domain knowledge.\n"
                        "Keep answers under 3 sentences, conversational, suitable for text-to-speech."
                    ),
                },
                {"role": "user", "content": question},
            ]
        }
    )

    messages = result["messages"]
    final_answer = messages[-1].content
    trace = build_trace(messages)
    print(f"[agent] trace={trace!r}")
    print(f"[agent] answer={final_answer!r}")

    if has_unverified_claims(final_answer):
        print("[agent] confidence guardrail replaced answer")
        return {
            "answer": LOW_CONFIDENCE_REPLY,
            "trace": trace + ["🛡️ Confidence check replaced a potentially unverified answer."],
        }

    return {
        "answer": final_answer,
        "trace": trace,
    }
