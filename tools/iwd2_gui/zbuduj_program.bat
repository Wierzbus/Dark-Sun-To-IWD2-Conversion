@echo off
rem Buduje przenosny program iwd2_gui_buduj.exe (Python + numpy + Pillow + scipy w jednym folderze),
rem zeby instalator paczki 1 dzialal u graczy bez zainstalowanego Pythona.
rem Uruchom RAZ w Anaconda Prompt z katalogu repo:
rem     tools\iwd2_gui\zbuduj_program.bat KATALOG_PACZKI
rem KATALOG_PACZKI = folder z setup-iwd2_upscale.tp2 (program trafi do iwd2_upscale\generator\).
setlocal
if "%~1"=="" (
  echo Podaj katalog paczki, np.: tools\iwd2_gui\zbuduj_program.bat D:\Gry\Modding\IWD2_mods\paczka1
  exit /b 1
)
if not exist "tools\iwd2_gui\buduj.py" (
  echo Uruchom z katalogu repo Dark-Sun-To-IWD2-Conversion.
  exit /b 1
)
python -m pip install --upgrade pyinstaller || exit /b 1
python -m PyInstaller --noconfirm --clean --onedir --console --name iwd2_gui_buduj ^
  --paths tools --paths tools\iwd2_gui --paths . ^
  --hidden-import scipy.ndimage ^
  --distpath build\pyi\dist --workpath build\pyi\work --specpath build\pyi ^
  tools\iwd2_gui\buduj.py || exit /b 1
if exist "%~1\iwd2_upscale\generator\iwd2_gui_buduj" rmdir /S /Q "%~1\iwd2_upscale\generator\iwd2_gui_buduj"
xcopy /E /I /Y /Q build\pyi\dist\iwd2_gui_buduj "%~1\iwd2_upscale\generator\iwd2_gui_buduj" || exit /b 1
echo.
echo Gotowe: %~1\iwd2_upscale\generator\iwd2_gui_buduj\iwd2_gui_buduj.exe
endlocal
