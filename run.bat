@echo off
title Fortune Summoners Unpacker v2.0.0

rem You can configure the following variables (careful when using & and ^ characters):
set python-path=
set parameters=-c -i

%python-path% "cli.py" %* %parameters%

echo Finished with exit code %ERRORLEVEL%.

pause >nul
