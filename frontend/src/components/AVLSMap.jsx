import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import axios from 'axios';
import L from 'leaflet';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const busIcon = new L.Icon({
    iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png',
    iconSize: [32, 32],
});

export default function AVLSMap() {
  const [buses, setBuses] = useState([]);
  const fetchBuses = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/avls/live`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBuses(res.data);
    } catch (err) {
      console.error(err);
    }
  };
  useEffect(() => {
    fetchBuses();
    const interval = setInterval(fetchBuses, 5000);
    return () => clearInterval(interval);
  }, []);
  return (
    <div className="h-full w-full">
      <MapContainer center={[28.61, 77.20]} zoom={10} style={{ height: '100%', width: '100%' }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {buses.map((bus) => (
          bus.location && (
            <Marker key={bus.id} position={[bus.location.coordinates[1], bus.location.coordinates[0]]} icon={busIcon}>
              <Popup>
                <div>
                  <h3 className="font-bold">{bus.bus_number}</h3>
                  <p>{bus.model}</p>
                </div>
              </Popup>
            </Marker>
          )
        ))}
      </MapContainer>
    </div>
  );
}
