# Pin the absolute Backend dir on sys.path so sibling imports (start_py/main_test/utils) resolve
# regardless of where the server is launched from. Must run before importing main_test. This used to
# be followed by os.chdir(repo_root) to make root-relative data paths work; those are now anchored to
# __file__ via utils.paths.repo_path, so the server no longer changes the process working directory.
import os, sys
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# External imports
from flask import Flask, render_template, request, jsonify, abort, Response, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
import os

# Custom function imports
from start_py import create_app
from main_test import generate_random_char, GENERATOR_VERSION

# generate_random_char seeds the process-global `random` (and numpy) module, so only one generation
# may run at a time within a process or their draws interleave -- see the comment at the call site.
import threading
_GENERATION_LOCK = threading.Lock()

# Load environment variables
load_dotenv()
# Redis backs rate-limiting ONLY. It used to back server-side sessions too; those are gone -- see
# the note above update_character_data. Without Redis the limiter falls back to in-process memory
# storage so the app still runs (this defaulted to redis://localhost:6379 once, which made every
# request 500 on Render with ConnectionRefusedError from flask-limiter).
#
# `memory://` counts per WORKER, so with gunicorn -w 4 the declared 60/minute is really 240/minute
# across the pool. That is the reason to provision a Redis instance, not sessions.
#
# THE REDIS INSTANCE MUST BE IN THE SAME REGION AS THE SERVICE. This is not a preference.
# flask-limiter checks each configured limit separately and `RedisStorage.incr` is one Lua call per
# limit, so the three default limits below cost THREE sequential round trips on every request. Same
# region (Render Oregon <-> Redis Cloud us-west-2) that is ~3 ms and invisible. Cross-country
# (Oregon <-> us-east-1) it is ~200 ms, against a generation that takes 85-285 ms -- i.e. pointing
# REDIS_URL at a far-away instance can double or triple response time to enforce a limit this
# service never approaches. If the only Redis available is in another region, leave REDIS_URL unset
# and take the per-worker limits; that is the better trade.
#
# Note the service's region is fixed at creation on Render, and its URL is hardcoded as the default
# in the FoundryVTT module (`module.js`, `button.js`) -- so the Redis moves to match the service,
# never the other way around.
#
# Redis selection: try each candidate in order, use the first that actually responds.
# Local dev -> your local server; if it's not running but a global/cloud URL is set, use that;
# if none respond, fall through to None -> memory storage.
# On Render set REDIS_LOCAL_URL to an EMPTY string: nothing listens on localhost:6379 there, so the
# default value below costs a 0.5 s connect timeout on every cold start before falling through.
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
    print("  Redis: none reachable -> in-process memory rate-limiting (limits count PER WORKER)")
    return None

redis_url = _resolve_redis_url()

app = create_app()
app.config['JSON_SORT_KEYS'] = False  # Disable sorting of JSON keys
app.json.sort_keys = False  # Disable sorting of JSON keys

# Initialize Flask-Limiter (Redis-backed when a Redis URL resolves, else in-process memory storage)
#
# swallow_errors=True is NOT optional once a real Redis is configured, and the default is False.
# The URL above is resolved ONCE, at import, by a single ping. If Redis is reachable then and dies
# later -- a managed instance restarting, a network blip, a free tier doing maintenance -- every
# rate-limited request would raise out of the storage layer, and `/update_character_data` would
# return 500 until someone redeployed. The generator would be fine; the limiter would be taking the
# API down with it.
#
# With this, a storage failure degrades to "limits stop being counted" and characters keep
# generating. That is the right trade for this service: the rate limit protects a free instance's
# CPU hours, so losing it briefly costs far less than refusing every request.
#
# in_memory_fallback_enabled goes further -- it falls back to per-process counting while Redis is
# down, so the limit keeps applying (loosely) instead of lapsing entirely.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1000 per day", "500 per hour", "60 per minute"],
    storage_uri=redis_url or "memory://",  # memory:// keeps the app up without Redis (limits are per-worker)
    swallow_errors=True,
    in_memory_fallback_enabled=True,
)

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
    # A signpost, not an application. This backend is a JSON API; the character sheet that used to
    # live at /sheet was retired in favour of the standalone Pathfinder-Character-Sheet front end.
    # The route stays so the deployment's root answers rather than 404s.
    return render_template('index.html')

@app.route('/license', methods=['GET'])
@limiter.exempt
def license_text():
    # Open Game License section 10: a copy of the licence must accompany every distribution of Open
    # Game Content, and serving generated mechanics over HTTP is Distribution. Payloads point here
    # (`license_url`) instead of embedding ~9 KB of legal text in every character.
    #
    # Served as text/plain rather than rendered: this is a legal document that must be reproducible
    # byte for byte, and HTML rendering would collapse the whitespace section 15 depends on.
    # LICENSE-OGL.txt is generated -- edit Backend/scripts/build_ogl_license.py, not the file.
    from utils.paths import repo_path
    licence = repo_path('LICENSE-OGL.txt')
    if not licence.exists():
        # Serving Open Game Content while unable to produce the licence is the one failure mode
        # section 10 does not tolerate, so this is a hard 500 rather than an empty body.
        abort(500, description="LICENSE-OGL.txt is missing; run Backend/scripts/build_ogl_license.py")
    return Response(licence.read_text(encoding='utf-8'), mimetype='text/plain; charset=utf-8')

@app.route('/backstory-stats', methods=['GET'])
@limiter.exempt
def backstory_stats():
    # Running tally of backstory-API usage: total requests, and the ollama-vs-template split.
    # See utils/usage_counter.py. Persists per-container (resets on Render redeploys).
    from utils.usage_counter import snapshot
    return jsonify(snapshot())

def process_input_values(input_values, spheres_flag="N", seed=None, professions_flag="Y", trainers_flag="Y",
                         misc_homebrew_rules="Y", luck_direction=None, optimize=None,
                         house_rules=None, mythic=None):
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
        # Serialized: generate_random_char seeds the PROCESS-GLOBAL random (and numpy) module, so two
        # generations running at once in one process interleave draws -- the second request would
        # perturb the first, and a replayed seed would not reproduce. gunicorn's sync workers already
        # serialize (the 4 worker PROCESSES still run in parallel), but Flask's dev server is
        # threaded, which is exactly where you would be replaying a seed to debug a character.
        # Generation is ~80ms against a 31s cold start, so the lock costs nothing that matters.
        with _GENERATION_LOCK:
            return generate_random_char(
            create_new_char, userInput_region, userInput_race, class_choice, chosen_BAB, chosen_caster_level, multi_class, alignment_input, deity_choice, userInput_gender, truly_random_feats, inherents, modded_char_sheet, homebrew_feat_amount, num_dice, num_sides, high_level, low_level, gold_num, use_backstory_api, spheres_flag, backstory_focus,
            seed, professions_flag, trainers_flag, misc_homebrew_rules, luck_direction, optimize,
            house_rules, mythic
            )

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
    # Optional replay handle, also read by NAME. Pass back the `generation_seed` from a previous
    # response to reproduce that character exactly. MUST be popped BEFORE `items` is built: last_5_keys
    # is derived from items[-5:], so a trailing 'seed' key left in the dict would displace one of the
    # five numeric fields and break the int conversion below. Absent -> None -> a fresh random seed.
    seed = data.pop('seed', None)
    # Profession / trainer opt-OUTS, read by NAME for the same reason as spheres_flag and seed, and
    # for the same reason popped BEFORE `items` is built. Default 'y' = today's behaviour, so the
    # Foundry module and any client that never sends them keep getting professions and trainers.
    professions_flag = (data.pop('professions', 'y') or 'y')
    trainers_flag = (data.pop('trainers', 'y') or 'y')
    # The house-rule catch-all, read by NAME for exactly the same reason and popped before `items` is
    # built. It gates the 2->4 skill-rank floor, the diminishing flaw-feat grant and -- as of the
    # inherent-luck work -- the whole luck subsystem. It was internal-only until luck needed to be
    # switchable from the client; default 'y' keeps today's behaviour for every existing consumer.
    misc_homebrew_rules = (data.pop('misc_homebrew_rules', 'y') or 'y')
    # DEBUG input, read by NAME and popped before `items` like the flags above. 'buy' or 'sell'
    # forces the luck branch and guarantees a stake; absent -> None -> the ordinary weighted rolls.
    # It exists so the negative side can be exercised without hand-editing LUCK_PROPENSITY /
    # LUCK_SELL_SHARE in luck.py -- constants that then had to be remembered before shipping.
    luck_direction = data.pop('luck_direction', None) or None
    # Optimized mode (spec 15), read by NAME and popped before `items` like the flags above.
    # `true`/`y` turns it on with the role drawn from the class map; a role name forces that role;
    # absent -> None -> random mode, byte-identical to today.
    optimize = data.pop('optimize', None)
    # Full house-rules optimization (spec 15, V4 wall pass), read by NAME and popped before
    # `items` like the flags above. Only meaningful alongside `optimize`: `true`/`y` makes the
    # optimizer build the house AC kickers (Strength of a Warrior, the defensive-sphere package,
    # sword-and-board TWD, ...) on top of the standard optimized build; absent -> None -> the
    # standard optimizer, byte-identical to before this key existed.
    house_rules = data.pop('house_rules', None)
    # Mythic grant (mythic map, ticket 02), read by NAME and popped before `items` like the flags
    # above. THE INPUT IS THE GATE: absent -> None -> never mythic (no rarity roll, so the goldens
    # are untouched by construction); an int 1-10 -> exactly that tier; true/'y' -> a rolled tier
    # that decays toward the low end (weights 11 - tier, mythic.py owns the constant). No level
    # gate -- the GM asking for a mythic character is the gate.
    mythic = data.pop('mythic', None)
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

    results = process_input_values(non_input_data, spheres_flag, seed, professions_flag, trainers_flag,
                                   misc_homebrew_rules, luck_direction, optimize, house_rules, mythic)
    # Promote the generator's bare '/license' path to an absolute URL. The Foundry module stores this
    # payload on an Actor and may surface the pointer long after the request, in a context that has no
    # idea which backend produced it -- a relative path would resolve against Foundry's own host.
    if isinstance(results, dict) and results.get('license_url'):
        results['license_url'] = url_for('license_text', _external=True)

    # No server-side session. This used to write the whole payload to `session['character_data']`
    # and then read it back on the next line -- a local variable wearing a session's clothes,
    # inherited from app_Backup_Working.py. Nothing ever read it across requests: none of the four
    # routes touches the session, and both consumers (the FoundryVTT module, the standalone web
    # sheet) keep the payload themselves. It cost a full serialisation of the payload to disk (or
    # Redis) on every request -- 40 KB for a level-5 rogue, more at high level -- for a 60-second
    # lifetime nobody queried. If a route ever DOES need to recall a
    # character, the `generation_seed` in the payload replays it exactly -- that is the intended
    # handle, and it is cheaper than storing the result.
    return jsonify(results)

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