cd C:\scripts\chat
& .\venv\Scripts\activate.ps1

Start-Process python -ArgumentList "play_server.py"
Start-Process "npm.cmd" -ArgumentList "start"
