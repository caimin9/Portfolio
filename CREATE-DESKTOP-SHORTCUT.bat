@echo off
title Create Desktop Shortcut

echo Creating desktop shortcut for Portfolio Terminal...

set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop

REM Create VBS script to make shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%DESKTOP%\Portfolio Terminal.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%SCRIPT_DIR%START-TERMINAL.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "Launch Portfolio Terminal" >> CreateShortcut.vbs
echo oLink.IconLocation = "C:\Windows\System32\SHELL32.dll,41" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

REM Run the VBS script
cscript CreateShortcut.vbs >nul

REM Clean up
del CreateShortcut.vbs

echo.
echo ========================================
echo   SHORTCUT CREATED!
echo ========================================
echo.
echo A shortcut "Portfolio Terminal" has been
echo created on your desktop.
echo.
echo Double-click it to launch your terminal!
echo.
pause
