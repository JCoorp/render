@echo off
title Visor Casita - Color y Texturas Fix
echo Iniciando visor con materiales corregidos...
echo.
echo PC:
echo http://localhost:5502
echo.
echo Android:
echo Usa la IP actual de tu PC con puerto 5502
echo.
npx http-server . -p 5502 -a 0.0.0.0
pause
