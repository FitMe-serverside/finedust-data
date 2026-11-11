@echo off
setlocal
cd /d "%~dp0.."
set "LOG=%~dp0restore.log"
echo [%date% %time%] start > "%LOG%"
git fetch origin main >> "%LOG%" 2>&1
git reset origin/main >> "%LOG%" 2>&1
rem 실수로 지운 data 파일을 지우기 직전 커밋(7d8e705)에서 되살린다(이미 Actions가 새로 만들었으면 건너뜀)
git cat-file -e origin/main:data/now.json 2>nul && (echo ALREADY_RESTORED >> "%LOG%" & goto end)
git checkout 7d8e705 -- data/now.json data/stations.json >> "%LOG%" 2>&1
git add data >> "%LOG%" 2>&1
git commit -m "restore data files" >> "%LOG%" 2>&1
git push origin main >> "%LOG%" 2>&1
echo PUSH_EXIT=%errorlevel% >> "%LOG%"
:end
echo [%date% %time%] DONE >> "%LOG%"
exit
