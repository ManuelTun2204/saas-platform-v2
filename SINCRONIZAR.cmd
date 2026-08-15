@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo   SINCRONIZAR PROYECTO CON GITHUB
echo   (descarga y sube los cambios de las 2 PCs)
echo ==================================================
echo.

echo [1/3] Descargando cambios desde GitHub...
git pull
if errorlevel 1 (
    echo.
    echo  ERROR: no se pudo descargar. Revisa tu conexion a internet.
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Guardando cambios locales (incluida la charla en chats/)...
git add -A
git commit -m "Cambios y charla guardados el %date% %time%" >nul 2>&1
echo      Listo (si habia algo que guardar).

echo.
echo [3/3] Subiendo a GitHub...
git push
if errorlevel 1 (
    echo.
    echo  ERROR: no se pudo subir. Revisa tu conexion o tus permisos en GitHub.
    echo.
    pause
    exit /b 1
)

echo.
echo  ================================================
echo   LISTO. Tu proyecto esta sincronizado en GitHub.
echo   Ahora puedes trabajar desde la otra computadora
echo   y volver a ejecutar este boton para continuar.
echo  ================================================
echo.
pause
