import subprocess
# Start Raptor_F Django server
# django_project_path = r'C:\Durgesh\Office\Automation\Raptor_Fiserv\Raptor_F'

# try:
#     subprocess.Popen(['python','manage.py','runserver'.'8001'], cwd=django_project_path)
#     print("Raptor_F started")
# except Exception as e:
#     print (f"Failed to start Raptor_F django server. Error: {e}")

# Start AutoMate Django server on port 8001
django_project_path_automate = r'C:\Durgesh\Office\Automation\Monkey\Monkey'

try:
    subprocess.Popen(['python', 'manage.py', 'runserver', '8000'], cwd=django_project_path_automate)
    print("AutoMate started on port 8001")
except Exception as e:
    print(f"Failed to start AutoMate django server. Error: {e}")
