@echo off
chcp 65001 >nul

:: === 1. Проверка наличия Python ===
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python не установлен на этом компьютере.
    set /p install_python="Хотите установить Python? (y/n): "
    if /I "%install_python%"=="y" (
        echo Пожалуйста, скачайте и установите Python с https://www.python.org/downloads/
        pause
        exit /b
    ) else (
        echo Без Python выполнение невозможно.
        pause
        exit /b
    )
)

:: === 2. Проверка и установка библиотек ===
echo Проверка необходимых библиотек...
python -c "import json" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo json отсутствует. (Эта библиотека встроена в Python, проверьте установку)
)

python -c "import PySide6" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Библиотека PySide6 не установлена.
    set /p install_pyside="Установить PySide6? (y/n): "
    if /I "%install_pyside%"=="y" (
        echo Устанавливаю PySide6...
        pip install PySide6
    ) else (
        echo Без PySide6 выполнение невозможно.
        pause
        exit /b
    )
)

:: === 3. Запуск main.py ===
echo Запуск main.py...
start "" /B pythonw.exe "%~dp0main.py"
exit
