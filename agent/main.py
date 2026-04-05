from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.llm import ask_llm
import agent.tools.airflow as airflow_tools
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

TOOLS = {
    "get_dags": {"fn": airflow_tools.get_dags, "params": [], "desc": "List all DAGs with their status"},
    "get_dag_details": {"fn": airflow_tools.get_dag_details, "params": ["dag_id"], "desc": "Get details of a specific DAG"},
    "get_dag_runs": {"fn": airflow_tools.get_dag_runs, "params": ["dag_id"], "desc": "Get recent runs of a specific DAG. dag_id must be exact DAG name, never use wildcard *"},
    "trigger_dag": {"fn": airflow_tools.trigger_dag, "params": ["dag_id"], "desc": "Trigger/run a DAG"},
    "pause_dag": {"fn": airflow_tools.pause_dag, "params": ["dag_id"], "desc": "Pause a DAG"},
    "unpause_dag": {"fn": airflow_tools.unpause_dag, "params": ["dag_id"], "desc": "Unpause/activate a DAG"},
    "get_failed_tasks": {"fn": airflow_tools.get_failed_tasks, "params": ["dag_id"], "desc": "Get failed tasks of a DAG"},
    "get_task_log": {"fn": airflow_tools.get_task_log, "params": ["dag_id"], "desc": "Get failure log of a DAG for debugging"},
    "get_system_health": {"fn": airflow_tools.get_system_health, "params": [], "desc": "Get overall system health summary of all DAGs"},
    "get_dag_stats": {"fn": airflow_tools.get_dag_stats, "params": [], "desc": "Get run count, average duration and longest run for ALL DAGs. Use this for questions like: most run dag, longest duration, statistics"},
    "get_pools": {"fn": airflow_tools.get_pools, "params": [], "desc": "Get Airflow pools"},
    "get_variables": {"fn": airflow_tools.get_variables, "params": [], "desc": "Get Airflow variables"},
    "clear_task": {"fn": airflow_tools.clear_task, "params": ["dag_id", "task_id", "run_id"], "desc": "Clear/retry a failed task"},
}

TOOL_DESCRIPTIONS = "\n".join([f"- {name}({', '.join(t['params'])}): {t['desc']}" for name, t in TOOLS.items()])

SYSTEM_PROMPT = f"""You are an expert Apache Airflow AI Assistant. You help users manage, monitor, debug and operate their Airflow environment.

You understand both English and Turkish. Always respond in the same language the user uses.

You have access to these tools:
{TOOL_DESCRIPTIONS}

## IMPORTANT RULES:
- NEVER use wildcard (*) as dag_id. Always use exact DAG name.
- For statistics questions (most run, longest duration) → always use get_dag_stats
- For system overview → use get_system_health
- For specific DAG runs → use get_dag_runs with exact dag_id

## How to use tools:
When you need data to answer, respond with ONLY this JSON (no markdown, no extra text):
{{"tool": "tool_name", "params": {{"param_name": "value"}}}}

## After getting tool results:
Analyze the data and give a helpful, natural language response. Be like an expert Airflow engineer.

## Example mappings:
- "en çok çalışan dag hangisi?" → {{"tool": "get_dag_stats", "params": {{}}}}
- "hangi dag en uzun sürdü?" → {{"tool": "get_dag_stats", "params": {{}}}}
- "sistemimin durumu nedir?" → {{"tool": "get_system_health", "params": {{}}}}
- "payment_auth_pipeline neden fail oldu?" → {{"tool": "get_task_log", "params": {{"dag_id": "payment_auth_pipeline"}}}}
- "payment_auth_pipeline'ı çalıştır" → {{"tool": "trigger_dag", "params": {{"dag_id": "payment_auth_pipeline"}}}}
- "payment_auth_pipeline'ı durdur" → {{"tool": "pause_dag", "params": {{"dag_id": "payment_auth_pipeline"}}}}
- "tüm dag'ları listele" → {{"tool": "get_dags", "params": {{}}}}
- "pool'larımı göster" → {{"tool": "get_pools", "params": {{}}}}

General Airflow questions (xcom, sensor, cron, etc.) → answer from your knowledge without using tools."""

def extract_json(text: str) -> dict | None:
    text = text.strip().replace("**", "")
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    if "{" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        try:
            return json.loads(text[start:end])
        except:
            return None
    return None

def call_tool(tool_name: str, params: dict) -> str:
    if tool_name not in TOOLS:
        return f"Unknown tool: {tool_name}"
    tool = TOOLS[tool_name]
    try:
        result = tool["fn"](**params)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Tool error: {e}"

@app.post("/chat")
async def chat(request: ChatRequest):
    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.message}
    ]

    llm_response = ask_llm(conversation)
    print(f"DEBUG llm_response: {llm_response[:200]}")

    tool_call = extract_json(llm_response)

    if tool_call and "tool" in tool_call:
        tool_name = tool_call.get("tool")
        params = tool_call.get("params", {})
        print(f"DEBUG calling tool: {tool_name} with {params}")

        tool_result = call_tool(tool_name, params)
        print(f"DEBUG tool_result: {tool_result[:200]}")

        conversation.append({"role": "assistant", "content": llm_response})
        conversation.append({
            "role": "user",
            "content": f"Tool '{tool_name}' returned:\n{tool_result}\n\nNow give a helpful natural language response. Respond in the same language as the user."
        })

        final_response = ask_llm(conversation)
    else:
        final_response = llm_response

    return {"response": final_response}

@app.get("/health")
async def health():
    return {"status": "ok"}