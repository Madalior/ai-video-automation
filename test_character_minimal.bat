@echo off
REM Test Character Video Manager - Script Generation Only

echo ================================================================================
echo CHARACTER VIDEO MANAGER - MINIMAL TEST
echo ================================================================================
echo.
echo This test runs ONLY the script generation phase (no browser automation needed)
echo.

python test_character_video_manager.py --minimal

echo.
echo ================================================================================
echo TEST COMPLETE
echo ================================================================================
pause
