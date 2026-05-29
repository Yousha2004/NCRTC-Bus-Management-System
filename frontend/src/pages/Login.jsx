import { useState } from 'react';
import api from '../lib/api';

const DEMO = [
  ['admin', 'admin123', 'Admin'],
  ['operator1', 'op123', 'Control operator'],
  ['manager1', 'mgr123', 'Depot manager'],
  ['driver1', 'dr123', 'Driver'],
  ['conductor1', 'co123', 'Conductor'],
];

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const doLogin = async (u, p) => {
    setError('');
    try {
      const form = new FormData();
      form.append('username', u);
      form.append('password', p);
      const res = await api.post('/auth/login', form);
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('role', res.data.role);
      const me = await api.get('/auth/me');
      localStorage.setItem('user', JSON.stringify(me.data));
      // drivers/conductors land on the mobile driver app
      window.location.href = ['driver', 'conductor'].includes(res.data.role) ? '/driver' : '/';
    } catch {
      setError('Login failed — check username and password.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-1 text-center text-blue-900">NCRTC Login</h2>
        <p className="text-center text-gray-500 mb-6 text-sm">Bus Management System</p>
        <form onSubmit={(e) => { e.preventDefault(); doLogin(username, password); }}>
          <label className="block mb-2 text-sm font-medium">Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)}
                 className="w-full p-2 border rounded mb-4" required />
          <label className="block mb-2 text-sm font-medium">Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                 className="w-full p-2 border rounded mb-4" required />
          {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
          <button type="submit" className="w-full bg-blue-900 text-white p-2 rounded hover:bg-blue-800">
            Sign In
          </button>
        </form>
        <div className="mt-6 border-t pt-4">
          <p className="text-xs text-gray-500 mb-2">Demo accounts (click to sign in):</p>
          <div className="grid grid-cols-1 gap-1">
            {DEMO.map(([u, p, label]) => (
              <button key={u} onClick={() => doLogin(u, p)}
                      className="text-left text-xs px-2 py-1 rounded hover:bg-gray-100 flex justify-between">
                <span className="font-medium">{label}</span>
                <span className="text-gray-400">{u} / {p}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
