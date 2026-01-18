@echo off
REM Test Character Video Manager - Full Pipeline

echo ================================================================================
echo CHARACTER VIDEO MANAGER - FULL PIPELINE TEST
echo ================================================================================
echo.
echo This test runs the COMPLETE pipeline:
echo   1. Script Generation (AI)
echo   2. Image Generation (Browser - Dreamina)
echo   3. Video Generation (Browser - Veo 3)
echo   4. Thumbnail Generation (PIL)
echo.
echo NOTE: This requires browser automation and may take 15-30 minutes.
echo.
pause

python test_character_video_manager.py

echo.
echo ================================================================================
echo TEST COMPLETE
echo ================================================================================
pause
