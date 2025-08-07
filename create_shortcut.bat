@echo off
chcp 65001 >nul

:: Получаем путь к текущей папке
set "CURRENT_DIR=%~dp0"

:: Указываем пути
set "TARGET=%CURRENT_DIR%start_delegation_tasks.bat"
set "SHORTCUT=%CURRENT_DIR%DelegTa.lnk"
set "ICON=%CURRENT_DIR%db\images\interface\icon_small.ico"

:: Создаём временный VBScript
set "VBS=%TEMP%\make_shortcut.vbs"
(
    echo Set WshShell = WScript.CreateObject("WScript.Shell"^)
    echo Set lnk = WshShell.CreateShortcut("%SHORTCUT%"^)
    echo lnk.TargetPath = "%TARGET%"
    echo lnk.WorkingDirectory = "%CURRENT_DIR%"
    echo lnk.IconLocation = "%ICON%"
    echo lnk.Save
) > "%VBS%"

:: Запускаем VBScript для создания ярлыка
cscript //nologo "%VBS%"

:: Удаляем временный скрипт
del "%VBS%"

echo Ярлык DelegTa.lnk создан.
pause
