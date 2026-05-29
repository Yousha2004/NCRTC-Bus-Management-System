"""Seed the database with realistic dummy data for the demo.

Run on a fresh schema (see scripts/init_db.py):

    python scripts/init_db.py --drop
    python scripts/seed.py

Idempotent guard: if vehicles already exist, it does nothing.
"""
import datetime
import random
from datetime import date, time, timedelta

from passlib.context import CryptContext
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, LineString

from app.db.session import SessionLocal
from app.models.user import User, Role
from app.models.bus import (
    Depot, Bus, Stop, Route, RouteStop, Duty,
    Incident, IncidentEvent, Notice, NoticeRead, BusLocationHistory,
)

random.seed(42)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
HASH = pwd_context.hash("password")  # shared hash for bulk users (fast: hash once)


def h(pw):
    return pwd_context.hash(pw)


# --- reference data -------------------------------------------------------
DEPOTS = [
    ("SKK", "Sarai Kale Khan Depot", (77.260, 28.590)),
    ("ANV", "Anand Vihar Depot", (77.315, 28.650)),
    ("GZB", "Ghaziabad Depot", (77.430, 28.670)),
    ("NOI", "Noida Sec-37 Depot", (77.330, 28.570)),
    ("MRT", "Meerut Depot", (77.700, 28.980)),
]

STOPS = [
    ("Sarai Kale Khan", (77.255, 28.589)),
    ("Ashram", (77.260, 28.572)),
    ("Anand Vihar ISBT", (77.315, 28.647)),
    ("Vaishali", (77.339, 28.645)),
    ("Kaushambi", (77.325, 28.645)),
    ("Ghaziabad Central", (77.430, 28.670)),
    ("Vasundhara", (77.375, 28.660)),
    ("Indirapuram", (77.370, 28.640)),
    ("Noida Sec-18", (77.325, 28.570)),
    ("Noida Sec-37", (77.330, 28.567)),
    ("Botanical Garden", (77.334, 28.564)),
    ("Modinagar", (77.575, 28.830)),
    ("Muradnagar", (77.500, 28.780)),
    ("Meerut South", (77.690, 28.960)),
    ("Meerut City", (77.706, 29.000)),
]

REG_PREFIXES = ["DL-1PC", "DL-1PD", "UP-14-BT", "UP-15-AT", "HR-26-CX"]
MODELS = ["Volvo 9400", "Tata Marcopolo", "Ashok Leyland 12M", "Eicher Skyline", "JBM Citylife EV"]
FIRST = ["Amit", "Rohit", "Suresh", "Vijay", "Anil", "Manoj", "Deepak", "Rakesh", "Sandeep",
         "Ravi", "Pradeep", "Naveen", "Sunil", "Arun", "Vikas", "Ramesh", "Mahesh", "Gaurav",
         "Neha", "Pooja", "Kavita", "Anita", "Sunita", "Priya", "Meena"]
LAST = ["Kumar", "Sharma", "Singh", "Yadav", "Verma", "Gupta", "Mishra", "Pandey", "Chauhan",
        "Tyagi", "Rana", "Saini", "Bhardwaj", "Tomar"]


def seed():
    db = SessionLocal()
    if db.query(Bus).count() > 0:
        print("Already seeded (vehicles exist). Skipping. Use init_db.py --drop to reset.")
        db.close()
        return

    # --- roles ---
    role_objs = {}
    for r_name in ["admin", "control_operator", "depot_manager", "driver", "conductor"]:
        role = Role(name=r_name)
        db.add(role)
        db.flush()
        role_objs[r_name] = role

    # --- depots ---
    depot_objs = []
    for code, name, (lng, lat) in DEPOTS:
        d = Depot(code=code, name=name, location=from_shape(Point(lng, lat), srid=4326))
        db.add(d)
        db.flush()
        depot_objs.append(d)

    # --- stops ---
    stop_objs = []
    for name, (lng, lat) in STOPS:
        s = Stop(name=name, location=from_shape(Point(lng, lat), srid=4326))
        db.add(s)
        db.flush()
        stop_objs.append(s)

    # --- known demo users (simple passwords, role table) ---
    demo = [
        ("admin", "admin@ncrtc.in", "admin123", "admin", None, "System Admin"),
        ("operator1", "op1@ncrtc.in", "op123", "control_operator", None, "Control Operator"),
        ("manager1", "mgr1@ncrtc.in", "mgr123", "depot_manager", 0, "Depot Manager SKK"),
        ("driver1", "dr1@ncrtc.in", "dr123", "driver", 0, "Driver One"),
        ("conductor1", "co1@ncrtc.in", "co123", "conductor", 0, "Conductor One"),
    ]
    drivers_by_depot = {i: [] for i in range(len(depot_objs))}
    for username, email, pw, r_name, depot_idx, full_name in demo:
        depot_id = depot_objs[depot_idx].id if depot_idx is not None else None
        u = User(username=username, email=email, full_name=full_name,
                 phone="98" + str(random.randint(10000000, 99999999)),
                 hashed_password=h(pw), role_id=role_objs[r_name].id, depot_id=depot_id)
        db.add(u)
        db.flush()
        if r_name == "driver":
            drivers_by_depot[depot_idx].append(u)

    # --- bulk users: managers per depot + ~70 drivers/conductors ---
    uname_n = 2
    for di, depot in enumerate(depot_objs):
        # one manager per depot (manager1 already covers depot 0)
        if di != 0:
            db.add(User(username=f"manager{di+1}", email=f"mgr{di+1}@ncrtc.in",
                        full_name=f"Depot Manager {depot.code}", phone="98" + str(random.randint(10000000, 99999999)),
                        hashed_password=HASH, role_id=role_objs["depot_manager"].id, depot_id=depot.id))
        # drivers + conductors
        for _ in range(14):
            name = f"{random.choice(FIRST)} {random.choice(LAST)}"
            role_name = "driver" if random.random() < 0.6 else "conductor"
            u = User(username=f"user{uname_n}", email=f"user{uname_n}@ncrtc.in", full_name=name,
                     phone="98" + str(random.randint(10000000, 99999999)),
                     hashed_password=HASH, role_id=role_objs[role_name].id, depot_id=depot.id)
            db.add(u)
            db.flush()
            uname_n += 1
            if role_name == "driver":
                drivers_by_depot[di].append(u)
    db.commit()

    # --- vehicles: ~50 across depots ---
    buses = []
    used_regs = set()
    for di, depot in enumerate(depot_objs):
        for _ in range(10):
            while True:
                reg = f"{random.choice(REG_PREFIXES)}-{random.randint(1000, 9999)}"
                if reg not in used_regs:
                    used_regs.add(reg)
                    break
            status = random.choices(["active", "idle", "maintenance"], weights=[7, 2, 1])[0]
            lng, lat = DEPOTS[di][2]
            b = Bus(bus_number=reg, model=random.choice(MODELS), status=status, depot_id=depot.id,
                    current_location=from_shape(Point(lng + random.uniform(-0.01, 0.01),
                                                      lat + random.uniform(-0.01, 0.01)), srid=4326),
                    current_speed=0.0)
            db.add(b)
            db.flush()
            buses.append((di, b))
    db.commit()

    # --- routes: ~12, each with 6-9 stops ---
    routes = []
    for r in range(12):
        di = r % len(depot_objs)
        chosen = sorted(random.sample(range(len(stop_objs)), random.randint(6, 9)))
        route = Route(code=f"R{r+1:02d}", route_name=f"{DEPOTS[di][1].split(' Depot')[0]} Line {r+1}",
                      depot_id=depot_objs[di].id)
        db.add(route)
        db.flush()
        coords = []
        for seq, si in enumerate(chosen):
            db.add(RouteStop(route_id=route.id, stop_id=stop_objs[si].id, sequence=seq,
                             planned_offset_min=seq * 8))
            coords.append(STOPS[si][1])
        route.path = from_shape(LineString(coords), srid=4326)
        routes.append((di, route))
    db.commit()

    routes_by_depot = {i: [r for (d, r) in routes if d == i] for i in range(len(depot_objs))}
    buses_by_depot = {i: [b for (d, b) in buses if d == i] for i in range(len(depot_objs))}

    # --- duties: yesterday (published), today (published), tomorrow (draft) ---
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    def make_duties(day, status):
        for di in range(len(depot_objs)):
            drivers = drivers_by_depot[di]
            deps_buses = buses_by_depot[di]
            deps_routes = routes_by_depot[di]
            if not (drivers and deps_buses and deps_routes):
                continue
            n = min(len(drivers), len(deps_buses), 5)
            for k in range(n):
                start = datetime.datetime.combine(day, time(7 + k, 0))
                db.add(Duty(
                    date=day, bus_id=deps_buses[k].id, route_id=deps_routes[k % len(deps_routes)].id,
                    driver_id=drivers[k].id, depot_id=depot_objs[di].id,
                    start_time=start, end_time=start + timedelta(hours=8), status=status,
                ))

    make_duties(yesterday, "published")
    make_duties(today, "published")   # driver1 gets a published duty to acknowledge in the demo
    make_duties(tomorrow, "draft")    # manager publishes these in the demo
    db.commit()

    # --- GPS history: yesterday's full trail for the first ~10 active buses ---
    trail_buses = [b for (_, b) in buses][:10]
    for b in trail_buses:
        route = db.query(Route).filter(Route.depot_id == b.depot_id).first()
        if not route or route.path is None:
            continue
        line = LineString([STOPS[i][1] for i in range(len(STOPS))])  # fallback
        # use the route's own stops for a plausible path
        rstops = sorted(route.stops, key=lambda x: x.sequence)
        coords = []
        for rs in rstops:
            s = next((s for s in stop_objs if s.id == rs.stop_id), None)
            if s:
                coords.append(STOPS[[so.id for so in stop_objs].index(s.id)][1])
        if len(coords) < 2:
            continue
        line = LineString(coords)
        base = datetime.datetime.combine(yesterday, time(9, 0))
        for step in range(40):
            frac = step / 39.0
            pt = line.interpolate(frac, normalized=True)
            db.add(BusLocationHistory(
                bus_id=b.id, location=from_shape(pt, srid=4326),
                speed=round(random.uniform(15, 45), 1),
                timestamp=base + timedelta(minutes=step * 2),
            ))
    db.commit()

    # --- incidents in various states, with event timelines ---
    admin = db.query(User).filter(User.username == "admin").first()
    op = db.query(User).filter(User.username == "operator1").first()
    sample_incidents = [
        ("breakdown", "P1", "open", "Engine overheating near Ghaziabad Central.", 0),
        ("complaint", "P3", "in_progress", "Passenger complaint about AC not working.", 1),
        ("accident", "P2", "resolved", "Minor scrape with auto-rickshaw; no injuries.", 2),
        ("other", "P3", "acknowledged", "Ticketing machine offline.", 0),
        ("breakdown", "P2", "open", "Flat tyre on the Noida line.", 3),
    ]
    for typ, sev, st, desc, di in sample_incidents:
        bus = buses_by_depot[di][0] if buses_by_depot[di] else None
        inc = Incident(type=typ, severity=sev, status=st, description=desc,
                       bus_id=bus.id if bus else None, depot_id=depot_objs[di].id,
                       raised_by=op.id, assigned_to=(op.id if st != "open" else None),
                       reported_at=datetime.datetime.utcnow() - timedelta(hours=random.randint(1, 20)),
                       resolved_at=(datetime.datetime.utcnow() if st == "resolved" else None))
        db.add(inc)
        db.flush()
        db.add(IncidentEvent(incident_id=inc.id, actor_id=op.id, from_status=None,
                             to_status="open", note="Incident raised"))
        if st in ("acknowledged", "in_progress", "resolved", "closed"):
            db.add(IncidentEvent(incident_id=inc.id, actor_id=op.id, from_status="open",
                                 to_status="acknowledged", note="Acknowledged by control room"))
        if st in ("in_progress", "resolved", "closed"):
            db.add(IncidentEvent(incident_id=inc.id, actor_id=op.id, from_status="acknowledged",
                                 to_status="in_progress", note="Field team dispatched"))
        if st in ("resolved", "closed"):
            db.add(IncidentEvent(incident_id=inc.id, actor_id=op.id, from_status="in_progress",
                                 to_status="resolved", note="Issue resolved on site"))
    db.commit()

    # --- notices, with some reads ---
    n1 = Notice(title="Route Diversion Alert",
                content="Meerut Line diverted due to road maintenance near Modinagar.",
                audience="all", created_by=admin.id)
    n2 = Notice(title="Mandatory Safety Briefing",
                content="All drivers must attend the safety briefing this Friday at their depot.",
                audience="role:driver", created_by=admin.id)
    n3 = Notice(title="Ghaziabad Depot Timing Change",
                content="Ghaziabad depot duties now start 30 minutes earlier.",
                audience=f"depot:{depot_objs[2].id}", created_by=admin.id)
    db.add_all([n1, n2, n3])
    db.flush()
    # mark notice 1 read by a few drivers (so receipts aren't empty)
    some_drivers = drivers_by_depot[0][:2]
    for u in some_drivers:
        db.add(NoticeRead(notice_id=n1.id, user_id=u.id))
    db.commit()

    print("Seeded:",
          db.query(Depot).count(), "depots,",
          db.query(Bus).count(), "vehicles,",
          db.query(User).count(), "users,",
          db.query(Route).count(), "routes,",
          db.query(Duty).count(), "duties,",
          db.query(BusLocationHistory).count(), "pings,",
          db.query(Incident).count(), "incidents,",
          db.query(Notice).count(), "notices.")
    db.close()


if __name__ == "__main__":
    seed()
