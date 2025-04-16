from django.shortcuts import render

# Import all reversal scripts
from .scripts.gen400 import create_reversal_0400_message as gen_400_reversal
from .scripts.gen401 import create_reversal_0401_message as gen_401_reversal
from .scripts.gen420 import create_reversal_0420_message as gen_420_reversal
from .scripts.refund import create_refund_message as gen_refund

# Mapping action names to functions
REVERSAL_FUNCTIONS = {
    "400 Reversal": gen_400_reversal,
    "401 Reversal": gen_401_reversal,
    "420 Reversal": gen_420_reversal,
    "Refund": gen_refund
}

def reversal_generator(request):
    return render(request, 'gen_reversals/reversals.html')
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def generate_reversal(request, action):
    if request.method == 'POST':
        try:
            if action not in REVERSAL_FUNCTIONS:
                return JsonResponse({'error': 'Invalid action'}, status=400)

            data = json.loads(request.body)
            reversal_function = REVERSAL_FUNCTIONS[action]

            reversal_results = []
            for group in data:
                auth_request = group[0]
                auth_response = group[1] if len(group) > 1 else {}
                reversal_message = reversal_function(auth_request, auth_response)
                reversal_results.append(reversal_message)

            return JsonResponse(reversal_results, safe=False, json_dumps_params={'indent': 4})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
