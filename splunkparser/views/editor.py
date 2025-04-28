from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
import json
import os
from django.conf import settings
import logging

logger = logging.getLogger('splunkparser')

settings_file_path = os.path.join(settings.MEDIA_ROOT, 'splunkparser', 'settings.json')

def editor_page(request):
    logger.info("Rendering the main editor page.")

    # Check and create default settings.json if not present
    if not os.path.exists(settings_file_path):
        logger.warning(f"settings.json not found at {settings_file_path}. Creating default config.")
        default_config = {
  "configs": [
    {
      "scheme": "Visa",
      "cards": [
        {
          "DE002": "4176662220010034",
          "DE014": "3112",
          "DE035": "4176662220010034=311220111523358",
          "DE048": "012",
          "DE052": "94AE5DDC44E9E0D2",
          "DE053": "3030313030320000000000000000000000000000000000000000000000000000000000000000",
          "cardName": "Visa Online PIN CT"
        }
      ]
    },
    {
      "scheme": "MasterCard",
      "cards": [
        {
          "DE002": "5357610050503022",
          "DE014": "2612",
          "DE035": "5357610050503022=261222677777777",
          "DE048": "978",
          "DE052": "7777C7C7CC7CC77C",
          "DE053": "3030313030320000000000000000000000000000000000000000000000000000000000000000",
          "cardName": "EMV Online Pin"
        }
      ]
    },
    {
      "scheme": "Diners",
      "cards": [
        {
          "DE002": "36070500100715",
          "DE014": "4912",
          "DE035": "36070500100715=4912201180400042600000",
          "DE048": "123",
          "DE052": "C0297DC996D22675",
          "DE053": "3030313030320000000000000000000000000000000000000000000000000000000000000000",
          "cardName": "Diners Online Pin CT"
        }
      ]
    }
  ]
}

        os.makedirs(os.path.dirname(settings_file_path), exist_ok=True)
        with open(settings_file_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        logger.info("Default settings.json created successfully.")

    return render(request, 'splunkparser/index.html')


def config_editor_page(request):
    logger.info("Rendering the settings editor page.")
    return render(request, 'splunkparser/settings.html')

def get_settings(request):
    if request.method == 'GET':
        try:
            with open(settings_file_path, 'r') as f:
                data = json.load(f)
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': f'Failed to load settings.json: {str(e)}'}, status=500)
    return HttpResponseNotAllowed(['GET'])

@csrf_exempt
def save_settings(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            with open(settings_file_path, 'w') as f:
                json.dump(data, f, indent=4)

            return JsonResponse({'status': 'success', 'message': 'Settings saved successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return HttpResponseBadRequest('Only POST method is allowed')
