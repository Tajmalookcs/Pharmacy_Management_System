Set WshShell = CreateObject("WScript.Shell")

' Start Django server silently (window style 0 = hidden)
WshShell.Run "cmd /c cd /d D:\Pharmacy_Management_System && venv\Scripts\activate.bat && python manage.py runserver 127.0.0.1:8000", 0, False

' Wait 2 seconds for server to start
WScript.Sleep 2000

' Open browser
WshShell.Run "http://127.0.0.1:8000", 1, False

Set WshShell = Nothing
