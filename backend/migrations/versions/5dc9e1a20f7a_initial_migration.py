"""Initial migration

Revision ID: 5dc9e1a20f7a
Revises:
Create Date: 2026-05-27 19:06:12.186168

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import geoalchemy2

revision: str = '5dc9e1a20f7a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('buses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bus_number', sa.String(), nullable=True),
    sa.Column('model', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('current_location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('last_updated', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_buses_bus_number'), 'buses', ['bus_number'], unique=True)
    op.create_index(op.f('ix_buses_id'), 'buses', ['id'], unique=False)
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_table('routes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('route_name', sa.String(), nullable=True),
    sa.Column('path', geoalchemy2.types.Geometry(geometry_type='LINESTRING', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_routes_id'), 'routes', ['id'], unique=False)
    op.create_index(op.f('ix_routes_route_name'), 'routes', ['route_name'], unique=True)
    op.create_table('stations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stations_id'), 'stations', ['id'], unique=False)
    op.create_index(op.f('ix_stations_name'), 'stations', ['name'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('incidents',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bus_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.Column('severity', sa.String(), nullable=True),
    sa.Column('reported_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['bus_id'], ['buses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incidents_id'), 'incidents', ['id'], unique=False)
    op.create_table('notices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('content', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notices_id'), 'notices', ['id'], unique=False)
    op.create_table('schedules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('bus_id', sa.Integer(), nullable=True),
    sa.Column('route_id', sa.Integer(), nullable=True),
    sa.Column('driver_id', sa.Integer(), nullable=True),
    sa.Column('conductor_id', sa.Integer(), nullable=True),
    sa.Column('departure_time', sa.DateTime(), nullable=True),
    sa.Column('arrival_time', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['bus_id'], ['buses.id'], ),
    sa.ForeignKeyConstraint(['conductor_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['driver_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedules_id'), 'schedules', ['id'], unique=False)

def downgrade() -> None:
    op.drop_table('schedules')
    op.drop_table('notices')
    op.drop_table('incidents')
    op.drop_table('users')
    op.drop_table('stations')
    op.drop_table('routes')
    op.drop_table('roles')
    op.drop_table('buses')
