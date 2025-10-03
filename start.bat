@echo off
echo Starting TouchDesigner WebSocket Server...
echo.
echo Installing dependencies...
call npm install
echo.
echo Starting server on http://localhost:9980
echo Press Ctrl+C to stop the server
echo.
npm start
pause
