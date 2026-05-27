import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function CMSDashboard() {
  const [notices, setNotices] = useState([]);
  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await axios.get(`${API_URL}/cms/`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setNotices(res.data);
      } catch (err) { console.error(err); }
    };
    fetch();
  }, []);
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">CMS</h2>
      {notices.map(n => <div key={n.id} className="border p-4 mb-2"><h3>{n.title}</h3><p>{n.content}</p></div>)}
    </div>
  );
}
