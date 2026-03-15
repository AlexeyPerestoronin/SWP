@echo off
REM Create virtual environment for Python if not created
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install requirements
pip install -r requirements.txt

REM List invoke commands
invoke --list
