; AMS Caps Lock OSD - installer (per-user, no admin rights required)
Unicode true
!include "MUI2.nsh"

!define APPNAME   "AMS Caps Lock OSD"
!define BRAND     "AMS"
!define EXENAME   "CapsLockOSD.exe"
!define VERSION   "1.1.0"
!define YOUTUBE   "https://www.youtube.com/channel/UCW5b5zJ1MW35P1x9--ExMvg"
!define UNINSTKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\CapsLockOSD"
!define RUNKEY    "Software\Microsoft\Windows\CurrentVersion\Run"

Name "${APPNAME}"
Caption "${APPNAME} Setup  -  by ${BRAND}"
UninstallCaption "${APPNAME} Uninstall  -  by ${BRAND}"
OutFile "..\release\AMS-CapsLockOSD-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\AMS\CapsLockOSD"
RequestExecutionLevel user
SetCompressor /SOLID lzma
BrandingText "${BRAND}  |  ${APPNAME} ${VERSION}"

VIProductVersion "1.1.0.0"
VIAddVersionKey "ProductName" "${APPNAME}"
VIAddVersionKey "CompanyName" "${BRAND}"
VIAddVersionKey "FileDescription" "${APPNAME} Setup"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "(c) 2026 ${BRAND}"

!define MUI_ICON   "..\assets\app.ico"
!define MUI_UNICON "..\assets\app.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "..\assets\wizard.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "..\assets\wizard.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "..\assets\header.bmp"
!define MUI_HEADERIMAGE_UNBITMAP "..\assets\header.bmp"
!define MUI_ABORTWARNING

!define MUI_WELCOMEPAGE_TITLE "Welcome to ${APPNAME}"
!define MUI_WELCOMEPAGE_TEXT "Created by ${BRAND}.$\r$\n$\r$\n${APPNAME} shows a clean on-screen indicator every time you turn Caps Lock ON or OFF.$\r$\n$\r$\nIt runs quietly in the system tray and starts automatically with Windows.$\r$\n$\r$\nClick Next to continue."
!define MUI_FINISHPAGE_TITLE "${APPNAME} is installed"
!define MUI_FINISHPAGE_TEXT "Thank you for installing ${APPNAME} by ${BRAND}!$\r$\n$\r$\nPress Caps Lock to see it in action.$\r$\n$\r$\nSubscribe to ${BRAND} on YouTube for more tools."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXENAME}"
!define MUI_FINISHPAGE_RUN_TEXT "Start ${APPNAME} now"
!define MUI_FINISHPAGE_LINK "${BRAND} on YouTube"
!define MUI_FINISHPAGE_LINK_LOCATION "${YOUTUBE}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!define MUI_FINISHPAGE_TITLE "${APPNAME} has been removed"
!define MUI_FINISHPAGE_TEXT "${APPNAME} by ${BRAND} was uninstalled from your computer.$\r$\n$\r$\nThanks for using it!"
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
  ; close a running copy (upgrade / reinstall)
  nsExec::Exec 'taskkill /F /IM "${EXENAME}"'
  Sleep 400

  ; remove files from the old v1.0 location if present
  Delete "$LOCALAPPDATA\Programs\CapsLockOSD\${EXENAME}"
  Delete "$LOCALAPPDATA\Programs\CapsLockOSD\app.ico"
  Delete "$LOCALAPPDATA\Programs\CapsLockOSD\Uninstall.exe"
  RMDir  "$LOCALAPPDATA\Programs\CapsLockOSD"
  Delete "$SMPROGRAMS\Caps Lock OSD.lnk"

  SetOutPath "$INSTDIR"
  File "..\release\${EXENAME}"
  File "..\assets\app.ico"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; start with Windows
  WriteRegStr HKCU "${RUNKEY}" "CapsLockOSD" '"$INSTDIR\${EXENAME}"'

  ; Start menu shortcuts
  CreateDirectory "$SMPROGRAMS\${BRAND}"
  CreateShortcut "$SMPROGRAMS\${BRAND}\${APPNAME}.lnk" "$INSTDIR\${EXENAME}" "" "$INSTDIR\app.ico"
  CreateShortcut "$SMPROGRAMS\${BRAND}\Uninstall ${APPNAME}.lnk" "$INSTDIR\Uninstall.exe"

  ; Apps & Features entry
  WriteRegStr   HKCU "${UNINSTKEY}" "DisplayName"     "${APPNAME}"
  WriteRegStr   HKCU "${UNINSTKEY}" "DisplayVersion"  "${VERSION}"
  WriteRegStr   HKCU "${UNINSTKEY}" "Publisher"       "${BRAND}"
  WriteRegStr   HKCU "${UNINSTKEY}" "URLInfoAbout"    "${YOUTUBE}"
  WriteRegStr   HKCU "${UNINSTKEY}" "HelpLink"        "${YOUTUBE}"
  WriteRegStr   HKCU "${UNINSTKEY}" "DisplayIcon"     "$INSTDIR\app.ico"
  WriteRegStr   HKCU "${UNINSTKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr   HKCU "${UNINSTKEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTKEY}" "NoRepair" 1
  WriteRegDWORD HKCU "${UNINSTKEY}" "EstimatedSize" 250
SectionEnd

; Opens the AMS YouTube channel exactly once after a successful install
Function .onInstSuccess
  ExecShell "open" "${YOUTUBE}"
FunctionEnd

Section "Uninstall"
  nsExec::Exec 'taskkill /F /IM "${EXENAME}"'
  Sleep 400
  DeleteRegValue HKCU "${RUNKEY}" "CapsLockOSD"
  DeleteRegKey   HKCU "${UNINSTKEY}"
  Delete "$SMPROGRAMS\${BRAND}\${APPNAME}.lnk"
  Delete "$SMPROGRAMS\${BRAND}\Uninstall ${APPNAME}.lnk"
  RMDir  "$SMPROGRAMS\${BRAND}"
  Delete "$INSTDIR\${EXENAME}"
  Delete "$INSTDIR\app.ico"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir  "$INSTDIR"
  RMDir  "$LOCALAPPDATA\Programs\AMS"
SectionEnd

; Opens the AMS YouTube channel exactly once after a successful uninstall
Function un.onUninstSuccess
  ExecShell "open" "${YOUTUBE}"
FunctionEnd
