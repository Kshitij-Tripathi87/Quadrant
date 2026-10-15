@echo off
setlocal EnableDelayedExpansion

echo ========================================================
echo   DocuGraph AI — Quick Desktop Installer
echo   Express Analytics AI/ML Take-Home Assignment
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "INSTALL_DIR=%LOCALAPPDATA%\Programs\DocuGraphAI"
set "DESKTOP_DIR=%USERPROFILE%\Desktop"
set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\DocuGraph AI"

echo Target Installation Directory: %INSTALL_DIR%
echo.

:: Create install directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Check if dist bundle or standalone setup exists
if exist "%SCRIPT_DIR%dist\DocuGraphAI" (
    echo Copying application files from dist\DocuGraphAI...
    xcopy /E /I /Y /Q "%SCRIPT_DIR%dist\DocuGraphAI\*" "%INSTALL_DIR%\" >nul
) else if exist "%SCRIPT_DIR%dist\DocuGraphAI_bundle.zip" (
    echo Extracting DocuGraphAI_bundle.zip...
    powershell -NoProfile -Command "Expand-Archive -Path '%SCRIPT_DIR%dist\DocuGraphAI_bundle.zip' -DestinationPath '%INSTALL_DIR%' -Force"
) else (
    echo Running python desktop launcher setup...
    if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
        "%SCRIPT_DIR%.venv\Scripts\python.exe" "%SCRIPT_DIR%installer\setup_gui.py" --silent
        exit /b 0
    ) else (
        echo Error: Application bundle not found. Please run installer\build_msi.py first.
        pause
        exit /b 1
    )
)

:: Copy icon
if exist "%SCRIPT_DIR%app_icon.ico" (
    copy /Y "%SCRIPT_DIR%app_icon.ico" "%INSTALL_DIR%\" >nul
)

:: Create desktop shortcut using PowerShell
echo Creating Windows Desktop Shortcut...
set "TARGET_EXE=%INSTALL_DIR%\DocuGraphAI.exe"
set "ICON_FILE=%INSTALL_DIR%\app_icon.ico"
set "SHORTCUT_PATH=%DESKTOP_DIR%\DocuGraph AI.lnk"

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_EXE%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.IconLocation = '%ICON_FILE%,0'; $s.Description = 'DocuGraph AI Technical Assistant'; $s.Save()"

:: Create start menu shortcut
echo Creating Start Menu Shortcut...
if not exist "%STARTMENU_DIR%" mkdir "%STARTMENU_DIR%"
set "START_SHORTCUT=%STARTMENU_DIR%\DocuGraph AI.lnk"
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%START_SHORTCUT%'); $s.TargetPath = '%TARGET_EXE%'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.IconLocation = '%ICON_FILE%,0'; $s.Description = 'DocuGraph AI Technical Assistant'; $s.Save()"

echo.
echo ========================================================
echo   Installation Complete!
echo   Desktop Shortcut: "%DESKTOP_DIR%\DocuGraph AI.lnk"
echo ========================================================
echo.
set /p LAUNCH="Would you like to launch DocuGraph AI now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    echo Starting DocuGraph AI...
    start "" "%TARGET_EXE%"
)

endlocal
