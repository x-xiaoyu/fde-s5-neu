# AGENTS.md

Rules for AI coding assistants (Copilot, Claude Code, Cursor and others) working in this repo.

## What this is

A RAG assistant for Meridian Analytics Group's HR, IT, expense and data-governance policies
(`meridian_docs/`). Python, Ollama (`llama3.2:3b` for answers,
`nomic-embed-text` for embeddings), ChromaDB. It runs locally or in a Codespace; nothing calls
an external AI API.

- `src/build_index.py` chunks and embeds the policies into `./chroma_db`
- `src/explore_index.py "question"` shows the top chunks and their distances
- `src/rag_chatbot.py` answers questions; `--plain` answers without retrieval
- `tests/` holds the tests; `evals/` holds the eval set (`golden.yaml`) and its runner

## Rules

- Never send policy text, or anything from `meridian_docs/`, to an external API.
- Every code change comes with a test, or a note in the PR saying why it can't have one.
- Keep changes small, and explain each one so the person reviewing can check it.

## Tests vs. evals

Keep them separate.

**Tests verify obligations:** behavior the code must always get right.
- Deterministic, pass/fail, expected to pass 100% of the time.
- No model calls. Stub them if the code under test makes one.
- Examples: the bot declines without calling the model when no chunk is relevant, chunking
  splits at numbered sections, section numbers are stored in metadata,
  the relevance filter drops distant chunks, the pay-range tool refuses a manager outside the
  employee's team.
- Location: `tests/`. Run on every change: `pytest tests/`.
- A failing test is a bug. Fix the code; never loosen or delete the test to make it pass.

**Evals estimate tendencies:** how well model-driven behavior performs across a set of questions.
- Use live model calls; results are scores or rates.
- Grading may use exact match (e.g. the right section number), heuristics or an LLM judge.
- Examples: answer is right and cites its section; declines questions the documents don't
  answer; refuses on access grounds; retrieval puts the right chunk in the top 3.
- Location: `evals/`. Run with `python evals/run.py`. Not part of `pytest tests/`: they're slow
  on a CPU (over a minute an answer in a Codespace). Run only when asked.
- A score drop is something to investigate and report, not a test to "fix". Never edit
  `golden.yaml`, thresholds or graders to raise a score unless explicitly asked.

**When adding a check, decide which it is.** If it must hold every time and can be checked
without a model, write a test. If it depends on model output, write an eval. If unclear, ask.

**Validation** (user acceptance, feedback, production monitoring) is separate from both and
outside this repo. That's Session 6–7.

## Pull requests

Use the template. Before asking for review, the author confirms:
- I can explain every change the assistant made.
- `pytest tests/` passes, and the eval score is recorded in the PR.
- A peer could rerun it from this PR.
