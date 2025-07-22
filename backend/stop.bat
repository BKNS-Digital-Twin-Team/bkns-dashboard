@echo off
REM ================================================================
REM ==   СКРИПТ ОСТАНОВКИ СЕРВЕРА ТОЧЕЧНО ПО ПОРТУ 8000          ==
REM ================================================================

title Stop Server on Port 8000
set TARGET_PORT=8000
set PROCESS_FOUND=0

echo Searching for process(es) using port %TARGET_PORT%...

FOR /F "tokens=5" %%P IN ('netstat -a -n -o ^| findstr ":%TARGET_PORT%" ^| findstr "LISTENING"') DO (
    taskkill /F /PID %%P > NUL
    set PROCESS_FOUND=1
)

IF %PROCESS_FOUND% equ 0 (
    echo [INFO] No running processes found on port %TARGET_PORT%.
    timeout /t 2 /nobreak > NUL
) ELSE (
    echo [SUCCESS] Server process(es) on port %TARGET_PORT% terminated.
    timeout /t 1 /nobreak > NUL
)