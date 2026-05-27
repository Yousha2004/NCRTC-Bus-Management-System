import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.models.user import User, Role
from app.models.bus import Bus, Route, Station, Schedule, Incident, Notice
from passlib.context import CryptContext
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, LineString

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed():
    db = SessionLocal()
    roles = ["admin", "control_operator", "depot_manager", "driver", "conductor"]
    role_objs = {}
    for r_name in roles:
        role = db.query(Role).filter(Role.name == r_name).first()
        if not role:
            role = Role(name=r_name)
            db.add(role)
            db.commit()
            db.refresh(role)
        role_objs[r_name] = role

    users_data = [
        ("admin", "admin@ncrtc.in", "admin123", "admin"),
        ("operator1", "op1@ncrtc.in", "op123", "control_operator"),
        ("manager1", "mgr1@ncrtc.in", "mgr123", "depot_manager"),
        ("driver1", "dr1@ncrtc.in", "dr123", "driver"),
        ("conductor1", "co1@ncrtc.in", "co123", "conductor"),
    ]
    for username, email, pwd, r_name in users_data:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(
                username=username,
                email=email,
                hashed_password=get_password_hash(pwd),
                role_id=role_objs[r_name].id
            )
            db.add(user)
    db.commit()

    routes_data = [
        ("Delhi-Meerut Express", LineString([(77.20, 28.61), (77.42, 28.66), (77.70, 28.98)])),
        ("Delhi-Ghaziabad Local", LineString([(77.20, 28.61), (77.30, 28.63), (77.42, 28.66)])),
    ]
    for name, path in routes_data:
        route = db.query(Route).filter(Route.route_name == name).first()
        if not route:
            route = Route(route_name=name, path=from_shape(path, srid=4326))
            db.add(route)
    db.commit()

    stations_data = [
        ("Sarai Kale Khan", Point(77.25, 28.59)),
        ("Ghaziabad Central", Point(77.43, 28.67)),
        ("Meerut City", Point(77.71, 29.00)),
    ]
    for name, loc in stations_data:
        station = db.query(Station).filter(Station.name == name).first()
        if not station:
            station = Station(name=name, location=from_shape(loc, srid=4326))
            db.add(station)
    db.commit()

    buses_data = [
        ("DL-1PC-0001", "Volvo 9400"),
        ("UP-14-BT-1234", "Tata Marcopolo"),
    ]
    for num, model in buses_data:
        bus = db.query(Bus).filter(Bus.bus_number == num).first()
        if not bus:
            bus = Bus(bus_number=num, model=model, current_location=from_shape(Point(77.20, 28.61), srid=4326))
            db.add(bus)
    db.commit()
    print("Database seeded successfully!")
    db.close()

if __name__ == "__main__":
    seed()
