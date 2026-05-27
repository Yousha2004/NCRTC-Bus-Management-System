from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db.session import Base
import datetime

class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String, unique=True, index=True)
    model = Column(String)
    status = Column(String, default="active")
    current_location = Column(Geometry("POINT", srid=4326))
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    route_name = Column(String, unique=True, index=True)
    path = Column(Geometry("LINESTRING", srid=4326))

class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(Geometry("POINT", srid=4326))

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    route_id = Column(Integer, ForeignKey("routes.id"))
    driver_id = Column(Integer, ForeignKey("users.id"))
    conductor_id = Column(Integer, ForeignKey("users.id"))
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)

    bus = relationship("Bus")
    route = relationship("Route")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    description = Column(String)
    location = Column(Geometry("POINT", srid=4326))
    severity = Column(String)
    reported_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="open")

class Notice(Base):
    __tablename__ = "notices"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
