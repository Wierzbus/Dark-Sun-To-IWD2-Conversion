@echo off
rem Build nowych lokacji + synchronizacja moda do folderu IWD2. WeiDU (odinstalowanie/instalacja) uruchamiasz sam.
rem Uruchamiaj w Anaconda Prompt, z dowolnego katalogu. Komponenty: 1 = AR9020, 2 = AR9021.
setlocal
set "PROJ=D:\Gry\Modding\iwd2_nowe_lokacje"
set "IWD=D:\Gry\Icewind Dale 2"

pushd "%PROJ%"
for %%A in (AR9020 AR9021) do (
  echo === Build %%A
  python -m geometry.image_area --dir areas_custom\%%A --name %%A
  if errorlevel 1 (
    echo BLAD BUDOWY %%A - przerywam.
    popd
    pause
    exit /b 1
  )
)
popd

echo === Synchronizacja moda do folderu IWD2 (bez katalogu backup)
robocopy "%PROJ%\mod\iwd2_nowe_lokacje" "%IWD%\iwd2_nowe_lokacje" /E /XD backup /XF setup-iwd2_nowe_lokacje.tp2 /NFL /NDL /NJH /NJS >nul
copy /Y "%PROJ%\mod\iwd2_nowe_lokacje\setup-iwd2_nowe_lokacje.tp2" "%IWD%\setup-iwd2_nowe_lokacje.tp2" >nul

echo.
echo Gotowe. Odinstaluj i zainstaluj komponenty WeiDU recznie.
pause
endlocal
