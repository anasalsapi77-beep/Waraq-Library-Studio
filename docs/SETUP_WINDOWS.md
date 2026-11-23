# Windows quick start

1. Extract `Waraq_Library_Studio.zip` with **Extract All**.
2. Open the extracted project folder. You should see `main.py`, `run.bat`, `waraq` and `static` in the same window.
3. Double-click `run.bat`.
4. Open <http://127.0.0.1:8000> in your browser.
5. To stop the server, return to its terminal and press `Ctrl + C`.

## Open PowerShell in the correct folder

In File Explorer, open the folder that contains `main.py`, click the address bar, type `powershell`, then press Enter. Confirm the prompt path is the project folder before running commands.

## Repair the sample login accounts

```powershell
python main.py --reset-demo-accounts
```

This command preserves all items, members and lending records. After it completes, start the server again:

```powershell
python main.py
```

## Run tests

```powershell
python -m unittest discover -s tests -v
```
