"""GPS simulation: every few seconds, advance each active bus along a route and
record a new ping (with speed). This animates the live map. Stop with Ctrl+C.

In production this would be a TCP ingest service feeding a queue feeding a
processor; here a single script writes straight to the DB through the ORM.
"""
import time
import random
import datetime
from app.db.session import SessionLocal
from app.models.bus import Bus, Route, BusLocationHistory
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point

STEP = 0.02  # fraction of the route advanced each tick


def simulate():
    db = SessionLocal()
    buses = db.query(Bus).filter(Bus.status == "active").all()
    routes = db.query(Route).all()
    if not buses or not routes:
        print("Nothing to simulate (seed the database first).")
        return

    # pick a route per bus (prefer its own depot's route) and a starting position
    route_by_bus, frac_by_bus = {}, {}
    for bus in buses:
        depot_routes = [r for r in routes if r.depot_id == bus.depot_id and r.path is not None]
        pool = depot_routes or [r for r in routes if r.path is not None]
        route_by_bus[bus.id] = random.choice(pool)
        frac_by_bus[bus.id] = random.random()

    # cache route geometries + bus ids so each tick uses a short-lived session
    path_by_bus = {b.id: to_shape(route_by_bus[b.id].path) for b in buses}
    bus_ids = [b.id for b in buses]
    db.close()

    print(f"Simulating {len(bus_ids)} active buses. Ctrl+C to stop.", flush=True)
    tick = 0
    try:
        while True:
            tick += 1
            s = SessionLocal()
            try:
                now = datetime.datetime.utcnow()
                bus_rows, ping_rows = [], []
                for bid in bus_ids:
                    frac_by_bus[bid] = (frac_by_bus[bid] + STEP) % 1.0
                    pt = path_by_bus[bid].interpolate(frac_by_bus[bid], normalized=True)
                    loc = from_shape(Point(pt.x, pt.y), srid=4326)
                    speed = round(random.uniform(15, 50), 1)
                    bus_rows.append({"id": bid, "current_location": loc, "current_speed": speed, "last_updated": now})
                    ping_rows.append({"bus_id": bid, "location": loc, "speed": speed, "timestamp": now})
                # batched writes: 2 round-trips instead of ~80 (matters over a remote DB)
                s.bulk_update_mappings(Bus, bus_rows)
                s.bulk_insert_mappings(BusLocationHistory, ping_rows)
                s.commit()
                if tick % 6 == 1:
                    print(f"tick {tick}: updated {len(bus_ids)} buses at {now:%H:%M:%S}", flush=True)
            except Exception as e:  # keep the simulation alive across transient DB hiccups
                s.rollback()
                print(f"tick {tick} error (will retry): {e}", flush=True)
            finally:
                s.close()
            time.sleep(5)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    simulate()
