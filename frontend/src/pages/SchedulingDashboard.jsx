import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function SchedulingDashboard() {
  const [schedules, setSchedules] = useState([]);
  useEffect(() => {
    const fetchSchedules = async () => {
      try {
        const res = await axios.get(`${API_URL}/scheduling/`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        setSchedules(res.data);
      } catch (err) { console.error(err); }
    };
    fetchSchedules();
  }, []);
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Scheduling</h2>
      <table className="min-w-full bg-white">
        <thead><tr><th>Bus</th><th>Route</th><th>Departure</th></tr></thead>
        <tbody>
          {schedules.map(s => <tr key={s.id}><td>{s.bus_number}</td><td>{s.route_name}</td><td>{s.departure_time}</td></tr>)}
        </tbody>
      </table>
    </div>
  );
}
