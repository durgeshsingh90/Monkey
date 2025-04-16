import subprocess
import time
import pyautogui

## Network drive credentials
#network_path = r'\\G4PPSS1005C2L3.1dc.com\DVOL_Omnipay\omnipay_teams\authorisation'
#username = r'1dc\f94gdos'
#password = r'ST78^$tD78'
#
## Disconnect the network drive
#try:
#    subprocess.run(['net', 'use', 'Z:', '/delete', '/y'], check=True)
#    print("Disconnected existing Z: drive")
#except subprocess.CalledProcessError as e:
#    print(f"Failed to disconnect Z: drive. Error: {e}")
#
## Connect the network drive
#try:
#    subprocess.run(['net', 'use', 'Z:', network_path, '/user:' + username, password], check=True)
#    print(f"Connected Z: drive to {network_path}")
#except subprocess.CalledProcessError as e:
#    print(f"Failed to connect Z: drive. Error: {e}")

# List of app paths
app_paths = [
#    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE',
#    'mstsc',
    r'C:\Program Files\Notepad++\notepad++.exe',
#    r'C:\Program Files\PuTTY\putty.exe',
    r'C:\Program Files\Tracker Software\PDF Editor\PDFXEdit.exe',
#    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files (x86)\Mobatek\MobaXterm\MobaXterm_Personal_23.4.exe'
]

# Open Chrome with multiple URLs
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
urls = [
    "http://localhost:8001/",  
    "http://localhost:8000/",
    "https://enterprise-jira.onefiserv.net/secure/Dashboard.jspa",
    "https://de-splunk.1dc.com/en-US/app/search/search",
    "https://fdiflxt-vip.1dc.com/tst/cgi-bin/felix",
    "https://outlook.office.com/mail/",
    "https://app.aitrium.app.atlas.gfs-emea-ai-platform.aws.fisv.cloud/"
]
try:
    # Pass all URLs as arguments to Chrome
    subprocess.Popen([chrome_path] + urls)
    print(f"Google Chrome started with URLs: {', '.join(urls)}")
except Exception as e:
    print(f"Failed to open Google Chrome with the links. Error: {e}")

# Start other apps
for app_path in app_paths:
    subprocess.Popen(app_path)
    print(f"{app_path} was successfully started.")

# Start Raptor_F Django server
django_project_path = r'C:\Durgesh\Office\Automation\Raptor_Fiserv\Raptor_F'

try:
    subprocess.Popen(['python','manage.py','runserver'], cwd=django_project_path)
    print("Raptor_F started")
except Exception as e:
    print (f"Failed to start Raptor_F django server. Error: {e}")

# Start AutoMate Django server on port 8001
django_project_path_automate = r'C:\Durgesh\Office\Automation\AutoMate\Automate'

try:
    subprocess.Popen(['python', 'manage.py', 'runserver', '8001'], cwd=django_project_path_automate)
    print("AutoMate started on port 8001")
except Exception as e:
    print(f"Failed to start AutoMate django server. Error: {e}")
