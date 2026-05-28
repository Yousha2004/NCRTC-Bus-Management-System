import time
import random
from app.db.session import SessionLocal
from app.models.bus import Bus, Route, BusLocationHistory
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point, LineString
import datetime

def simulate():
    db = SessionLocal()
    buses = db.query(Bus).all()
    routes = db.query(Route).all()
    if not buses or not routes:
        return
    try:
        while True:
            for bus in buses:
                route = random.choice(routes)
                path = to_shape(route.path)
                fraction = random.random()
                new_point = path.interpolate(fraction, normalized=True)
                loc = from_shape(new_point, srid=4326)
                bus.current_location = loc
                bus.last_updated = datetime.datetime.utcnow()

                history = BusLocationHistory(
                    bus_id=bus.id,
                    location=loc,
                    timestamp=bus.last_updated
                )
                db.add(history)
            db.commit()
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        db.close()

if __name__ == "__main__":
    simulate()
