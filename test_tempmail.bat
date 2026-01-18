@echo off
REM Test Tempmail Functionality

echo ================================================================================
echo TEMPMAIL API TEST
echo ================================================================================
echo.
echo This tests the temporary email generation and OTP retrieval
echo used in the character video pipeline login process.
echo.
echo Select test mode:
echo   1 - Email Generation Only (quick test)
echo   2 - Full Automated Flow (recommended)
echo   3 - All Tests
echo.

python test_tempmail.py

echo.
pause
