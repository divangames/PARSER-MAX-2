@echo off
echo ============================================
echo PARSER MAX 2 - Компиляция приложения
echo ============================================
echo.

REM Проверяем наличие PyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Установка PyInstaller...
    pip install pyinstaller
    echo.
)

REM Очищаем предыдущие сборки
echo Очистка предыдущих сборок...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
echo.

REM Компилируем приложение
echo Компиляция приложения...
pyinstaller parser.spec
echo.

REM Проверяем результат
if exist "dist\PARSER MAX 2.exe" (
    echo ============================================
    echo Компиляция успешно завершена!
    echo Исполняемый файл: dist\PARSER MAX 2.exe
    echo ============================================
) else (
    echo ============================================
    echo Ошибка при компиляции!
    echo Проверьте сообщения выше.
    echo ============================================
)

echo.
pause 