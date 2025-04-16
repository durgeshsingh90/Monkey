from django.http import JsonResponse
from django.shortcuts import render

def string_to_hex(s):
    return s.encode('utf-8').hex()

def hex_to_string(hex_str):
    try:
        return bytes.fromhex(hex_str).decode('utf-8')
    except Exception:
        return "[Invalid hex string]"

def index(request):
    if request.method == "POST":
        user_input = request.POST.get("user_input", "")
        inputs = user_input.splitlines()
        results = []

        for input_line in inputs:
            input_line = input_line.strip()

            if len(input_line) == 12 and input_line.isdigit():
                hex_output = string_to_hex(input_line)
                results.append(f"{input_line} OR {hex_output}")
            elif len(input_line) == 24 and all(c in "0123456789abcdefABCDEF" for c in input_line):
                original_string = hex_to_string(input_line)
                results.append(f"{input_line} OR {original_string}")
            else:
                results.append(f"Invalid input length or format for '{input_line}'")

        result = "\n".join(results)

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"result": result})

        return render(request, 'splunkrrn/index.html', {'result': result})

    return render(request, 'splunkrrn/index.html', {'result': ""})
