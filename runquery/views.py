from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from pathlib import Path
from django.utils.text import slugify
from .db_connection import execute_multiple_query_sets, get_or_load_table_metadata, CustomJSONEncoder
import json

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

@csrf_exempt
def execute_oracle_queries(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            query_sets = data.get("query_sets", [])
            script_name = data.get("script_name", "user_triggered_script")

            if not query_sets:
                return JsonResponse({"error": "No queries provided"}, status=400)

            # Build the expected format: {"db_key": [queries]}
            query_sets_dict = {script_name: query_sets[0]}  # assuming only one db per request
            # Convert list of queries to dict format expected by execute_multiple_query_sets
            query_sets_dict = {script_name: query_sets[0]}  # assuming only 1 DB alias selected
            results = execute_multiple_query_sets(query_sets_dict, script_name)
            save_dir = Path(settings.MEDIA_ROOT) / "runquery" / script_name
            save_dir.mkdir(parents=True, exist_ok=True)


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



                        save_path = save_dir / f"{table_slug}.json"
                        with open(save_path, "w", encoding="utf-8") as f:
                            json.dump(result, f, cls=CustomJSONEncoder, indent=2)


                        print(f"✅ Saved: {save_path}")

                    except Exception as parse_err:
                        print("⚠️ Failed to extract table name:", parse_err)

            return JsonResponse(json.loads(json.dumps({"results": results}, cls=CustomJSONEncoder)), safe=False)


        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"message": "Only POST allowed"}, status=405)

from django.http import JsonResponse
from django.conf import settings
from pathlib import Path

# Assuming you have the read_pinned_tables and write_pinned_tables functions

def get_table_structure(request):
    db_key = request.GET.get("db", "uat_ist")
    refresh = request.GET.get("refresh") == "1"
    
    pinned_tables = read_pinned_tables()
    data = get_or_load_table_metadata(db_key, refresh=refresh)
    
    all_tables = data.get("tables", {})
    
    # Separate pinned and unpinned tables, and sort them
    pinned_tables_dict = {table: all_tables[table] for table in pinned_tables if table in all_tables}
    unpinned_tables_dict = {table: all_tables[table] for table in sorted(all_tables) if table not in pinned_tables}
    
    # Combine pinned and unpinned tables, ensuring pinned are at the top
    data["tables"] = {**pinned_tables_dict, **unpinned_tables_dict}
    table_count = len(data["tables"])

    return JsonResponse({"tables": data["tables"], "count": table_count})


import json
from pathlib import Path

PINNED_TABLES_FILE = Path(settings.MEDIA_ROOT) / "runquery" / "pinned_tables.json"

def read_pinned_tables():
    if PINNED_TABLES_FILE.exists():
        with open(PINNED_TABLES_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def write_pinned_tables(pinned_tables):
    with open(PINNED_TABLES_FILE, 'w') as f:
        json.dump(pinned_tables, f, indent=2)

@csrf_exempt
def pin_table(request):
    if request.method == "POST":
        table = json.loads(request.body).get("table")
        pinned_tables = read_pinned_tables()
        if table not in pinned_tables:
            pinned_tables.append(table)
            pinned_tables.sort()
            write_pinned_tables(pinned_tables)
        return JsonResponse({"status": "success"})

@csrf_exempt
def unpin_table(request):
    if request.method == "POST":
        table = json.loads(request.body).get("table")
        pinned_tables = read_pinned_tables()
        if table in pinned_tables:
            pinned_tables.remove(table)
            write_pinned_tables(pinned_tables)
        return JsonResponse({"status": "success"})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
from pathlib import Path
from datetime import datetime

@csrf_exempt
def save_history(request):
    try:
        data = json.loads(request.body)
        history_file = Path(settings.MEDIA_ROOT) / "runquery" / "history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)

        history = []
        if history_file.exists():
            with open(history_file, "r") as f:
                history = json.load(f)

        history.append(data)
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)

        return JsonResponse({"status": "saved"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def view_history(request):
    return render(request, "runquery/history.html")

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from pathlib import Path
import json

SCRIPTS_DIR = Path(settings.MEDIA_ROOT) / "runquery" / "scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

@csrf_exempt
def save_script(request):
    try:
        data = json.loads(request.body)
        name = data["name"]
        db = data["db"]
        query = data["query"]
        scripts_dir = Path(settings.MEDIA_ROOT) / "runquery" / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        script_file = scripts_dir / f"{db}.json"

        scripts = []
        if script_file.exists():
            scripts = json.loads(script_file.read_text())

        # Replace if already exists
        scripts = [s for s in scripts if s["name"] != name]
        scripts.append({"name": name, "query": query})

        script_file.write_text(json.dumps(scripts, indent=2))
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})

def list_scripts(request):
    db = request.GET.get("db", "local_oracle")  # default fallback
    scripts_file = Path(settings.MEDIA_ROOT) / "runquery" / "scripts" / f"{db}.json"

    if scripts_file.exists():
        try:
            with open(scripts_file, "r") as f:
                scripts = json.load(f)
            return JsonResponse({"scripts": scripts})
        except Exception as e:
            return JsonResponse({"scripts": [], "error": str(e)})
    return JsonResponse({"scripts": []})

def load_script(request):
    db = request.GET.get("db")
    name = request.GET.get("name")
    script_file = Path(settings.MEDIA_ROOT) / "runquery" / "scripts" / f"{db}.json"
    if script_file.exists():
        scripts = json.loads(script_file.read_text())
        for s in scripts:
            if s["name"] == name:
                return JsonResponse({"query": s["query"]})
    return JsonResponse({"error": "Script not found"})
