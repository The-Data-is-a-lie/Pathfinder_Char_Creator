# Pin the absolute Backend dir on sys.path so sibling imports (start_py/main_test/utils) resolve
# regardless of where the server is launched from. Must run before importing main_test. This used to
# be followed by os.chdir(repo_root) to make root-relative data paths work; those are now anchored to
# __file__ via utils.paths.repo_path, so the server no longer changes the process working directory.
import os, sys
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# External imports
from flask import Flask, render_template, request, jsonify, session, abort
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from datetime import timedelta
import os

# Custom function imports
from start_py import create_app
from main_test import generate_random_char, GENERATOR_VERSION

# Load environment variables
load_dotenv()
# Redis powers rate-limiting + server-side sessions ONLY when REDIS_URL is set (local dev, or a
# provisioned Redis instance). When it is not set, fall back to in-process memory rate-limiting and
# filesystem sessions so the app runs without a Redis server -- e.g. the Render deployment, which has
# none. (Previously this defaulted to redis://localhost:6379, so every request 500'd on Render with
# ConnectionRefusedError from flask-limiter.)
# Redis selection: try each candidate in order, use the first that actually responds.
# Local dev -> your local server; if it's not running but a global/cloud URL is set, use that;
# if none respond (e.g. Render, which has no Redis), fall through to None -> memory/filesystem.
_REDIS_CANDIDATES = [
    os.getenv('REDIS_LOCAL_URL', 'redis://localhost:6379/0'),  # local server (preferred in dev)
    os.getenv('REDIS_URL'),                                     # global / cloud (unset on Render)
]

def _resolve_redis_url():
    for url in _REDIS_CANDIDATES:
        if not url:
            continue
        try:
            Redis.from_url(url, socket_connect_timeout=0.5).ping()
            print(f"  Redis: using {url.split('@')[-1]}")  # host only, no password in logs
            return url
        except Exception as e:
            print(f"  Redis: {url.split('@')[-1]} unreachable ({e.__class__.__name__})")
    print("  Redis: none reachable -> memory/filesystem fallback")
    return None

redis_url = _resolve_redis_url()

app = create_app()
app.config['JSON_SORT_KEYS'] = False  # Disable sorting of JSON keys
app.json.sort_keys = False  # Disable sorting of JSON keys

# Initialize Flask-Limiter (Redis-backed when REDIS_URL is set, else in-process memory storage)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "500 per hour", "60 per minute"],
    storage_uri=redis_url or "memory://"  # memory:// keeps the app up without Redis (limits are per-worker)
)

# Flask Configuration -- Redis-backed sessions when available, else server-side filesystem sessions.
if redis_url:
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = Redis.from_url(redis_url)
else:
    app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SESSION_PERMANENT'] = False
# Needs enough time or multiple workers break
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=60)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

Session(app)

# allowing many routes:
# For allowing all origins
CORS(app, 
     supports_credentials=True, 
    origins=["*"],  # Allow all origins [works]

    #  origins=["http://192.168.1.164:30000", 
    #          "http://72.180.6.78:30000", 
    #          "http://localhost:3000",
    #          "http://localhost:30000",
    #          "http://127.0.0.1:30000",
    #          "http://127.0.0.1:3000",
    #          "http://localhost:4000",
    #          "http://localhost:5000",
    #          "http://localhost:6000",
    #          "http://localhost:7000",
    #          "http://localhost:8000",
    #          "http://localhost:9000"], 
             
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"], 
     expose_headers=["Content-Type", "Authorization"] 
     )

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/sheet', methods=['GET'])
@limiter.exempt
def sheet():
    # Read-only pf1-style character sheet; renders client-side from the JSON that
    # POST /update_character_data returns (static/scripts/sheet.js).
    return render_template('sheet.html')

@app.route('/backstory-stats', methods=['GET'])
@limiter.exempt
def backstory_stats():
    # Running tally of backstory-API usage: total requests, and the ollama-vs-template split.
    # See utils/usage_counter.py. Persists per-container (resets on Render redeploys).
    from utils.usage_counter import snapshot
    return jsonify(snapshot())

def process_input_values(input_values, spheres_flag="N"):
    try:
        if len(input_values) < 19:
            raise IndexError("Not enough elements in input_values")

        # Optional 20th input: the "use backstory API" toggle (the button that decides whether the
        # Ollama backstory call runs at all). Older clients send 19 fields -> default to "Y" (on).
        # Trim to the core 19 so the integer conversion + unpack below stay aligned.
        use_backstory_api = input_values[19] if len(input_values) >= 20 else "Y"
        # Optional 21st input: backstory focus (comma/space-separated aspects to emphasize, e.g.
        # "combat, faith"). Older clients omit it -> None -> balanced/profession default.
        backstory_focus = input_values[20] if len(input_values) >= 21 else None
        input_values = input_values[:19]

        # Convert specific elements to integers
        for i in range(-5, 0):
        # for i in [14, 15, 16, 17, 18]:
            value = input_values[i]
            if value is not None and value != "":
                input_values[i] = int(value)
            elif i == -1:
                # Blank gold stays non-int so assign_gold falls through to the
                # Paizo wealth-by-level default instead of literal 0 gp.
                input_values[i] = ""
            else:
                input_values[i] = 0

        # Unpack input_values
        create_new_char, userInput_region, userInput_race, class_choice, chosen_BAB, chosen_caster_level, multi_class, alignment_input, deity_choice, userInput_gender, truly_random_feats, inherents, modded_char_sheet, homebrew_feat_amount, num_dice, num_sides, high_level, low_level, gold_num = input_values
        session['character_data'] = generate_random_char(
        create_new_char, userInput_region, userInput_race, class_choice, chosen_BAB, chosen_caster_level, multi_class, alignment_input, deity_choice, userInput_gender, truly_random_feats, inherents, modded_char_sheet, homebrew_feat_amount, num_dice, num_sides, high_level, low_level, gold_num, use_backstory_api, spheres_flag, backstory_focus
        )
        return session['character_data']

    except ValueError as ve:
        return {"error": str(ve)}
    except IndexError as ie:
        return {"error": str(ie)}
    except Exception as e:
        return {"error": str(e)}

@app.route('/update_character_data', methods=['GET', 'POST'])
@limiter.limit("60 per minute")
def update_character_data():
    data = request.json
    # Spheres opt-in is read by NAME (not positionally) and removed so the fixed 19-field positional
    # unpack below stays aligned regardless of where the client puts it / whether older clients send it.
    spheres_flag = (data.pop('spheres_of_power', 'n') or 'n')
    non_input_data = []
    # Calculate last 5 keys dynamically
    items = list(data.items())
    last_5_keys = set(key for key, _ in items[-5:])

    for key, value in data.items():
        if key in last_5_keys:
            try:
                value = int(value)
            except:
                value = value
        else:
            value = value.strip()
        non_input_data.append(value)

    results = process_input_values(non_input_data, spheres_flag)
    session['character_data'] = results

    # Print raw data to terminal for debugging
    return jsonify(session['character_data'])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    # Loud freshness banner: if a regenerated character looks stale, confirm this line shows the latest
    # GENERATOR_VERSION -- if not, THIS process wasn't restarted after the code change.
    print("=" * 80)
    print(f"  Pathfinder character generator backend  |  generator {GENERATOR_VERSION}  |  port {port}")
    print("=" * 80)
    # use_reloader=False: the project's .venv redirects to the base C:\Python310 interpreter, which
    # makes Werkzeug's debug auto-reloader spawn a runaway cascade of nested processes that fight over
    # the port and serve stale code. Keep the debugger, drop the reloader; restart manually after edits.
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)  # debug when production = dangerous