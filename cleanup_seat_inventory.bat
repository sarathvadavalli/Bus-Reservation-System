@echo off
cd /d "%~dp0"

python manage.py cleanup_seat_inventory
pause