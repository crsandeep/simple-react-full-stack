@echo off
rem Copyright 2013 Google Inc. All Rights Reserved.

SETLOCAL
SET CLOUDSDK_ROOT_DIR=%~dp0
rem <cloud-sdk-cmd-preamble>
rem
rem  CLOUDSDK_ROOT_DIR            (a)  installation root dir
rem  CLOUDSDK_PYTHON              (u)  python interpreter path
rem  CLOUDSDK_GSUTIL_PYTHON       (u)  python interpreter path for gsutil
rem  CLOUDSDK_PYTHON_ARGS         (u)  python interpreter arguments
rem  CLOUDSDK_PYTHON_SITEPACKAGES (u)  use python site packages
rem
rem (a) always defined by the preamble
rem (u) user definition overrides preamble

rem This command lives in google-cloud-sdk\bin or google-cloud-sdk\ so it or its
rem parent directory is the root. Don't enable DelayedExpansion yet or we
rem destroy PATHs that have exclamation marks. Quotes needed to support
rem ampersands.
IF "%CLOUDSDK_ROOT_DIR%"=="" (
  rem If sourced in install.bat ROOT_DIR is already defined. This case handles
  rem setting the ROOT_DIR for every other usecase.
  SET "CLOUDSDK_ROOT_DIR=%~dp0.."
)
SET "PATH=%CLOUDSDK_ROOT_DIR%\bin\sdk;%PATH%"

rem %PYTHONHOME% can interfere with gcloud. Users should use
rem CLOUDSDK_PYTHON to configure which python gcloud uses.
SET PYTHONHOME=


SETLOCAL EnableDelayedExpansion

IF "!CLOUDSDK_PYTHON!"=="" (
  SET BUNDLED_PYTHON=!CLOUDSDK_ROOT_DIR!\platform\bundledpython\python.exe
  IF EXIST "!BUNDLED_PYTHON!" (
    SET CLOUDSDK_PYTHON=!BUNDLED_PYTHON!
  )
)

for %%X in (where.exe) do (set WHERE_FOUND=%%~$PATH:X)

IF defined WHERE_FOUND (
  IF "!CLOUDSDK_PYTHON!"=="" (
    where /q python
    IF NOT ERRORLEVEL 1 (
      FOR /F "tokens=* USEBACKQ" %%F IN (`where python`) DO (
      SET PYTHON_CANDIDATE_PATH="%%F"
        "!PYTHON_CANDIDATE_PATH!" -c "import sys; print(sys.version)" > tmpfile
      set PYTHON_CANDIDATE_VERSION=
      set /p PYTHON_CANDIDATE_VERSION= < tmpfile
      del tmpfile
      IF "!PYTHON_CANDIDATE_VERSION:~0,1!"=="2" (
        SET CLOUDSDK_PYTHON="%%F"
      SET CLOUDSDK_PYTHON_VERSION="!PYTHON_CANDIDATE_VERSION!"
      )
      )
    )
  )

  IF "!CLOUDSDK_PYTHON!"=="" (
    where /q python
    IF NOT ERRORLEVEL 1 (
      FOR /F "tokens=* USEBACKQ" %%F IN (`where python`) DO (
      SET PYTHON_CANDIDATE_PATH="%%F"
        "!PYTHON_CANDIDATE_PATH!" -c "import sys; print(sys.version)" > tmpfile
      set PYTHON_CANDIDATE_VERSION=
      set /p PYTHON_CANDIDATE_VERSION= < tmpfile
      del tmpfile
      IF "!PYTHON_CANDIDATE_VERSION:~0,1!"=="3" (
        SET CLOUDSDK_PYTHON="%%F"
      SET CLOUDSDK_PYTHON_VERSION="!PYTHON_CANDIDATE_VERSION!"
      )
      )
    )
  )

  IF "!CLOUDSDK_PYTHON!"=="" (
    where /q python3
    IF NOT ERRORLEVEL 1 (
      FOR /F "tokens=* USEBACKQ" %%F IN (`where python3`) DO (
      SET PYTHON_CANDIDATE_PATH="%%F"
        "!PYTHON_CANDIDATE_PATH!" -c "import sys; print(sys.version)" > tmpfile
      set PYTHON_CANDIDATE_VERSION=
      set /p PYTHON_CANDIDATE_VERSION= < tmpfile
      del tmpfile
      IF "!PYTHON_CANDIDATE_VERSION:~0,1!"=="3" (
        SET CLOUDSDK_PYTHON="%%F"
      SET CLOUDSDK_PYTHON_VERSION="!PYTHON_CANDIDATE_VERSION!"
      )
      )
    )
  )
)

IF "!CLOUDSDK_PYTHON!"=="" (
  SET CLOUDSDK_PYTHON="python.exe"
)


SET NO_WORKING_PYTHON_FOUND="false"
rem We run sys.version to ensure it's not the Windows Store python.exe
"!CLOUDSDK_PYTHON!" -c "import sys; print(sys.version)" >nul 2>&1
IF NOT %ERRORLEVEL%==0 (
  SET NO_WORKING_PYTHON_FOUND="true"
)

IF "%CLOUDSDK_PYTHON_SITEPACKAGES%" == "" (
  IF "!VIRTUAL_ENV!" == "" (
    SET CLOUDSDK_PYTHON_SITEPACKAGES=
  ) ELSE (
    SET CLOUDSDK_PYTHON_SITEPACKAGES=1
  )
)
SET CLOUDSDK_PYTHON_ARGS_NO_S=!CLOUDSDK_PYTHON_ARGS:-S=!
IF "%CLOUDSDK_PYTHON_SITEPACKAGES%" == "" (
  IF "!CLOUDSDK_PYTHON_ARGS!" == "" (
    SET CLOUDSDK_PYTHON_ARGS=-S
  ) ELSE (
    SET CLOUDSDK_PYTHON_ARGS=!CLOUDSDK_PYTHON_ARGS_NO_S! -S
  )
) ELSE IF "!CLOUDSDK_PYTHON_ARGS!" == "" (
  SET CLOUDSDK_PYTHON_ARGS=
) ELSE (
  SET CLOUDSDK_PYTHON_ARGS=!CLOUDSDK_PYTHON_ARGS_NO_S!
)

rem TODO(b/133246173): Remove this once we want to default to Python 3.
rem Allow users to set the Python interpreter used to launch gsutil, falling
rem back to the CLOUDSDK_PYTHON interpreter otherwise. In the future, if this
rem is not set, we'll try finding (and prefer using) Python 3 before falling
rem back to the default Cloud SDK Python.
IF "%CLOUDSDK_GSUTIL_PYTHON%" == "" (
  SET CLOUDSDK_GSUTIL_PYTHON=!CLOUDSDK_PYTHON!
)

rem Gsutil prefers Python 3 if it is available, which may likely differ from the
rem $CLOUDSDK_PYTHON version. We launch Gsutil with $CLOUDSDK_GSUTIL_PYTHON; the
rem user can set this to any interpreter they like, so we only try to find
rem Python 3 for them if they haven't specified the interpreter already.
IF "%CLOUDSDK_GSUTIL_PYTHON%" == "" (
  where /q python3
  IF NOT ERRORLEVEL 1 (
    FOR /F "tokens=* USEBACKQ" %%F IN (`where python3`) DO (
    SET CLOUDSDK_GSUTIL_PYTHON=%%F )
  ) ELSE (
    where /q python
    IF NOT ERRORLEVEL 1 (
      FOR /F "tokens=* USEBACKQ" %%F IN (`where python`) DO (
      SET CLOUDSDK_GSUTIL_PYTHON=%%F )
    ) ELSE (
      SET CLOUDSDK_GSUTIL_PYTHON=!CLOUDSDK_PYTHON!
    )
  )
)


SETLOCAL DisableDelayedExpansion

rem </cloud-sdk-cmd-preamble>

echo %CmdCmdLine% | %WINDIR%\System32\find /i "%~0" >nul
SET INTERACTIVE=%ERRORLEVEL%
rem install.bat lives in the root of the Cloud SDK installation directory.

echo Welcome to the Google Cloud SDK!

IF "%CLOUDSDK_COMPONENT_MANAGER_SNAPSHOT_URL%"=="" (
  GOTO SETENABLEDELAYED
  ) ELSE (
    echo WARNING: You have set the environment variable
    echo CLOUDSDK_COMPONENT_MANAGER_SNAPSHOT_URL to
    echo %CLOUDSDK_COMPONENT_MANAGER_SNAPSHOT_URL%. This may cause installation
    echo to fail. If installation fails, run "SET
    echo CLOUDSDK_COMPONENT_MANAGER_SNAPSHOT_URL=" and try again.
  )

:SETENABLEDELAYED
SETLOCAL EnableDelayedExpansion

rem temporarily set code page to utf-8 support
for /F "tokens=4" %%G in ('chcp') do (set OLD_CP=%%G)
set PYTHONIOENCODING=utf-8
chcp 65001

IF %NO_WORKING_PYTHON_FOUND%=="true" (
  echo.
  echo To use the Google Cloud SDK, you must have Python installed and on your PATH.
  echo As an alternative, you may also set the CLOUDSDK_PYTHON environment variable
  echo to the location of your Python executable.
  "%COMSPEC%" /C exit 1
) ELSE (
  rem copy_bundled_python.py will make a copy of the Python interpreter if it's
  rem bundled in the Cloud SDK installation and report the location of the new
  rem interpreter. We want to use this copy to install the Cloud SDK, since the
  rem bundled copy can't modify itself.
  FOR /F "delims=" %%i in (
    '""%COMSPEC%" /U /C ""!CLOUDSDK_PYTHON!" "!CLOUDSDK_ROOT_DIR!\lib\gcloud.py""" components copy-bundled-python'
  ) DO (
    SET CLOUDSDK_PYTHON=%%i
  )
  "%COMSPEC%" /U /C ""!CLOUDSDK_PYTHON!" "!CLOUDSDK_ROOT_DIR!\bin\bootstrapping\install.py" %*"
)

set EXIT_CODE=%ERRORLEVEL%

chcp %OLD_CP%

IF _%INTERACTIVE%_==_0_ (
  IF _%CLOUDSDK_CORE_DISABLE_PROMPTS%_==__ (
    echo Google Cloud SDK installer will now exit.
    PAUSE
  )
)

"%COMSPEC%" /C exit %EXIT_CODE%
