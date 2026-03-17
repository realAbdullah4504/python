@echo off
echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo Installing Tesseract OCR for Windows...
echo NOTE: This will download and install Tesseract OCR automatically
echo.

REM Check if winget is available
where winget >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Using winget to install Tesseract OCR...
    winget install -e --id UB-Mannheim.TesseractOCR
    echo.
    echo Installing Poppler for PDF to image conversion...
    winget install -e --id poppler.poppler
    if %ERRORLEVEL% neq 0 (
        echo Winget failed for Poppler, trying manual download...
        goto :install_poppler_manual
    )
) else (
    echo.
    echo Winget not found. Installing Tesseract and Poppler manually...
    goto :install_manual
)

goto :end

:install_poppler_manual
echo.
echo Downloading Poppler for Windows...
echo Creating poppler directory...
if not exist "poppler" mkdir poppler

echo Downloading Poppler release...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/oschwartz10612/poppler-windows/releases/download/v23.11.0-0/Release-23.11.0-0.zip' -OutFile 'poppler.zip'"
if %ERRORLEVEL% neq 0 (
    echo Failed to download Poppler automatically
    echo Please download manually from: https://github.com/oschwartz10612/poppler-windows/releases
    goto :manual_instructions
)

echo Extracting Poppler...
powershell -Command "Expand-Archive -Path 'poppler.zip' -DestinationPath 'poppler' -Force"
if %ERRORLEVEL% neq 0 (
    echo Failed to extract Poppler
    goto :manual_instructions
)

echo Adding Poppler to PATH...
powershell -Command "[Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH', 'User') + ';%CD%\poppler\poppler-23.11.0\Library\bin', 'User')"
echo Poppler installed to: %CD%\poppler\poppler-23.11.0\Library\bin
echo.
echo NOTE: You may need to restart your terminal for PATH changes to take effect
goto :end

:install_manual
echo.
echo 1. Downloading Tesseract OCR...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/UB-Mannheim/tesseract/wiki/raw/gh-pages/tesseract-ocr-w64-setup-5.4.0.20240606.exe' -OutFile 'tesseract-installer.exe'"
if %ERRORLEVEL% equ 0 (
    echo Running Tesseract installer...
    start /wait tesseract-installer.exe
    del tesseract-installer.exe
) else (
    echo Failed to download Tesseract automatically
    echo Please download manually from: https://github.com/UB-Mannheim/tesseract/wiki
)

echo.
echo 2. Downloading Poppler for Windows...
goto :install_poppler_manual

:manual_instructions
echo.
echo MANUAL INSTALLATION INSTRUCTIONS:
echo.
echo 1. Tesseract OCR:
echo    Download from: https://github.com/UB-Mannheim/tesseract/wiki
echo    Run the installer and make sure to check "Add Tesseract to your PATH"
echo.
echo 2. Poppler:
echo    Download from: https://github.com/oschwartz10612/poppler-windows/releases
echo    Extract to a location like C:\poppler
echo    Add the bin directory to your system PATH
echo.
echo Alternative: Use chocolatey (if available):
echo    choco install tesseract poppler

:end
echo.
echo Installation completed!
echo.
echo Please restart your terminal/command prompt after installation.
echo Make sure both Tesseract and Poppler are in your system PATH.
pause
