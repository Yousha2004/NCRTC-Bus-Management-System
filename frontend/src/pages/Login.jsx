import { useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    try {
      const res = await axios.post(`${API_URL}/auth/login`, formData);
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('role', res.data.role);
      window.location.href = '/';
    } catch (err) {
      alert('Login failed');
    }
  };
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleLogin} className="bg-white p-8 rounded shadow-md w-96">
        <h2 className="text-2xl font-bold mb-6 text-center">NCRTC Login</h2>
        <div className="mb-4">
          <label htmlFor="username" className="block mb-2">Username</label>
          <input id="username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} className="w-full p-2 border rounded" required />
        </div>
        <div className="mb-6">
          <label htmlFor="password" className="block mb-2">Password</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full p-2 border rounded" required />
        </div>
        <button type="submit" className="w-full bg-blue-900 text-white p-2 rounded hover:bg-blue-800">Sign In</button>
      </form>
    </div>
  );
}
