@echo off
REM Direct test of video generator without Python imports
echo ========================================
echo Testing Veo 3.1 Video Generator
echo ========================================
echo.

cd /d "c:\Users\vijay\OneDrive\Pictures\automation tool\flowchart\character"

echo [1] Testing if video_generator.py can run standalone...
python video_generator.py
if %errorlevel% neq 0 (
    echo.
    echo Generator needs to be run from main project directory
    echo Trying alternative method...
    cd /d "c:\Users\vijay\OneDrive\Pictures\automation tool"
    
    echo.
    echo [2] Running direct Python command...
    python -c "import sys; sys.path.insert(0, '.'); exec(open('flowchart/character/video_generator.py').read()); print('Generator imported successfully!')"
)

echo.
echo ========================================
echo Test complete
echo ========================================
pause
