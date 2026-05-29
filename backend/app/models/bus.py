from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db.session import Base
import datetime


class Depot(Base):
    __tablename__ = "depots"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String)
    location = Column(Geometry("POINT", srid=4326))


class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String, unique=True, index=True)
    model = Column(String)
    status = Column(String, default="active")  # active | idle | maintenance
    depot_id = Column(Integer, ForeignKey("depots.id"))
    current_location = Column(Geometry("POINT", srid=4326))
    current_speed = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

    depot = relationship("Depot")


class Stop(Base):
    __tablename__ = "stops"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(Geometry("POINT", srid=4326))


class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    route_name = Column(String, index=True)
    depot_id = Column(Integer, ForeignKey("depots.id"))
    path = Column(Geometry("LINESTRING", srid=4326))

    depot = relationship("Depot")
    stops = relationship("RouteStop", back_populates="route", order_by="RouteStop.sequence",
                         cascade="all, delete-orphan")


class RouteStop(Base):
    __tablename__ = "route_stops"
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    stop_id = Column(Integer, ForeignKey("stops.id"))
    sequence = Column(Integer)
    planned_offset_min = Column(Integer)  # minutes after route start

    route = relationship("Route", back_populates="stops")
    stop = relationship("Stop")


class Duty(Base):
    __tablename__ = "duties"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    route_id = Column(Integer, ForeignKey("routes.id"))
    driver_id = Column(Integer, ForeignKey("users.id"))
    conductor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    depot_id = Column(Integer, ForeignKey("depots.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String, default="draft")  # draft | published | acknowledged
    ack_at = Column(DateTime, nullable=True)

    bus = relationship("Bus")
    route = relationship("Route")
    driver = relationship("User", foreign_keys=[driver_id])
    conductor = relationship("User", foreign_keys=[conductor_id])
    depot = relationship("Depot")


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, default="other")  # breakdown | accident | complaint | other
    severity = Column(String, default="P3")  # P1 | P2 | P3
    status = Column(String, default="open")  # open | acknowledged | in_progress | resolved | closed
    description = Column(String)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=True)
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=True)
    raised_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    location = Column(Geometry("POINT", srid=4326), nullable=True)
    reported_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    bus = relationship("Bus")
    depot = relationship("Depot")
    raiser = relationship("User", foreign_keys=[raised_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    events = relationship("IncidentEvent", back_populates="incident",
                          order_by="IncidentEvent.ts", cascade="all, delete-orphan")


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    ts = Column(DateTime, default=datetime.datetime.utcnow)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=True)
    note = Column(String)

    incident = relationship("Incident", back_populates="events")
    actor = relationship("User")


class Notice(Base):
    __tablename__ = "notices"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)
    audience = Column(String, default="all")  # all | role:<role> | depot:<depot_id>
    publish_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

    reads = relationship("NoticeRead", back_populates="notice", cascade="all, delete-orphan")


class NoticeRead(Base):
    __tablename__ = "notice_reads"
    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(Integer, ForeignKey("notices.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    read_at = Column(DateTime, default=datetime.datetime.utcnow)

    notice = relationship("Notice", back_populates="reads")
    user = relationship("User")


class BusLocationHistory(Base):
    __tablename__ = "bus_location_history"
    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    location = Column(Geometry("POINT", srid=4326))
    speed = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    bus = relationship("Bus")
