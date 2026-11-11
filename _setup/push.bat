@echo off
setlocal
cd /d "%~dp0.."
set "LOG=%~dp0push.log"
echo [%date% %time%] start > "%LOG%"
if not exist ".github\workflows" mkdir ".github\workflows"
copy /y "_setup\update.yml" ".github\workflows\update.yml" >> "%LOG%" 2>&1
if not exist ".git" (
  git init -b main >> "%LOG%" 2>&1
  git remote add origin https://github.com/FitMe-serverside/finedust-data.git >> "%LOG%" 2>&1
)
git config user.name "SingNumber"
git config user.email "postshare.co.kr@gmail.com"
git config core.autocrlf false
git fetch origin main >> "%LOG%" 2>&1
git reset origin/main >> "%LOG%" 2>&1
git add -A >> "%LOG%" 2>&1
git commit -m "fetch all stations in one call every 10 minutes" >> "%LOG%" 2>&1
git push -u origin main >> "%LOG%" 2>&1
echo PUSH_EXIT=%errorlevel% >> "%LOG%"
echo [%date% %time%] DONE >> "%LOG%"
exit
