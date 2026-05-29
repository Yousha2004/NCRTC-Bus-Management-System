import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';

const SEV_COLOR = { P1: 'bg-red-100 text-red-800', P2: 'bg-amber-100 text-amber-800', P3: 'bg-gray-100 text-gray-700' };
const STATUSES = ['open', 'acknowledged', 'in_progress', 'resolved', 'closed'];

export default function IMSDashboard() {
  const nav = useNavigate();
  const [incidents, setIncidents] = useState([]);
  const [filters, setFilters] = useState({ status: '', severity: '', mine: false });
  const [vehicles, setVehicles] = useState([]);

  const load = () => {
    const params = {};
    if (filters.status) params.status = filters.status;
    if (filters.severity) params.severity = filters.severity;
    if (filters.mine) params.mine = true;
    api.get('/ims/', { params }).then((r) => setIncidents(r.data)).catch(() => {});
  };
  useEffect(() => { load(); }, [filters]);
  useEffect(() => { api.get('/scheduling/vehicles').then((r) => setVehicles(r.data)).catch(() => {}); }, []);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Incident Management</h2>

      <div className="flex flex-wrap gap-3 items-end mb-4 bg-white p-3 rounded shadow text-sm">
        <div><label className="block text-xs mb-1">Status</label>
          <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} className="border rounded p-1">
            <option value="">All</option>{STATUSES.map((s) => <option key={s}>{s}</option>)}
          </select></div>
        <div><label className="block text-xs mb-1">Severity</label>
          <select value={filters.severity} onChange={(e) => setFilters({ ...filters, severity: e.target.value })} className="border rounded p-1">
            <option value="">All</option><option>P1</option><option>P2</option><option>P3</option>
          </select></div>
        <label className="flex items-center gap-1"><input type="checkbox" checked={filters.mine}
          onChange={(e) => setFilters({ ...filters, mine: e.target.checked })} /> Mine only</label>
        <span className="text-gray-500">{incidents.length} incidents</span>
      </div>

      <div className="bg-white rounded shadow overflow-x-auto mb-6">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100"><tr>
            <th className="text-left p-2">Sev</th><th className="text-left p-2">Type</th>
            <th className="text-left p-2">Description</th><th className="text-left p-2">Vehicle</th>
            <th className="text-left p-2">Status</th><th className="text-left p-2">Assigned</th>
          </tr></thead>
          <tbody>
            {incidents.map((i) => (
              <tr key={i.id} onClick={() => nav(`/ims/${i.id}`)} className="border-t hover:bg-blue-50 cursor-pointer">
                <td className="p-2"><span className={`px-2 py-0.5 rounded text-xs font-semibold ${SEV_COLOR[i.severity]}`}>{i.severity}</span></td>
                <td className="p-2">{i.type}</td>
                <td className="p-2">{i.description}</td>
                <td className="p-2">{i.bus_number || '—'}</td>
                <td className="p-2"><span className="text-xs uppercase">{i.status}</span></td>
                <td className="p-2">{i.assigned_to || '—'}</td>
              </tr>
            ))}
            {incidents.length === 0 && <tr><td colSpan={6} className="p-4 text-gray-500">No incidents.</td></tr>}
          </tbody>
        </table>
      </div>

      <RaiseForm vehicles={vehicles} onDone={load} />
    </div>
  );
}

function RaiseForm({ vehicles, onDone }) {
  const [f, setF] = useState({ type: 'breakdown', severity: 'P3', description: '', bus_id: '' });
  const [msg, setMsg] = useState('');
  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/ims/', { type: f.type, severity: f.severity, description: f.description,
        bus_id: f.bus_id ? Number(f.bus_id) : null });
      setMsg('Incident raised.');
      setF({ type: 'breakdown', severity: 'P3', description: '', bus_id: '' });
      onDone();
    } catch (e) { setMsg(e.response?.data?.detail || 'Failed'); }
  };
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  return (
    <form onSubmit={submit} className="bg-white rounded shadow p-4 flex flex-wrap gap-3 items-end text-sm">
      <h3 className="w-full font-semibold">Raise an incident</h3>
      <div><label className="block text-xs mb-1">Type</label>
        <select value={f.type} onChange={set('type')} className="border rounded p-2">
          <option>breakdown</option><option>accident</option><option>complaint</option><option>other</option>
        </select></div>
      <div><label className="block text-xs mb-1">Severity</label>
        <select value={f.severity} onChange={set('severity')} className="border rounded p-2">
          <option>P1</option><option>P2</option><option>P3</option>
        </select></div>
      <div><label className="block text-xs mb-1">Vehicle (optional)</label>
        <select value={f.bus_id} onChange={set('bus_id')} className="border rounded p-2">
          <option value="">—</option>{vehicles.map((v) => <option key={v.id} value={v.id}>{v.bus_number}</option>)}
        </select></div>
      <div className="flex-1 min-w-[200px]"><label className="block text-xs mb-1">Description</label>
        <input value={f.description} onChange={set('description')} required className="border rounded p-2 w-full" /></div>
      <button className="bg-blue-900 text-white px-4 py-2 rounded hover:bg-blue-800">Raise</button>
      {msg && <span className="text-blue-700">{msg}</span>}
    </form>
  );
}
