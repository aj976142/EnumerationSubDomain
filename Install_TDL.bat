@echo off
echo ======================================================
echo Tally Prime 5 - Custom TDL Package Installer
echo ======================================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo WARNING: Running without administrator privileges.
    echo Some installation paths may require administrator access.
    echo.
)

:: Set variables
set "CURRENT_DIR=%~dp0"
set "TALLY_DIR1=C:\Program Files (x86)\Tally.ERP 9"
set "TALLY_DIR2=C:\Program Files\Tally.ERP 9"
set "TALLY_DIR3=C:\TallyPrime"
set "DATA_DIR=%USERPROFILE%\TallyPrime\Data"

echo Current directory: %CURRENT_DIR%
echo.

:: Check for TDL files in current directory
if not exist "%CURRENT_DIR%TallyPrime5_CustomTDL.tdl" (
    echo ERROR: TallyPrime5_CustomTDL.tdl not found in current directory!
    pause
    exit /b 1
)

if not exist "%CURRENT_DIR%TallyPrime5_ExcelImport.tdl" (
    echo ERROR: TallyPrime5_ExcelImport.tdl not found in current directory!
    pause
    exit /b 1
)

echo TDL files found:
echo - TallyPrime5_CustomTDL.tdl
echo - TallyPrime5_ExcelImport.tdl
echo.

:: Find Tally installation directory
set "TALLY_INSTALL_DIR="

if exist "%TALLY_DIR1%" (
    set "TALLY_INSTALL_DIR=%TALLY_DIR1%"
    echo Found Tally installation at: %TALLY_DIR1%
) else if exist "%TALLY_DIR2%" (
    set "TALLY_INSTALL_DIR=%TALLY_DIR2%"
    echo Found Tally installation at: %TALLY_DIR2%
) else if exist "%TALLY_DIR3%" (
    set "TALLY_INSTALL_DIR=%TALLY_DIR3%"
    echo Found Tally installation at: %TALLY_DIR3%
) else (
    echo WARNING: Tally Prime installation not found in standard locations.
    echo Please specify the Tally installation directory manually.
    echo.
    set /p "TALLY_INSTALL_DIR=Enter Tally installation path: "
    
    if not exist "%TALLY_INSTALL_DIR%" (
        echo ERROR: Specified directory does not exist!
        pause
        exit /b 1
    )
)

echo.
echo Installation Options:
echo 1. Install to Tally program directory (Recommended)
echo 2. Install to user data directory
echo 3. Custom installation path
echo.

set /p "INSTALL_OPTION=Choose installation option (1-3): "

if "%INSTALL_OPTION%"=="1" (
    set "INSTALL_PATH=%TALLY_INSTALL_DIR%"
) else if "%INSTALL_OPTION%"=="2" (
    if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"
    set "INSTALL_PATH=%DATA_DIR%"
) else if "%INSTALL_OPTION%"=="3" (
    set /p "INSTALL_PATH=Enter custom installation path: "
    if not exist "%INSTALL_PATH%" (
        echo Creating directory: %INSTALL_PATH%
        mkdir "%INSTALL_PATH%"
    )
) else (
    echo Invalid option selected!
    pause
    exit /b 1
)

echo.
echo Installing TDL files to: %INSTALL_PATH%
echo.

:: Create backup if files already exist
if exist "%INSTALL_PATH%\TallyPrime5_CustomTDL.tdl" (
    echo Creating backup of existing TallyPrime5_CustomTDL.tdl...
    copy "%INSTALL_PATH%\TallyPrime5_CustomTDL.tdl" "%INSTALL_PATH%\TallyPrime5_CustomTDL.tdl.bak" >nul
)

if exist "%INSTALL_PATH%\TallyPrime5_ExcelImport.tdl" (
    echo Creating backup of existing TallyPrime5_ExcelImport.tdl...
    copy "%INSTALL_PATH%\TallyPrime5_ExcelImport.tdl" "%INSTALL_PATH%\TallyPrime5_ExcelImport.tdl.bak" >nul
)

:: Copy TDL files
echo Copying TDL files...
copy "%CURRENT_DIR%TallyPrime5_CustomTDL.tdl" "%INSTALL_PATH%\" >nul
if %errorLevel% neq 0 (
    echo ERROR: Failed to copy TallyPrime5_CustomTDL.tdl
    echo Please check permissions and try running as administrator.
    pause
    exit /b 1
)

copy "%CURRENT_DIR%TallyPrime5_ExcelImport.tdl" "%INSTALL_PATH%\" >nul
if %errorLevel% neq 0 (
    echo ERROR: Failed to copy TallyPrime5_ExcelImport.tdl
    echo Please check permissions and try running as administrator.
    pause
    exit /b 1
)

:: Copy documentation if exists
if exist "%CURRENT_DIR%TDL_Documentation.md" (
    echo Copying documentation...
    copy "%CURRENT_DIR%TDL_Documentation.md" "%INSTALL_PATH%\" >nul
)

echo.
echo ======================================================
echo Installation completed successfully!
echo ======================================================
echo.
echo TDL files installed to: %INSTALL_PATH%
echo.
echo Next Steps:
echo 1. Open Tally Prime
echo 2. Press F1 (Help) ^> TDL ^& Add-On ^> TDL Management
echo 3. Load the following TDL files:
echo    - TallyPrime5_CustomTDL.tdl
echo    - TallyPrime5_ExcelImport.tdl
echo 4. Check Gateway of Tally for "Custom Reports" menu
echo 5. Test keyboard shortcuts (Alt+C, Alt+L, Alt+O, Alt+G)
echo.
echo Features:
echo - Custom Dashboard (Alt+C)
echo - Enhanced Ledger Report (Alt+L)  
echo - Outstanding Analysis (Alt+O)
echo - GST Summary Report (Alt+G)
echo - Excel Import/Export functionality
echo.

:: Create shortcut to documentation if possible
if exist "%INSTALL_PATH%\TDL_Documentation.md" (
    echo Documentation available at: %INSTALL_PATH%\TDL_Documentation.md
    echo.
)

echo Installation log saved to: %INSTALL_PATH%\install_log.txt
echo %date% %time% - TDL Package installed successfully > "%INSTALL_PATH%\install_log.txt"
echo Installation path: %INSTALL_PATH% >> "%INSTALL_PATH%\install_log.txt"
echo Files installed: TallyPrime5_CustomTDL.tdl, TallyPrime5_ExcelImport.tdl >> "%INSTALL_PATH%\install_log.txt"

echo.
echo IMPORTANT: Always backup your Tally data before using new TDL files!
echo.

pause