from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import json
import os
from django.views.decorators.csrf import csrf_exempt

BASE_DIR = settings.BASE_DIR
CONFIG_PATH = os.path.join(BASE_DIR, 'media', 'slot_booking', 'config.json')
SUBMISSIONS_FILE = os.path.join(BASE_DIR, 'media', 'slot_booking', 'submissions.json')
COUNTER_FILE = os.path.join(BASE_DIR, 'media', 'slot_booking', 'counter.json')

def ensure_files_exist():
    os.makedirs(os.path.dirname(SUBMISSIONS_FILE), exist_ok=True)

    if not os.path.exists(SUBMISSIONS_FILE):
        with open(SUBMISSIONS_FILE, 'w') as file:
            json.dump({"submissions": []}, file)

    if not os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'w') as file:
            json.dump({"last_booking_id": 0}, file)

    if not os.path.exists(CONFIG_PATH):
        default_config = {
            "psps": [{"name": "DummyPSP", "pspID": "001"}],
            "owners": [{"name": "John Doe", "lanID": "jdoe"}],
            "servers": [{"hostname": "dummyhost", "user": "dummyuser"}],
            "schemeTypes": [{"name": "Visa"}, {"name": "MasterCard"}],
            "simulators": [{"name": "DummySim", "ipAddress": "127.0.0.1"}]
        }
        with open(CONFIG_PATH, 'w') as file:
            json.dump(default_config, file, indent=4)

def read_counter():
    with open(COUNTER_FILE, 'r') as file:
        data = json.load(file)
        return data.get('last_booking_id', 0)

def write_counter(counter):
    with open(COUNTER_FILE, 'w') as file:
        json.dump({'last_booking_id': counter}, file)

def index(request):
    ensure_files_exist()
    return render(request, 'slot_booking/index.html')

def admin(request):
    ensure_files_exist()
    return render(request, 'slot_booking/admin.html')

@csrf_exempt
def config(request):
    ensure_files_exist()  # ✅ Ensure all files exist including config.json

    if request.method == 'GET':
        try:
            with open(CONFIG_PATH, 'r') as file:
                config_data = json.load(file)
                return JsonResponse(config_data, safe=False)
        except FileNotFoundError:
            return HttpResponse("Config file not found", status=404)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            with open(CONFIG_PATH, 'w') as file:
                json.dump(data, file, indent=4)
            return HttpResponse("Config saved successfully", status=200)
        except Exception as e:
            return HttpResponse(f"Failed to save config: {str(e)}", status=500)

@csrf_exempt
def submissions(request):
    ensure_files_exist()

    if request.method == 'GET':
        try:
            with open(SUBMISSIONS_FILE, 'r') as file:
                submissions_data = json.load(file)
                return JsonResponse(submissions_data, safe=False)
        except FileNotFoundError:
            return HttpResponse("submissions file not found", status=404)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            with open(SUBMISSIONS_FILE, 'w') as file:
                json.dump(data, file, indent=4)
            return HttpResponse("submissions saved successfully", status=200)
        except Exception as e:
            return HttpResponse(f"Failed to save submissions: {str(e)}", status=500)

    return HttpResponse("Method not allowed", status=405)


def is_date_range_overlap(start1, end1, start2, end2):
    from datetime import datetime
    start1 = datetime.strptime(start1, "%d/%m/%Y")
    end1 = datetime.strptime(end1, "%d/%m/%Y")
    start2 = datetime.strptime(start2, "%d/%m/%Y")
    end2 = datetime.strptime(end2, "%d/%m/%Y")
    return max(start1, start2) <= min(end1, end2)

def is_duplicate_submission(data):
    with open(SUBMISSIONS_FILE, 'r') as file:
        submissions_data = json.load(file)["submissions"]
        for submission in submissions_data:
            if submission.get("status") == "Cancelled":
                continue  # Skip canceled bookings
            if (submission["server"] == data["server"] and
                any(scheme in submission["schemeType"] for scheme in data["schemeType"]) and
                bool(set(submission["timeSlot"]).intersection(set(data["timeSlot"]))) and
                is_date_range_overlap(
                    submission["dateRange"]["start"],
                    submission["dateRange"]["end"],
                    data["dateRange"]["start"],
                    data["dateRange"]["end"]
                ) and
                submission.get("openSlot") == data.get("openSlot")): 
                return True, submission["bookingID"]
    return False, None

def is_open_slot_duplicate(data):
    if not data.get("openSlot"):
        return False, None
    with open(SUBMISSIONS_FILE, 'r') as file:
        submissions_data = json.load(file)["submissions"]
        for submission in submissions_data:
            if submission.get("status") == "Cancelled":
                continue  # Skip canceled bookings
            if (submission.get("openSlot") and
                is_date_range_overlap(
                    submission["dateRange"]["start"],
                    submission["dateRange"]["end"],
                    data["dateRange"]["start"],
                    data["dateRange"]["end"]
                )):
                return True, submission["bookingID"]
    return False, None

import logging

logger = logging.getLogger(__name__)

def save_submission(request):
    ensure_files_exist()
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # 🔽 Print the incoming data for debugging
            logger.info("📦 Incoming Frontend Data: %s", json.dumps(data, indent=4))
            
            # Check for open slot duplicate booking if open slot is true
            is_open_slot, open_slot_booking_id = is_open_slot_duplicate(data)
            if is_open_slot:
                return JsonResponse({"error": f"Open slot booking already exists (Booking ID: {open_slot_booking_id})"}, status=409)

            # Check for duplicate submission for openSlot = False
            is_duplicate, booking_id = is_duplicate_submission(data)
            if is_duplicate:
                return JsonResponse({"error": f"Duplicate booking found (Booking ID: {booking_id})"}, status=409)

            # ✅ Inject all servers if openSlot is true
            if data.get("openSlot"):
                if os.path.exists(CONFIG_PATH):
                    with open(CONFIG_PATH, 'r') as f:
                        config = json.load(f)
                        data["server"] = config.get("servers", [])

            # Get the next booking ID
            last_booking_id = read_counter()
            new_booking_id = last_booking_id + 1
            write_counter(new_booking_id)

            data["bookingID"] = new_booking_id
            data["status"] = "Booked"

            # Append the submission to the submissions file
            with open(SUBMISSIONS_FILE, 'r+') as file:
                submissions_data = json.load(file)
                submissions_data['submissions'].append(data)
                file.seek(0)
                json.dump(submissions_data, file, indent=4)

            return JsonResponse({
                "message": "Submission saved successfully",
                "bookingID": new_booking_id
            }, status=200)

        except Exception as e:
            logger.error("Error saving submission: %s", str(e), exc_info=True)
            return JsonResponse({"error": str(e)}, status=500)

    return HttpResponse(status=405)

# NEW VIEW: Serve the submissions for the calendar
def get_submissions(request):
    if request.method == 'GET':
        try:
            with open(SUBMISSIONS_FILE, 'r') as file:
                submissions_data = json.load(file)
                return JsonResponse(submissions_data, safe=False)
        except FileNotFoundError:
            return JsonResponse({"submissions": []})

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Or use CSRF token in the fetch call!
def cancel_booking(request, booking_id):
    ensure_files_exist()
    if request.method == 'POST':
        try:
            booking_id = int(booking_id)
            with open(SUBMISSIONS_FILE, 'r+') as file:
                data = json.load(file)
                updated = False
                for submission in data["submissions"]:
                    if submission["bookingID"] == booking_id:
                        submission["status"] = "Cancelled"
                        updated = True
                        break
                if not updated:
                    return JsonResponse({"error": "Booking not found"}, status=404)

                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()

            return JsonResponse({"message": "Booking cancelled successfully"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)

