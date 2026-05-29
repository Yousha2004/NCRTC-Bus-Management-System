import { useEffect, useState } from 'react';
import api, { getRole } from '../lib/api';

function mondayOf(d) {
  const x = new Date(d);
  const day = (x.getDay() + 6) % 7; // 0 = Monday
  x.setDate(x.getDate() - day);
  return x.toISOString().slice(0, 10);
}
const addDays = (iso, n) => { const d = new Date(iso); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
const DAYNAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function SchedulingDashboard() {
  const role = getRole();
  const canManage = ['admin', 'depot_manager', 'control_operator'].includes(role);
  const [weekStart, setWeekStart] = useState(mondayOf(new Date()));
  const [duties, setDuties] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [msg, setMsg] = useState('');

  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  const loadDuties = () => api.get('/scheduling/duties', { params: { week_start: weekStart } })
    .then((r) => setDuties(r.data)).catch(() => {});

  useEffect(() => { loadDuties(); }, [weekStart]);
  useEffect(() => {
    api.get('/scheduling/drivers').then((r) => setDrivers(r.data)).catch(() => {});
    api.get('/scheduling/vehicles').then((r) => setVehicles(r.data)).catch(() => {});
    api.get('/scheduling/routes').then((r) => setRoutes(r.data)).catch(() => {});
  }, []);

  const cell = (driverId, day) => duties.find((d) => d.driver_id === driverId && d.date === day);

  const publishDay = async (day) => {
    setMsg('');
    try {
      const r = await api.post('/scheduling/duties/publish', { date: day });
      setMsg(`Published ${r.data.published} duties for ${day}.`);
      loadDuties();
    } catch (e) { setMsg(e.response?.data?.detail || 'Publish failed'); }
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4 flex-wrap gap-2">
        <h2 className="text-2xl font-bold">Scheduling — Weekly Roster</h2>
        <div className="flex items-center gap-2 text-sm">
          <button onClick={() => setWeekStart(addDays(weekStart, -7))} className="px-2 py-1 border rounded">‹ Prev</button>
          <span className="font-medium">Week of {weekStart}</span>
          <button onClick={() => setWeekStart(addDays(weekStart, 7))} className="px-2 py-1 border rounded">Next ›</button>
        </div>
      </div>
      {msg && <p className="mb-3 text-sm text-blue-700 bg-blue-50 px-3 py-2 rounded">{msg}</p>}

      <div className="overflow-x-auto bg-white rounded shadow">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="text-left p-2 sticky left-0 bg-gray-100">Driver</th>
              {days.map((d, i) => (
                <th key={d} className="p-2 text-center min-w-[130px]">
                  <div>{DAYNAMES[i]} {d.slice(5)}</div>
                  {canManage && (
                    <button onClick={() => publishDay(d)}
                            className="mt-1 text-xs bg-green-600 text-white px-2 py-0.5 rounded hover:bg-green-500">
                      Publish
                    </button>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {drivers.map((dr) => (
              <tr key={dr.id} className="border-t">
                <td className="p-2 font-medium sticky left-0 bg-white whitespace-nowrap">{dr.full_name}</td>
                {days.map((day) => {
                  const c = cell(dr.id, day);
                  return (
                    <td key={day} className="p-2 text-center">
                      {c ? (
                        <div className={`rounded px-2 py-1 text-xs ${
                          c.status === 'acknowledged' ? 'bg-green-100' :
                          c.status === 'published' ? 'bg-blue-100' : 'bg-gray-100'}`}>
                          <div className="font-semibold">{c.bus_number}</div>
                          <div className="text-gray-600">{c.route_name}</div>
                          <div className="text-[10px] uppercase text-gray-500">{c.status}</div>
                        </div>
                      ) : <span className="text-gray-300">—</span>}
                    </td>
                  );
                })}
              </tr>
            ))}
            {drivers.length === 0 && <tr><td className="p-4 text-gray-500" colSpan={8}>No drivers in scope.</td></tr>}
          </tbody>
        </table>
      </div>

      {canManage && <AssignForm drivers={drivers} vehicles={vehicles} routes={routes} onDone={loadDuties} setMsg={setMsg} />}
      {role === 'admin' && <RouteForm routes={routes} onDone={() => api.get('/scheduling/routes').then((r) => setRoutes(r.data))} setMsg={setMsg} />}
    </div>
  );
}

function AssignForm({ drivers, vehicles, routes, onDone, setMsg }) {
  const today = new Date().toISOString().slice(0, 10);
  const [f, setF] = useState({ date: today, driver_id: '', bus_id: '', route_id: '', start: '07:00' });
  const submit = async (e) => {
    e.preventDefault();
    setMsg('');
    try {
      const start = `${f.date}T${f.start}:00`;
      const end = `${f.date}T${String(Number(f.start.slice(0, 2)) + 8).padStart(2, '0')}:00:00`;
      await api.post('/scheduling/duties', {
        date: f.date, driver_id: Number(f.driver_id), bus_id: Number(f.bus_id),
        route_id: Number(f.route_id), start_time: start, end_time: end,
      });
      setMsg('Duty assigned (draft). Publish it to notify the driver.');
      onDone();
    } catch (e) { setMsg(e.response?.data?.detail || 'Assign failed'); }
  };
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  return (
    <form onSubmit={submit} className="mt-6 bg-white rounded shadow p-4 flex flex-wrap gap-3 items-end">
      <h3 className="w-full font-semibold">Assign a duty</h3>
      <div><label className="block text-xs mb-1">Date</label><input type="date" value={f.date} onChange={set('date')} className="border rounded p-2 text-sm" /></div>
      <div><label className="block text-xs mb-1">Driver</label>
        <select value={f.driver_id} onChange={set('driver_id')} required className="border rounded p-2 text-sm">
          <option value="">…</option>{drivers.map((d) => <option key={d.id} value={d.id}>{d.full_name}</option>)}
        </select></div>
      <div><label className="block text-xs mb-1">Vehicle</label>
        <select value={f.bus_id} onChange={set('bus_id')} required className="border rounded p-2 text-sm">
          <option value="">…</option>{vehicles.map((v) => <option key={v.id} value={v.id}>{v.bus_number}</option>)}
        </select></div>
      <div><label className="block text-xs mb-1">Route</label>
        <select value={f.route_id} onChange={set('route_id')} required className="border rounded p-2 text-sm">
          <option value="">…</option>{routes.map((r) => <option key={r.id} value={r.id}>{r.route_name}</option>)}
        </select></div>
      <div><label className="block text-xs mb-1">Start</label><input type="time" value={f.start} onChange={set('start')} className="border rounded p-2 text-sm" /></div>
      <button className="bg-blue-900 text-white px-4 py-2 rounded text-sm hover:bg-blue-800">Assign</button>
    </form>
  );
}

function RouteForm({ routes, onDone, setMsg }) {
  const [depots, setDepots] = useState([]);
  const [stops, setStops] = useState([]);
  const [f, setF] = useState({ code: '', route_name: '', depot_id: '', picked: [] });
  useEffect(() => {
    api.get('/avls/depots').then((r) => setDepots(r.data)).catch(() => {});
    api.get('/scheduling/stops').then((r) => setStops(r.data)).catch(() => {});
  }, []);
  const toggle = (id) => setF((p) => ({ ...p, picked: p.picked.includes(id) ? p.picked.filter((x) => x !== id) : [...p.picked, id] }));
  const submit = async (e) => {
    e.preventDefault();
    setMsg('');
    try {
      await api.post('/scheduling/routes', {
        code: f.code, route_name: f.route_name, depot_id: Number(f.depot_id),
        stops: f.picked.map((id, i) => ({ stop_id: id, sequence: i, planned_offset_min: i * 8 })),
      });
      setMsg(`Route ${f.code} created.`);
      setF({ code: '', route_name: '', depot_id: '', picked: [] });
      onDone();
    } catch (e) { setMsg(e.response?.data?.detail || 'Route create failed'); }
  };
  return (
    <form onSubmit={submit} className="mt-6 bg-white rounded shadow p-4">
      <h3 className="font-semibold mb-3">Create a route (admin)</h3>
      <div className="flex flex-wrap gap-3 items-end mb-3">
        <div><label className="block text-xs mb-1">Code</label><input value={f.code} onChange={(e) => setF({ ...f, code: e.target.value })} required className="border rounded p-2 text-sm" placeholder="R99" /></div>
        <div><label className="block text-xs mb-1">Name</label><input value={f.route_name} onChange={(e) => setF({ ...f, route_name: e.target.value })} required className="border rounded p-2 text-sm w-56" placeholder="New Express Line" /></div>
        <div><label className="block text-xs mb-1">Depot</label>
          <select value={f.depot_id} onChange={(e) => setF({ ...f, depot_id: e.target.value })} required className="border rounded p-2 text-sm">
            <option value="">…</option>{depots.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select></div>
        <button className="bg-blue-900 text-white px-4 py-2 rounded text-sm hover:bg-blue-800">Create</button>
      </div>
      <p className="text-xs mb-1 text-gray-500">Pick stops in order (click to add/remove): {f.picked.length} selected</p>
      <div className="flex flex-wrap gap-2">
        {stops.map((s) => {
          const i = f.picked.indexOf(s.id);
          return (
            <button type="button" key={s.id} onClick={() => toggle(s.id)}
                    className={`text-xs px-2 py-1 rounded border ${i >= 0 ? 'bg-blue-600 text-white' : 'bg-white'}`}>
              {i >= 0 ? `${i + 1}. ` : ''}{s.name}
            </button>
          );
        })}
      </div>
    </form>
  );
}
