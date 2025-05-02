import os
import json
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .iso_converter import parse_iso8583_message, build_iso8583_hex
from django.conf import settings
from django.http import JsonResponse

# Load schema from the correct media path
SCHEMA_PATH = os.path.join(settings.MEDIA_ROOT, 'schemas', 'omnipay_schema.json')
with open(SCHEMA_PATH, 'r') as f:
    ISO_SCHEMA = json.load(f)

def index(request):
    return render(request, 'hex2iso/index.html')

@csrf_exempt
def convert(request):
    try:
        body = json.loads(request.body)
        print("🚀 Received request:")
        print("   ➤ direction:", body.get('direction'))
        print("   ➤ input:", body.get('input'))
        print("   ➤ schema:", body.get('schema'))

        direction = body.get('direction')
        input_data = body.get('input', '').strip()
        schema_name = body.get('schema', '').strip()

        if not schema_name or not schema_name.endswith('_schema.json'):
            print("❌ Missing or invalid schema name")
            return HttpResponse("Invalid schema name", status=400)

        schema_path = os.path.join(SCHEMA_FOLDER, schema_name)
        if not os.path.isfile(schema_path):
            print("❌ Schema file not found:", schema_path)
            return HttpResponse("Schema not found", status=404)

        with open(schema_path) as f:
            schema = json.load(f)

        if direction == 'hex_to_json':
            result = parse_iso8583_message(input_data, schema)
            return JsonResponse(result, json_dumps_params={'indent': 2})

        elif direction == 'json_to_hex':
            try:
                json_obj = json.loads(input_data)
            except json.JSONDecodeError:
                print("❌ Invalid JSON")
                return HttpResponse("Invalid JSON", status=400)

            hex_str = build_iso8583_hex(json_obj, schema)
            return HttpResponse(hex_str)

        print("❌ Invalid direction:", direction)
        return HttpResponse("Invalid direction", status=400)

    except Exception as e:
        print("🔥 Error:", str(e))
        return HttpResponse(f"Error: {str(e)}", status=500)


SCHEMA_FOLDER = os.path.join(settings.MEDIA_ROOT, 'schemas')

def list_schemas(request):
    schema_files = [
        fname for fname in os.listdir(SCHEMA_FOLDER)
        if fname.endswith('_schema.json')
    ]
    return JsonResponse(schema_files, safe=False)
