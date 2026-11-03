# Setup: your own Mac or Linux machine

About 15 minutes, most of it downloading (about 2.5 GB). Answers are much faster than in a
Codespace. On Windows, use a [Codespace](SETUP-codespace.md) instead.

You need [miniforge](https://github.com/ds5110/git-intro/blob/main/conda.md) (conda from
conda-forge) and git. Everything installs into one conda environment, `fde-s5`; nothing goes in
/Applications or /usr/local/bin on a Mac.

1. **Get the repo**
   ```
   git clone https://github.com/pbogden/fde-s5.git
   cd fde-s5
   ```
2. **Install** (once)
   ```
   make install
   conda activate fde-s5
   ```
   * Creates the `fde-s5` conda environment, installs Ollama inside it (on a Mac, the signed app
     from ollama.com; on Linux, Ollama's install script) and downloads the two models (into
     `~/.ollama`).
   * **Check:** the prompt shows `(fde-s5)`.
3. **Check that it works**
   ```
   make check
   ```
   * **Check:** a one-sentence hello from the model, then **"Setup works."**

**In class:** open a terminal in `fde-s5`, then `conda activate fde-s5` and `make serve` (it starts
the model server if it isn't running).

**To remove it all later:** `conda env remove -n fde-s5`, and delete `~/.ollama` for the models.

**If something fails:** note the step and the last few lines of the terminal, and bring them to
class.
