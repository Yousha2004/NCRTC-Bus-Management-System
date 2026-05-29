import { useEffect, useState } from 'react';
import api, { getRole } from '../lib/api';

export default function CMSDashboard() {
  const role = getRole();
  const canCreate = ['admin', 'control_operator', 'depot_manager'].includes(role);
  const canSeeReceipts = canCreate;
  const [notices, setNotices] = useState([]);
  const [receipts, setReceipts] = useState(null);
  const [msg, setMsg] = useState('');

  const load = () => api.get('/cms/').then((r) => setNotices(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const markRead = async (id) => { await api.post(`/cms/${id}/read`); load(); };
  const showReceipts = async (id) => {
    try { const r = await api.get(`/cms/${id}/receipts`); setReceipts(r.data); }
    catch (e) { setMsg(e.response?.data?.detail || 'Failed'); }
  };

  return (
    <div className="p-4 max-w-3xl">
      <h2 className="text-2xl font-bold mb-4">Notices (CMS)</h2>

      {notices.map((n) => (
        <div key={n.id} className={`border rounded p-4 mb-3 bg-white ${!n.read ? 'border-l-4 border-l-blue-600' : ''}`}>
          <div className="flex justify-between items-start">
            <h3 className="font-semibold">{n.title} {!n.read && <span className="text-xs text-blue-600">● unread</span>}</h3>
            <span className="text-xs text-gray-400">{n.audience}</span>
          </div>
          <p className="text-gray-700 text-sm mt-1">{n.content}</p>
          <div className="text-xs text-gray-400 mt-2">{new Date(n.publish_at || n.created_at).toLocaleString()}</div>
          <div className="flex gap-3 mt-2">
            {!n.read && <button onClick={() => markRead(n.id)} className="text-xs text-blue-700">Mark read</button>}
            {canSeeReceipts && <button onClick={() => showReceipts(n.id)} className="text-xs text-gray-600">Read receipts</button>}
          </div>
        </div>
      ))}
      {notices.length === 0 && <p className="text-gray-500">No notices.</p>}

      {canCreate && <CreateForm onDone={load} setMsg={setMsg} />}
      {msg && <p className="text-blue-700 text-sm mt-3">{msg}</p>}

      {receipts && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-[2000] p-4" onClick={() => setReceipts(null)}>
          <div className="bg-white rounded shadow-lg p-5 w-full max-w-md max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between mb-2">
              <h3 className="font-semibold">Read receipts — {receipts.title}</h3>
              <button onClick={() => setReceipts(null)}>✕</button>
            </div>
            <p className="text-sm text-gray-500 mb-3">{receipts.read_count} of {receipts.total} read</p>
            <ul className="text-sm divide-y">
              {receipts.receipts.map((r) => (
                <li key={r.user_id} className="py-1 flex justify-between">
                  <span>{r.full_name}</span>
                  <span className={r.read ? 'text-green-600' : 'text-gray-400'}>{r.read ? '✓ read' : 'unread'}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

function CreateForm({ onDone, setMsg }) {
  const [f, setF] = useState({ title: '', content: '', audience: 'all' });
  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/cms/', f);
      setMsg('Notice published.');
      setF({ title: '', content: '', audience: 'all' });
      onDone();
    } catch (e) { setMsg(e.response?.data?.detail || 'Failed'); }
  };
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  return (
    <form onSubmit={submit} className="bg-white rounded shadow p-4 mt-6 text-sm">
      <h3 className="font-semibold mb-3">Publish a notice</h3>
      <input value={f.title} onChange={set('title')} placeholder="Title" required className="border rounded p-2 w-full mb-2" />
      <textarea value={f.content} onChange={set('content')} placeholder="Body" required className="border rounded p-2 w-full mb-2" rows={3} />
      <div className="flex gap-3 items-end">
        <div><label className="block text-xs mb-1">Audience</label>
          <select value={f.audience} onChange={set('audience')} className="border rounded p-2">
            <option value="all">All</option>
            <option value="role:driver">All drivers</option>
            <option value="role:conductor">All conductors</option>
          </select></div>
        <button className="bg-blue-900 text-white px-4 py-2 rounded hover:bg-blue-800">Publish</button>
      </div>
    </form>
  );
}
