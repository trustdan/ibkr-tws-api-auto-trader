@echo off
echo Building TraderAdmin...

cd frontend
call npm ci
call npm run build
cd ..

call wails build

echo Build complete! Output in build/bin directory. 