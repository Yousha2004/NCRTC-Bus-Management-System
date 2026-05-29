import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api, { getRole } from '../lib/api';

const STATUSES = ['open', 'acknowledged', 'in_progress', 'resolved', 'closed'];

export default function IncidentDetail() {
  const { id } = useParams();
  const role = getRole();
  const canAssign = ['admin', 'control_operator', 'depot_manager'].includes(role);
  const [inc, setInc] = useState(null);
  const [newStatus, setNewStatus] = useState('');
  const [note, setNote] = useState('');
  const [assignees, setAssignees] = useState([]);
  const [assignee, setAssignee] = useState('');
  const [msg, setMsg] = useState('');

  const load = () => api.get(`/ims/${id}`).then((r) => { setInc(r.data); setNewStatus(r.data.status); }).catch(() => {});
  useEffect(() => { load(); }, [id]);
  useEffect(() => { if (canAssign) api.get('/scheduling/drivers').then((r) => setAssignees(r.data)).catch(() => {}); }, [canAssign]);

  const changeStatus = async (e) => {
    e.preventDefault();
    setMsg('');
    try { await api.post(`/ims/${id}/status`, { status: newStatus, note }); setNote(''); load(); }
    catch (e) { setMsg(e.response?.data?.detail || 'Failed'); }
  };
  const doAssign = async () => {
    if (!assignee) return;
    try { await api.post(`/ims/${id}/assign`, { assigned_to: Number(assignee) }); load(); }
    catch (e) { setMsg(e.response?.data?.detail || 'Failed'); }
  };

  if (!inc) return <div className="p-4">Loading…</div>;

  return (
    <div className="p-4 max-w-3xl">
      <Link to="/ims" className="text-blue-700 text-sm">‹ Back to incidents</Link>
      <h2 className="text-2xl font-bold mt-2 mb-1">Incident #{inc.id}</h2>
      <p className="text-gray-600 mb-4">{inc.description}</p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6 text-sm">
        <Info label="Type" value={inc.type} />
        <Info label="Severity" value={inc.severity} />
        <Info label="Status" value={inc.status} />
        <Info label="Vehicle" value={inc.bus_number || '—'} />
        <Info label="Raised by" value={inc.raised_by || '—'} />
        <Info label="Assigned to" value={inc.assigned_to || '—'} />
      </div>

      <div className="bg-white rounded shadow p-4 mb-6">
        <h3 className="font-semibold mb-3">Timeline</h3>
        <ol className="border-l-2 border-gray-200 pl-4 space-y-3">
          {inc.events?.map((e, i) => (
            <li key={i} className="text-sm">
              <div className="text-gray-800">
                {e.from_status ? <span>{e.from_status} → </span> : null}<b>{e.to_status}</b>
              </div>
              <div className="text-gray-600">{e.note}</div>
              <div className="text-xs text-gray-400">{e.actor || 'system'} · {new Date(e.ts).toLocaleString()}</div>
            </li>
          ))}
        </ol>
      </div>

      <div className="bg-white rounded shadow p-4 mb-4">
        <h3 className="font-semibold mb-3">Update status</h3>
        <form onSubmit={changeStatus} className="flex flex-wrap gap-3 items-end text-sm">
          <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)} className="border rounded p-2">
            {STATUSES.map((s) => <option key={s}>{s}</option>)}
          </select>
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="Note (required)" required
                 className="border rounded p-2 flex-1 min-w-[200px]" />
          <button className="bg-blue-900 text-white px-4 py-2 rounded hover:bg-blue-800">Save</button>
        </form>
      </div>

      {canAssign && (
        <div className="bg-white rounded shadow p-4">
          <h3 className="font-semibold mb-3">Assign</h3>
          <div className="flex gap-3 items-end text-sm">
            <select value={assignee} onChange={(e) => setAssignee(e.target.value)} className="border rounded p-2">
              <option value="">Select user…</option>
              {assignees.map((a) => <option key={a.id} value={a.id}>{a.full_name}</option>)}
            </select>
            <button onClick={doAssign} className="bg-gray-800 text-white px-4 py-2 rounded hover:bg-gray-700">Assign</button>
          </div>
        </div>
      )}
      {msg && <p className="text-red-600 text-sm mt-3">{msg}</p>}
    </div>
  );
}

const Info = ({ label, value }) => (
  <div className="bg-white rounded shadow p-3">
    <div className="text-xs text-gray-400">{label}</div>
    <div className="font-medium">{value}</div>
  </div>
);
