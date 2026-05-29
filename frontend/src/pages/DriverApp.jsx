import { useEffect, useState } from 'react';
import api, { getUser } from '../lib/api';

export default function DriverApp() {
  const user = getUser();
  const [duty, setDuty] = useState(null);
  const [notices, setNotices] = useState([]);
  const [panicMsg, setPanicMsg] = useState('');
  const [confirming, setConfirming] = useState(false);

  const loadDuty = () => api.get('/scheduling/duties/today').then((r) => setDuty(r.data)).catch(() => {});
  const loadNotices = () => api.get('/cms/').then((r) => setNotices(r.data)).catch(() => {});
  useEffect(() => { loadDuty(); loadNotices(); }, []);

  const acknowledge = async () => { await api.post(`/scheduling/duties/${duty.id}/acknowledge`); loadDuty(); };
  const markRead = async (id) => { await api.post(`/cms/${id}/read`); loadNotices(); };
  const logout = () => { localStorage.clear(); window.location.href = '/login'; };

  const panic = async () => {
    try { const r = await api.post('/ims/panic'); setPanicMsg(`P1 incident #${r.data.id} raised. Help is on the way.`); }
    catch { setPanicMsg('Failed to raise alert — call control room.'); }
    finally { setConfirming(false); }
  };

  return (
    <div className="min-h-screen bg-gray-100 max-w-md mx-auto">
      <header className="bg-blue-900 text-white p-4 flex justify-between items-center">
        <div>
          <div className="font-bold">NCRTC Driver</div>
          <div className="text-xs text-blue-200">{user?.full_name}</div>
        </div>
        <button onClick={logout} className="text-xs bg-red-600 px-3 py-1 rounded">Logout</button>
      </header>

      <div className="p-4 space-y-4">
        <section className="bg-white rounded-lg shadow p-4">
          <h2 className="font-semibold mb-2">Today's Duty</h2>
          {duty ? (
            <>
              <div className="text-sm space-y-1">
                <Row label="Vehicle" value={duty.bus_number} />
                <Row label="Route" value={duty.route_name} />
                <Row label="Start" value={new Date(duty.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} />
                <Row label="Status" value={duty.status} />
              </div>
              {duty.status === 'acknowledged' ? (
                <div className="mt-3 text-green-700 text-sm font-medium">✓ Acknowledged {duty.ack_at ? `at ${new Date(duty.ack_at).toLocaleTimeString()}` : ''}</div>
              ) : (
                <button onClick={acknowledge} className="mt-3 w-full bg-green-600 text-white py-2 rounded font-medium">
                  Acknowledge duty
                </button>
              )}
            </>
          ) : <p className="text-sm text-gray-500">No duty assigned for today.</p>}
        </section>

        <section className="bg-white rounded-lg shadow p-4">
          <h2 className="font-semibold mb-2">Notices</h2>
          {notices.length === 0 && <p className="text-sm text-gray-500">No notices.</p>}
          {notices.map((n) => (
            <div key={n.id} className={`py-2 border-b last:border-0 ${!n.read ? 'font-medium' : ''}`} onClick={() => !n.read && markRead(n.id)}>
              <div className="flex justify-between text-sm">
                <span>{n.title}</span>
                {!n.read && <span className="text-blue-600 text-xs">tap to read</span>}
              </div>
              <p className="text-xs text-gray-600">{n.content}</p>
            </div>
          ))}
        </section>

        <section className="bg-white rounded-lg shadow p-4">
          <h2 className="font-semibold mb-2 text-red-700">Emergency</h2>
          {panicMsg ? (
            <p className="text-sm text-red-700">{panicMsg}</p>
          ) : confirming ? (
            <div className="flex gap-2">
              <button onClick={panic} className="flex-1 bg-red-600 text-white py-3 rounded font-bold">CONFIRM PANIC</button>
              <button onClick={() => setConfirming(false)} className="flex-1 bg-gray-200 py-3 rounded">Cancel</button>
            </div>
          ) : (
            <button onClick={() => setConfirming(true)} className="w-full bg-red-600 text-white py-4 rounded-lg text-lg font-bold shadow">
              🚨 PANIC
            </button>
          )}
          <p className="text-xs text-gray-400 mt-2">Raises a P1 incident for your vehicle and alerts the control room.</p>
        </section>
      </div>
    </div>
  );
}

const Row = ({ label, value }) => (
  <div className="flex justify-between"><span className="text-gray-500">{label}</span><span className="font-medium">{value}</span></div>
);
