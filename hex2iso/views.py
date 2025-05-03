from django.shortcuts import render
from django.http import JsonResponse
from .hex2iso import parse_iso8583
from .iso2hex import json_to_hex

def index(request):
    return render(request, 'hex2iso/index.html')

def parse_iso_view(request):
    if request.method == 'POST':
        hex_data = request.POST.get('hex_data')
        schema_file = request.POST.get('schema', 'omnipay_schema.json')
        try:
            parsed = parse_iso8583(hex_data, schema_file)
            return JsonResponse(parsed)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .hex2iso import parse_iso8583  # your parser

def list_schemas(request):
    schema_dir = os.path.join(settings.MEDIA_ROOT, 'schemas')
    schemas = [f for f in os.listdir(schema_dir) if f.endswith('.json')]
    return JsonResponse(schemas, safe=False)

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import os
from .hex2iso import parse_iso8583

@csrf_exempt
def convert_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            direction = data.get('direction')
            schema_filename = data.get('schema')
            input_str = data.get('input', '')

            if not direction or not schema_filename:
                return JsonResponse({'error': 'Missing direction or schema'}, status=400)

            schema_path = os.path.join(settings.MEDIA_ROOT, 'schemas', schema_filename)

            if not os.path.exists(schema_path):
                return JsonResponse({'error': f'Schema not found: {schema_filename}'}, status=404)
            if not input_str.strip():
                return JsonResponse({}, safe=False)  # return empty result for blank input

            if direction == 'hex_to_json':
                result = parse_iso8583(input_str, schema_path)
                return JsonResponse(result, safe=False)

            elif direction == 'json_to_hex':
                result = json_to_hex(input_str, schema_path)
                return JsonResponse({}, safe=False)  # Send empty result instead of error


            else:
                return JsonResponse({'error': 'Invalid direction'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid method'}, status=405)
