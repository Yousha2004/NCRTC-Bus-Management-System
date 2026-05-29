import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Tooltip } from 'react-leaflet';
import api from '../lib/api';

function yesterdayISO() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
}

export default function HistoryPage() {
  const [vehicles, setVehicles] = useState([]);
  const [busId, setBusId] = useState('');
  const [day, setDay] = useState(yesterdayISO()); // trails are seeded for yesterday
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { api.get('/scheduling/vehicles').then((r) => setVehicles(r.data)).catch(() => {}); }, []);

  const load = async () => {
    if (!busId) return;
    setLoading(true);
    try {
      const r = await api.get(`/avls/history/${busId}`, { params: { on: day } });
      setData(r.data);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const line = data?.path?.map((p) => [p.coordinates[1], p.coordinates[0]]) || [];

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Trip History</h2>
      <div className="flex flex-wrap gap-3 items-end mb-4 bg-white p-4 rounded shadow">
        <div>
          <label className="block text-sm font-medium mb-1">Vehicle</label>
          <select value={busId} onChange={(e) => setBusId(e.target.value)} className="border rounded p-2 text-sm">
            <option value="">Select…</option>
            {vehicles.map((v) => <option key={v.id} value={v.id}>{v.bus_number}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Date</label>
          <input type="date" value={day} onChange={(e) => setDay(e.target.value)} className="border rounded p-2 text-sm" />
        </div>
        <button onClick={load} className="bg-blue-900 text-white px-4 py-2 rounded text-sm hover:bg-blue-800">
          Show path
        </button>
        {data && <span className="text-sm text-gray-500">{data.count} pings on {data.date}</span>}
      </div>

      <div style={{ height: 'calc(100vh - 220px)' }} className="rounded overflow-hidden shadow">
        <MapContainer center={[28.7, 77.4]} zoom={10} style={{ height: '100%', width: '100%' }}>
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {line.length > 1 && <Polyline positions={line} color="#dc2626" />}
          {line.length > 0 && <CircleMarker center={line[0]} radius={6} color="#16a34a"><Tooltip>Start</Tooltip></CircleMarker>}
          {line.length > 1 && <CircleMarker center={line[line.length - 1]} radius={6} color="#dc2626"><Tooltip>End</Tooltip></CircleMarker>}
        </MapContainer>
      </div>
      {loading && <p className="text-sm text-gray-500 mt-2">Loading…</p>}
      {data && data.count === 0 && <p className="text-sm text-amber-600 mt-2">No GPS data for that vehicle/date. Seeded trails are on {yesterdayISO()}.</p>}
    </div>
  );
}
