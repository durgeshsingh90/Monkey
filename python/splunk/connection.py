import splunklib.client as client
import traceback


HOST = "de-splunk.1dc.com"
PORT = 8089  

USERNAME = "username"
PASSWORD = "password"

def test_connection(scheme):
    try:
        print(f"Attempting to connect using {scheme.upper()}...")
        service = client.connect(
            host=HOST,
            port=PORT,
            username=USERNAME,
            password=PASSWORD,
            scheme=scheme  
        )

        if service:
            print(f"Connection to Splunk successful using {scheme.upper()}.")
        else:
            print(f"Failed to connect to Splunk using {scheme.upper()}.")
    except Exception as e:
        print(f"An error occurred using {scheme.upper()}:")
        traceback.print_exc()

test_connection("https")
test_connection("http")
