@echo off
setlocal

rem PDF Toolbox launcher for Windows. Double-click this file to start the app.
cd /d "%~dp0"

if not exist "pdf_toolbox.py" (
    echo pdf_toolbox.py が見つかりません。この bat ファイルをリポジトリのルートに置いて実行してください。
    pause
    exit /b 1
)

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "%CD%\pdf_toolbox.py"
    exit /b 0
)

if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" "%CD%\pdf_toolbox.py"
    exit /b 0
)

where pyw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pyw.exe -3 "%CD%\pdf_toolbox.py"
    exit /b 0
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
    start "" pythonw.exe "%CD%\pdf_toolbox.py"
    exit /b 0
)

where py.exe >nul 2>nul
if not errorlevel 1 (
    start "" py.exe -3 "%CD%\pdf_toolbox.py"
    exit /b 0
)

where python.exe >nul 2>nul
if not errorlevel 1 (
    start "" python.exe "%CD%\pdf_toolbox.py"
    exit /b 0
)

echo Python が見つかりません。Python 3.10 以降をインストールしてから再実行してください。
pause
exit /b 1
