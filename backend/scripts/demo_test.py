"""End-to-end smoke test of the PRD section-8 demo flow against the running API."""
import json
import urllib.request
import urllib.parse
from datetime import date, timedelta

BASE = "http://localhost:8000"


def call(method, path, token=None, data=None, form=None):
    url = BASE + path
    headers = {}
    body = None
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            txt = r.read().decode()
            return r.status, (json.loads(txt) if txt else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def login(u, p):
    s, r = call("POST", "/auth/login", form={"username": u, "password": p})
    assert s == 200, f"login {u} failed: {r}"
    return r["access_token"], r["role"]


def ok(label, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + label + ("  " + str(extra) if extra else ""))
    return cond


fails = 0

# 1. admin creates a route
admin, _ = login("admin", "admin123")
_, stops = call("GET", "/scheduling/stops", admin)
picked = [s["id"] for s in stops[:5]]
_, depots = call("GET", "/avls/depots", admin)
s, r = call("POST", "/scheduling/routes", admin, data={
    "code": "RTEST1", "route_name": "Demo Test Line", "depot_id": depots[0]["id"],
    "stops": [{"stop_id": sid, "sequence": i, "planned_offset_min": i * 8} for i, sid in enumerate(picked)],
})
fails += not ok("admin create route", s == 200, r)

# 2. manager sees roster + publishes tomorrow's duties
mgr, _ = login("manager1", "mgr123")
tomorrow = str(date.today() + timedelta(days=1))
s, duties = call("GET", "/scheduling/duties", mgr)
fails += not ok("manager sees roster", s == 200 and len(duties) > 0, f"{len(duties) if isinstance(duties,list) else duties} duties")
s, r = call("POST", "/scheduling/duties/publish", mgr, data={"date": tomorrow})
fails += not ok("manager publishes tomorrow", s == 200, r)

# 3. driver: today's duty, acknowledge, read notice, panic
drv, _ = login("driver1", "dr123")
s, duty = call("GET", "/scheduling/duties/today", drv)
fails += not ok("driver has today's duty", s == 200 and duty is not None, duty)
if duty:
    s, r = call("POST", f"/scheduling/duties/{duty['id']}/acknowledge", drv)
    fails += not ok("driver acknowledges duty", s == 200 and r["status"] == "acknowledged")
s, notices = call("GET", "/cms/", drv)
fails += not ok("driver sees notices", s == 200 and len(notices) > 0, f"{len(notices) if isinstance(notices,list) else notices}")
if isinstance(notices, list) and notices:
    s, _ = call("POST", f"/cms/{notices[0]['id']}/read", drv)
    fails += not ok("driver marks notice read", s == 200)
s, panic = call("POST", "/ims/panic", drv)
fails += not ok("driver panic -> P1 incident", s == 200 and panic["severity"] == "P1", panic)

# 4. operator: live map, sees the new P1, assigns it
op, _ = login("operator1", "op123")
s, live = call("GET", "/avls/live", op)
fails += not ok("operator live map", s == 200 and len(live) > 0, f"{len(live) if isinstance(live,list) else live} buses")
s, p1s = call("GET", "/ims/?severity=P1", op)
fails += not ok("operator sees P1 queue", s == 200 and any(i["status"] == "open" for i in p1s), f"{len(p1s)} P1s")
if panic and isinstance(panic, dict):
    _, drivers = call("GET", "/scheduling/drivers", op)
    s, r = call("POST", f"/ims/{panic['id']}/assign", op, data={"assigned_to": drivers[0]["id"]})
    fails += not ok("operator assigns incident", s == 200, r)
    s, detail = call("GET", f"/ims/{panic['id']}", op)
    fails += not ok("incident has timeline", s == 200 and len(detail["events"]) >= 2, f"{len(detail['events'])} events")

# 5. history: yesterday's trail for a vehicle
_, vehicles = call("GET", "/scheduling/vehicles", op)
yest = str(date.today() - timedelta(days=1))
s, hist = call("GET", f"/avls/history/{vehicles[0]['id']}?on={yest}", op)
fails += not ok("history has a path", s == 200, f"{hist.get('count') if isinstance(hist,dict) else hist} pings")

# 6. depot scoping: manager1 (SKK) should NOT see other depots' buses
s, mlive = call("GET", "/avls/live", mgr)
depot_ids = {b["depot_id"] for b in mlive}
fails += not ok("depot scoping for manager", len(depot_ids) == 1, f"depots seen: {depot_ids}")

# 7. RBAC: driver cannot create a route
s, _ = call("POST", "/scheduling/routes", drv, data={"code": "X", "route_name": "x", "depot_id": depots[0]["id"], "stops": []})
fails += not ok("driver blocked from route creation", s == 403, f"status {s}")

print("\n" + ("ALL PASSED" if fails == 0 else f"{fails} FAILURES"))
