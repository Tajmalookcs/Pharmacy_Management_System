@echo off
cd /d D:\Pharmacy_Management_System

call venv\Scripts\activate.bat

start "" python manage.py runserver

start http://127.0.0.1:8000

exit