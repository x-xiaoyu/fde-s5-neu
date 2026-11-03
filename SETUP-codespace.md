# Setup: GitHub Codespace

About 10 minutes, most of it waiting. You need a free GitHub account.

1. **Make sure you can't be charged** (once per GitHub account)
   * github.com → your picture → Settings → Billing and licensing → Budgets and alerts.
   * **Check:** the Codespaces budget is $0. Free accounts include enough Codespace hours for
     this course.
2. **Create your Codespace**
   * On this repo's GitHub page: the green **Code** button → **Codespaces** → **Create codespace
     on main**.
   * It opens VS Code in your browser and installs Ollama and the Python packages. Wait until the
     terminal at the bottom is ready for typing (about 4 minutes).
   * **Check:** in the terminal, `nproc` prints `4`.
3. **Download the two models** (about 2.3 GB, under a minute)
   ```
   make models
   ```
   * **Check:** it ends without an error.
4. **Check that it works**
   ```
   make check
   ```
   * **Check:** a one-sentence hello from the model, then **"Setup works."** The first answer can
     take 10–30 seconds.
5. **Stop the Codespace** when you're done, so it doesn't use your free hours
   * github.com/codespaces → the **…** next to your Codespace → **Stop codespace**. Don't delete
     it: you'll reopen it in class.

**In class:** reopen it from github.com/codespaces, then run `make serve` (the model server
stops when the Codespace does).

**If something fails:** note the step and the last few lines of the terminal, and bring them to
class.
