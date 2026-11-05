# Session 5 steps

The commands for each part of today's session, in order. Run them from this folder, in your
Codespace or (after `conda activate fde-s5`) on your own machine. Start with `make serve` if the
model server isn't running.

In a Codespace, the first answer can take about a minute; later ones are faster. Work with your
partner on whichever machine is faster.

## Under the hood

### 1. Build the index

> The bot can't read the whole handbook for every question, so we cut it into pieces it can search.

```
python src/build_index.py
```

[src/build_index.py](src/build_index.py) cuts the four policy files in `meridian_docs/` into
400-word chunks, turns each into an embedding (a list of numbers that captures its meaning) and
stores them in `./chroma_db`. Look for "13 chunks stored".

### 2. Ask it

> Ask it something the handbook answers, and something it doesn't.

```
python src/rag_chatbot.py "How much PTO can I carry over?"
python src/rag_chatbot.py "Who approved the new parking policy?"
```

The last line shows where the time went. Look for: Is the PTO answer right? What does it say
about parking, which the documents don't cover? Compare with your partner: same words?

### 3. Look inside the index

> It retrieved something even for a question the handbook can't answer. How close is close
> enough?

```
python src/explore_index.py "How much PTO can I carry over?"
python src/explore_index.py "Who approved the new parking policy?"
python src/explore_index.py "What is the capital of France?"
```

[src/explore_index.py](src/explore_index.py) prints the three closest chunks and their **cosine
distance**: 0 is the same meaning, 1 is unrelated. Retrieval always returns three chunks, however
far away they are.

Choose a cutoff from those distances: any chunk farther than it gets dropped. Answer the poll
with yours.

### 4. Try your cutoff

> Drop every chunk farther than your cutoff. What does the bot do when nothing is left?

Replace `CUTOFF` with your number:

```
python src/rag_chatbot.py --show --threshold CUTOFF "Who approved the new parking policy?"
python src/rag_chatbot.py --show --threshold CUTOFF "How much PTO can I carry over?"
```

`--show` marks each chunk kept or dropped. Look for: when every chunk is dropped, what does the
last line say?

Now try a tight cutoff:

```
python src/rag_chatbot.py --show --threshold 0.41 "How far in advance do I need to request vacation?"
```

What goes wrong when the cutoff is too tight?

### 5. Same question, two systems

> Same question, no handbook.

```
python src/rag_chatbot.py --plain "How much PTO can I carry over?"
```

`--plain` skips retrieval: the model answers from what it learned in training.

### 6. Add one tool

> Give the bot a tool that looks up pay, and watch who makes each decision: the model or the code.

```
python src/pay_tool.py --as "Sam Okafor" --raw "Is Marcus Brown paid within range?"
python src/pay_tool.py --as "Sam Okafor" "Is Marcus Brown paid within range?"
python src/pay_tool.py --as "Jordan Lee" "Is Marcus Brown paid within range?"
python src/pay_tool.py --as "Sam Okafor" "How much PTO can I carry over?"
python src/pay_tool.py --as "Sam Okafor" --route "How much PTO can I carry over?"
```

[src/pay_tool.py](src/pay_tool.py) gives the model one tool, `get_pay_range`, over
[comp_ranges.csv](comp_ranges.csv) (made-up data). `--as` says who's asking. `--raw`: the tool
returns only the numbers. `--route`: the code, not the model, decides when to use the tool. The
last line shows the tool call the model made.

## Proving it works

### 7. Run the decline test

> When every chunk is past the cutoff, the code skips the model and returns one fixed sentence,
> word for word the same every time. Something that never varies can be checked by a test: feed
> it a question with no close chunks and confirm that exact sentence comes back.

```
pytest
```

`pytest` runs every test in `tests/`. Look at the last line: how long did the four tests take,
compared with the answers you got today? Then answer the poll: why so fast?

Afterwards, read [tests/test_decline.py](tests/test_decline.py). Then watch on the projector: we
break the code on purpose, by deleting the two decline lines in `answer()` in
[src/rag_chatbot.py](src/rag_chatbot.py), and run `pytest` again. Does the test notice?

### 8. Chunk by section

> What if each chunk were one section of the handbook?

```
python src/build_index.py --by-section
python src/explore_index.py "How much PTO can I carry over?"
python src/build_index.py
```

`--by-section` cuts one chunk per numbered section. The last command puts the 400-word index back.

### 9. Write and run an eval set

> A test says pass or fail; an eval gives a score.

[evals/golden.yaml](evals/golden.yaml) holds questions and what a right answer contains. Add one
question of your own **at the top of the list**, just under the comment lines, copying the shape
of the first entry. Then run it at your cutoff (replace `CUTOFF`):

```
python evals/run.py --threshold CUTOFF
```

In a Codespace, `--limit 5` runs only the first five, which includes yours because it's at the
top. For each failure, read the retrieved chunks:
if the answer isn't in them, retrieval failed; if it is, the model did.

Production teams use frameworks for this, like DeepEval, Ragas or promptfoo: our `run.py` plus an LLM judge and a dashboard.

### 10. The pull request

> Before anyone merges your change, show your evidence: what changed, what passed, and what could
> still go wrong.

Nothing to run: we'll talk it through. Today's change would be your cutoff as the default
(`RELEVANCE_THRESHOLD` in `src/rag_chatbot.py`), with the test from step 7. Its pull request,
from [.github/pull_request_template.md](.github/pull_request_template.md), records what changed and
why, the test results, the eval score before (no cutoff) and after, known risks, and what's needed
before promotion. Its checklist is the point: can you explain every change the assistant made?

The coding assistant's rules live in the repo too, in [AGENTS.md](AGENTS.md): the stack, how to run
the tests, and rules such as "every change needs a test" and "never loosen a test to make it pass".
