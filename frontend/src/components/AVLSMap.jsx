import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Tooltip, Polyline } from 'react-leaflet';
import L from 'leaflet';
import api from '../lib/api';

const busIcon = new L.Icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
  iconSize: [30, 30],
});

const statusColor = { active: '#16a34a', idle: '#9ca3af', maintenance: '#d97706' };

export default function AVLSMap() {
  const [buses, setBuses] = useState([]);
  const [depots, setDepots] = useState([]);
  const [depotId, setDepotId] = useState('');
  const [selected, setSelected] = useState(null); // vehicle detail

  const fetchBuses = async (d) => {
    try {
      const res = await api.get('/avls/live', { params: d ? { depot_id: d } : {} });
      setBuses(res.data);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { api.get('/avls/depots').then((r) => setDepots(r.data)).catch(() => {}); }, []);
  useEffect(() => {
    fetchBuses(depotId);
    const t = setInterval(() => fetchBuses(depotId), 5000);
    return () => clearInterval(t);
  }, [depotId]);

  const openVehicle = async (id) => {
    try { const r = await api.get(`/avls/vehicle/${id}`); setSelected(r.data); }
    catch (e) { console.error(e); }
  };

  return (
    <div className="relative" style={{ height: 'calc(100vh - 56px)', width: '100%' }}>
      <div className="absolute top-3 left-3 z-[1000] bg-white rounded shadow px-3 py-2 flex items-center gap-2">
        <label className="text-sm font-medium">Depot:</label>
        <select value={depotId} onChange={(e) => setDepotId(e.target.value)} className="text-sm border rounded p-1">
          <option value="">All depots</option>
          {depots.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <span className="text-xs text-gray-500">{buses.length} buses</span>
      </div>

      <MapContainer center={[28.62, 77.35]} zoom={11} style={{ height: '100%', width: '100%' }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {buses.map((bus) => bus.location && (
          <Marker key={bus.id} position={[bus.location.coordinates[1], bus.location.coordinates[0]]}
                  icon={busIcon} eventHandlers={{ click: () => openVehicle(bus.id) }}>
            <Tooltip>
              <b>{bus.bus_number}</b> · {bus.speed} km/h<br />
              <span style={{ color: statusColor[bus.status] }}>{bus.status}</span>
              {bus.route ? <> · {bus.route}</> : null}
            </Tooltip>
          </Marker>
        ))}
        {selected?.recent_trail?.length > 1 && (
          <Polyline positions={selected.recent_trail.map((c) => [c[1], c[0]])} color="#2563eb" />
        )}
      </MapContainer>

      {selected && (
        <div className="absolute top-3 right-3 z-[1000] bg-white rounded shadow p-4 w-72">
          <div className="flex justify-between items-start">
            <h3 className="font-bold text-lg">{selected.bus_number}</h3>
            <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-700">✕</button>
          </div>
          <dl className="text-sm mt-2 space-y-1">
            <div className="flex justify-between"><dt className="text-gray-500">Model</dt><dd>{selected.model}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Status</dt>
              <dd style={{ color: statusColor[selected.status] }}>{selected.status}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Speed</dt><dd>{selected.speed} km/h</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Depot</dt><dd>{selected.depot || '—'}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Driver</dt><dd>{selected.driver || '—'}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Route</dt><dd>{selected.route || '—'}</dd></div>
          </dl>
          <p className="text-xs text-gray-400 mt-3">
            Blue line = last 30 min of GPS ({selected.recent_trail?.length || 0} pings)
          </p>
        </div>
      )}
    </div>
  );
}
