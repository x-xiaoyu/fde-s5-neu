# Meridian HR assistant with one tool: an employee's pay against their band (made-up data).
#   python src/pay_tool.py --as "Sam Okafor" "Is Marcus Brown paid within range?"
#   python src/pay_tool.py --as "Sam Okafor" --raw "..."     # the tool returns only the numbers
#   python src/pay_tool.py --as "Sam Okafor" --route "..."   # the code decides when to use the tool

import argparse
import csv
import json
import time

import requests

from rag_chatbot import CHAT_MODEL, OLLAMA_CHAT_URL, answer as rag_answer

COMP_PATH = "comp_ranges.csv"
NOT_ALLOWED = "You can only ask about the pay of people you manage. For anything else, please contact HR."
TOOL_PROMPT = "You are an HR assistant for Meridian Analytics Group."
ANSWER_PROMPT = """You are an HR assistant for Meridian Analytics Group.
Answer the user's question in one or two sentences, using ONLY the pay record below.

PAY RECORD:
{record}"""
TOOLS = [{"type": "function", "function": {
    "name": "get_pay_range",
    "description": "Look up an employee's salary and how it compares to their pay band.",
    "parameters": {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "the employee's full name"}},
        "required": ["name"]
    }
}}]


def load_employees(path=COMP_PATH):
    with open(path) as f:
        return {row["name"]: row for row in csv.DictReader(f)}


# ── The tool: code, so a test can check it ────────────────────
def may_see(asker, employee):
    return employee["manager"] == asker


def get_pay_range(employee, raw=False):
    salary, low, high = (int(employee[k]) for k in ("salary", "band_min", "band_max"))
    record = {k: employee[k] for k in ("name", "title", "band")}
    record.update(salary=salary, band_min=low, band_max=high)
    if raw:
        return record
    if salary < low:
        record.update(status="below band", by=low - salary)
    elif salary > high:
        record.update(status="above band", by=salary - high)
    else:
        record.update(status="within band", by=0)
    return record


# ── Who decides to use the tool: the model, or (--route) the code ──
def model_picks(question):
    response = requests.post(OLLAMA_CHAT_URL, json={
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": TOOL_PROMPT},
            {"role": "user", "content": question}
        ],
        "tools": TOOLS,
        "stream": False
    })
    response.raise_for_status()
    calls = response.json()["message"].get("tool_calls") or []
    return calls[0]["function"]["arguments"].get("name", "") if calls else None


def code_picks(question, employees):
    return next((name for name in employees if name.lower() in question.lower()), None)


def chat(system_prompt, question):
    response = requests.post(OLLAMA_CHAT_URL, json={
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "stream": False
    })
    response.raise_for_status()
    return response.json()["message"]["content"]


def answer(question, asker, raw=False, route=False, employees=None):
    """Return (reply, name): name is who the tool was called for, or None."""
    employees = employees or load_employees()
    name = code_picks(question, employees) if route else model_picks(question)
    if name is None:
        return rag_answer(question)[0], None
    employee = employees.get(name)
    if employee is None:
        record = {"error": f"no employee named {name}"}
    elif not may_see(asker, employee):
        return NOT_ALLOWED, name
    else:
        record = get_pay_range(employee, raw=raw)
    return chat(ANSWER_PROMPT.format(record=json.dumps(record)), question), name


# ── Command line ───────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Meridian HR assistant with a pay tool")
    parser.add_argument("question", nargs="+", help="the question to ask")
    parser.add_argument("--as", dest="asker", required=True, help="who is asking (full name)")
    parser.add_argument("--raw", action="store_true", help="the tool returns only the numbers")
    parser.add_argument("--route", action="store_true", help="the code decides when to use the tool")
    args = parser.parse_args()
    question = " ".join(args.question)

    start = time.time()
    try:
        reply, name = answer(question, args.asker, raw=args.raw, route=args.route)
    except requests.exceptions.ConnectionError:
        print("Cannot connect to Ollama. Is it running? Try: make serve")
        return
    print(reply)
    tool = f'get_pay_range("{name}")' if name is not None else "no tool call"
    print(f"\n[{tool}, {CHAT_MODEL}, {time.time() - start:.0f} s]")


if __name__ == "__main__":
    main()
