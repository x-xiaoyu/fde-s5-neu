# FDE Session 5: Build/Test/Validate

Setup for Session 5 (Thu 5 Nov 2026). Before class, set up **one** of these, and finish with
`make check`:

- **A GitHub Codespace** (works anywhere, including Windows): [SETUP-codespace.md](SETUP-codespace.md)
- **Your own Mac or Linux machine** (faster): [SETUP-mac.md](SETUP-mac.md)

You're done when `make check` ends with **"Setup works."**

The code for the session arrives in class: you'll run `git pull` in this repo. Until then, don't
change any files here, so the pull goes through cleanly.

Everything runs on your machine or your Codespace: a small open model (`llama3.2:3b`) and an
embedding model (`nomic-embed-text`), served by [Ollama](https://ollama.com). Nothing goes to an
outside AI service.
