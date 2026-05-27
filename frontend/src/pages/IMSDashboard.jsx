import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function IMSDashboard() {
  const [incidents, setIncidents] = useState([]);
  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await axios.get(`${API_URL}/ims/`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setIncidents(res.data);
      } catch (err) { console.error(err); }
    };
    fetch();
  }, []);
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">IMS</h2>
      {incidents.map(i => <div key={i.id} className="border p-4 mb-2">{i.description}</div>)}
    </div>
  );
}
