@echo off
chcp 65001 >nul

:: === 1. Проверка наличия Python ===
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python не установлен на этом компьютере.
    set /p install_python="Хотите установить Python автоматически? (y/n): "
    if /I "%install_python%"=="y" (
        echo Скачивание установщика Python...

        :: Задаём URL для последней версии Python (Windows x64)
        set "PYTHON_URL=https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe"
        set "INSTALLER=%TEMP%\python_installer.exe"

        :: Скачиваем установщик через PowerShell
        powershell -Command "(New-Object System.Net.WebClient).DownloadFile('%PYTHON_URL%', '%INSTALLER%')"

        if exist "%INSTALLER%" (
            echo Установка Python...
            :: /quiet - тихая установка, InstallAllUsers=1 - для всех пользователей
            :: PrependPath=1 - добавить Python в PATH
            "%INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
            echo Установка завершена. Проверка...

            :: Обновляем переменные окружения в текущей сессии
            setx PATH "%PATH%;C:\Program Files\Python312\Scripts;C:\Program Files\Python312"

            python --version >nul 2>&1
            IF %ERRORLEVEL% EQU 0 (
                echo Python успешно установлен!
            ) ELSE (
                echo Ошибка: Python не удалось установить.
                pause
                exit /b
            )
        ) else (
            echo Ошибка загрузки установщика Python.
            pause
            exit /b
        )
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
