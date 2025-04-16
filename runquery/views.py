from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json

# Import your Oracle query executor
from .scripts.db_connection import execute_multiple_query_sets


# View to render the HTML page (index.html)
def query_page(request):
    return render(request, "runquery/index.html")  # Make sure this file exists at templates/runquery/index.html


# View to return available Oracle DB aliases
def get_available_oracle_databases(request):
    oracle_dbs = []
    for alias, config in settings.DATABASES.items():
        if config.get("ENGINE") == "django.db.backends.oracle":
            oracle_dbs.append(alias)
    return JsonResponse({"databases": oracle_dbs})

from pathlib import Path
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from .scripts.db_connection import execute_multiple_query_sets
import json


@csrf_exempt
def execute_oracle_queries(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            query_sets = data.get("query_sets", [])
            script_name = data.get("script_name", "user_triggered_script")

            if not query_sets:
                return JsonResponse({"error": "No queries provided"}, status=400)

            results = execute_multiple_query_sets(query_sets, script_name)

            for result in results:
                query = result.get("query", "").lower()
                if "from" in query:
                    try:
                        # Extract table name
                        from_index = query.find("from") + 5
                        table_part = query[from_index:].split()[0]
                        table_base = table_part.split('.')[-1]
                        table_slug = slugify(table_base)

                        # ✅ Correct location: Monkey/media/runquery/<db>/<table>.json
                        print("Resolved save_dir =", save_dir.resolve())

                        save_dir = Path(settings.MEDIA_ROOT) / "runquery" / script_name
                        save_dir.mkdir(parents=True, exist_ok=True)

                        save_path = save_dir / f"{table_slug}.json"
                        with open(save_path, "w", encoding="utf-8") as f:
                            json.dump(result, f, indent=2)

                        print(f"✅ Saved: {save_path}")

                    except Exception as parse_err:
                        print("⚠️ Failed to extract table name:", parse_err)

            return JsonResponse({"results": results}, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Only POST allowed"}, status=405)
