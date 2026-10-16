@echo off
REM Rebuild CapsLockOSD.exe on Windows using the C# compiler built into .NET Framework 4 (no Visual Studio needed)
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
if not exist release mkdir release
"%CSC%" /nologo /target:winexe /optimize+ /win32icon:assets\app.ico /r:System.Drawing.dll /r:System.Windows.Forms.dll /out:release\CapsLockOSD.exe src\Program.cs
if errorlevel 1 (echo Build failed & pause & exit /b 1)
echo Built release\CapsLockOSD.exe
echo (Optional) To rebuild the installer, install NSIS and run: makensis installer\installer.nsi
pause
