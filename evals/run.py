# Run the eval set against the live model:
#   python evals/run.py                  # all of evals/golden.yaml
#   python evals/run.py --threshold 0.5  # with a relevance cutoff
#   python evals/run.py --limit 4        # the first four only
#
# An eval estimates a tendency: it asks the real model real questions and counts how often the
# reply is right. Unlike a test, the score can change from run to run.
import argparse
import re
import sys
import time

import yaml

sys.path.insert(0, "src")   # so we can import the chatbot and the pay tool from src/
import pay_tool
import rag_chatbot


def contains(reply, alternatives):
    # "80 hours|10 days" passes if the reply contains either phrase (case doesn't matter)
    return any(a.lower() in reply.lower() for a in alternatives.split("|"))


def grade(item, reply, chunks, tool):
    """Grade one question: check the reply, the retrieved chunks and the tool call against the
    question's entry in golden.yaml. Returns one entry per check, e.g.
    {"retrieval": True, "says 80 hours|10 days": False}."""
    checks = {}
    # Retrieval: was the expected section (e.g. "4.2") in one of the top 3 chunks?
    # If it fails, the model never saw the answer.
    if "section" in item:
        pattern = rf"(^| ){re.escape(item['section'])} "
        checks["retrieval"] = any(re.search(pattern, c["text"]) for c in chunks)
    # Generation: does the reply contain what a right answer must say?
    for alternatives in item.get("expect", []):
        checks[f"says {alternatives}"] = contains(reply, alternatives)
    # A question the documents don't answer: the bot should say so
    if item.get("decline"):
        checks["declines"] = "I don't have information" in reply
    # A question the asker isn't allowed to ask: the pay tool's fixed refusal
    if item.get("refuse"):
        checks["refuses"] = reply == pay_tool.NOT_ALLOWED
    # A question that shouldn't use the pay tool at all
    if item.get("no_tool"):
        checks["no tool call"] = tool is None
    return checks


def main():
    parser = argparse.ArgumentParser(description="Run the eval set")
    parser.add_argument("--threshold", type=float, default=rag_chatbot.RELEVANCE_THRESHOLD)
    parser.add_argument("--limit", type=int, help="run only the first N questions")
    args = parser.parse_args()
    items = yaml.safe_load(open("evals/golden.yaml"))[:args.limit]

    passed = 0
    for i, item in enumerate(items, 1):
        start = time.time()
        # Questions with "as:" (who's asking) go to the pay tool; the rest go to the RAG chatbot
        if "as" in item:
            reply, tool = pay_tool.answer(item["question"], item["as"])
            chunks = []
        else:
            reply, chunks = rag_chatbot.answer(item["question"], threshold=args.threshold)
            tool = None
        checks = grade(item, reply, chunks, tool)
        ok = all(checks.values())   # a question passes only if every check passes
        passed += ok
        print(f"{i}. {'PASS' if ok else 'FAIL'} ({time.time() - start:.0f} s) {item['question']}"
              + (f"  [as {item['as']}]" if "as" in item else ""))
        # For a failure, show which checks missed and the start of the reply, so you can tell a
        # retrieval failure from a generation failure
        for check, result in checks.items():
            if not result:
                print(f"     missed: {check}")
        if not ok:
            print(f"     reply: {reply[:160]}")
    print(f"\nScore: {passed}/{len(items)}  (threshold {args.threshold})")


if __name__ == "__main__":
    main()
