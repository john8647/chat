@echo off
cd /d C:\scripts\chat

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting Python server...
start "" python play_server.py

echo Starting Node server...
start "" npm start

echo All services launched.
