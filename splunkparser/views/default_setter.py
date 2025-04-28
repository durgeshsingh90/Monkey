from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import os
from django.conf import settings
import logging
import random

logger = logging.getLogger('splunkparser')

settings_file_path = os.path.join(settings.MEDIA_ROOT, 'splunkparser', 'settings.json')
output_file_path = os.path.join(settings.MEDIA_ROOT, 'splunkparser', 'output.json')

@csrf_exempt
def set_default_values(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

    try:
        # ✅ Get present fields from frontend payload
        body = json.loads(request.body)
        present_fields = body.get('present_fields', [])
        logger.info(f"Present DEs from editor: {present_fields}")

        # ✅ Load parsed ISO8583 output from output.json
        with open(output_file_path, 'r') as f:
            output_data = json.load(f)

        data_elements = output_data.get('data_elements', {})
        if not data_elements:
            return JsonResponse({'status': 'error', 'message': 'No parsed data found in output.json'})

        # ✅ Load settings.json (default config)
        with open(settings_file_path, 'r') as f:
            settings_data = json.load(f)

        # ✅ Get DE002 to extract BIN prefix
        de002_value = data_elements.get('DE002', '')
        if not de002_value:
            return JsonResponse({'status': 'error', 'message': 'DE002 not found in output.json'})

        logger.info(f"Original DE002: {de002_value}")
        prefix_to_try = de002_value[:4]

        match_found = False
        default_card = None
        scheme_name = None

        # ✅ Prefix-matching logic
        while len(prefix_to_try) > 0:
            matching_cards = []
            for scheme in settings_data.get('configs', []):
                for card in scheme.get('cards', []):
                    card_de002 = card.get('DE002', '')
                    if card_de002.startswith(prefix_to_try):
                        matching_cards.append({'scheme': scheme.get('scheme'), 'card': card})

            if matching_cards:
                selected = random.choice(matching_cards)
                scheme_name = selected['scheme']
                default_card = selected['card']
                logger.info(f"Match found for prefix {prefix_to_try} in scheme {scheme_name}, card: {default_card.get('cardName')}")
                match_found = True
                break

            prefix_to_try = prefix_to_try[:-1]

        if not match_found or not default_card:
            return JsonResponse({'status': 'error', 'message': f'No matching default card found for prefix {de002_value[:4]}'})

        # ✅ Apply defaults only for DEs that are:
        # - present in the parsed log
        # - included in the editor content's DEs
        for field in ['DE002', 'DE014', 'DE035', 'DE048', 'DE052', 'DE053']:
            if field in data_elements and field in present_fields:
                current_value = data_elements.get(field, '')
                if '*' in current_value or current_value.strip('*') == '':
                    replacement = default_card.get(field)
                    if replacement is not None:
                        logger.info(f"Replacing masked {field} with default value: {replacement}")
                        data_elements[field] = replacement

        # ✅ Save updated data back to output.json
        with open(output_file_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        return JsonResponse({
            'status': 'success',
            'message': 'Default values applied',
            'result': output_data,
            'scheme': scheme_name,
            'cardName': default_card.get('cardName'),
            'prefix_used': prefix_to_try
        })

    except Exception as e:
        logger.exception("Error applying default values")
        return JsonResponse({'status': 'error', 'message': str(e)})
