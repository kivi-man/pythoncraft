@echo off
echo Installing required Python packages...

:: Python'un yüklenip yüklenmediğini kontrol et
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python first.
    pause
    exit /b 1
)

:: Paketleri yükle
pip install ursina
pip install noise
pip install psutil

echo Installation complete.
pause
