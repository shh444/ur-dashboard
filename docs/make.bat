@ECHO OFF
SETLOCAL
PUSHD %~dp0

IF "%PYTHON%"=="" SET PYTHON=python

IF "%1"=="" GOTO help
IF "%1"=="html" GOTO html
IF "%1"=="clean" GOTO clean
GOTO help

:html
%PYTHON% build_multilang.py
GOTO end

:clean
IF EXIST build RMDIR /S /Q build
GOTO end

:help
ECHO Targets:
ECHO   make html   Build both English and Korean docs into build/html
ECHO   make clean  Remove build artifacts

:end
POPD
ENDLOCAL
