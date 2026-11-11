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
rem data 폴더는 GitHub Actions가 만든다. PC에 없어서 지워지지 않도록 GitHub 것을 그대로 가져온다.
git checkout origin/main -- data >> "%LOG%" 2>&1
git add -A >> "%LOG%" 2>&1
git commit -m "update relay scripts" >> "%LOG%" 2>&1
git push -u origin main >> "%LOG%" 2>&1
echo PUSH_EXIT=%errorlevel% >> "%LOG%"
echo [%date% %time%] DONE >> "%LOG%"
exit
