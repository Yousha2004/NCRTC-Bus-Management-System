import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import AVLSMap from './components/AVLSMap';
import HistoryPage from './pages/HistoryPage';
import SchedulingDashboard from './pages/SchedulingDashboard';
import IMSDashboard from './pages/IMSDashboard';
import IncidentDetail from './pages/IncidentDetail';
import CMSDashboard from './pages/CMSDashboard';
import DriverApp from './pages/DriverApp';
import Login from './pages/Login';
import { getRole, getUser } from './lib/api';

const NAV = [
  { to: '/', label: 'AVLS (Map)' },
  { to: '/history', label: 'History' },
  { to: '/scheduling', label: 'Scheduling' },
  { to: '/ims', label: 'IMS' },
  { to: '/cms', label: 'CMS' },
];

const Layout = ({ children }) => {
  const role = getRole();
  const user = getUser();
  const loc = useLocation();
  const logout = () => { localStorage.clear(); window.location.href = '/login'; };
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-blue-900 text-white px-4 py-3 flex justify-between items-center flex-wrap gap-2">
        <h1 className="text-lg font-bold">NCRTC Bus Management</h1>
        <nav className="flex items-center gap-1 text-sm flex-wrap">
          {NAV.map((n) => (
            <Link key={n.to} to={n.to}
                  className={`px-3 py-1 rounded ${loc.pathname === n.to ? 'bg-blue-700' : 'hover:bg-blue-800'}`}>
              {n.label}
            </Link>
          ))}
          <span className="ml-2 text-blue-200 text-xs">
            {user?.full_name || role} · {user?.depot_name || (role === 'admin' || role === 'control_operator' ? 'All depots' : '')}
          </span>
          <button onClick={logout} className="bg-red-600 px-3 py-1 rounded ml-2 hover:bg-red-500">Logout</button>
        </nav>
      </header>
      <main className="flex-1 relative">{children}</main>
    </div>
  );
};

const PrivateRoute = ({ children }) =>
  localStorage.getItem('token') ? <Layout>{children}</Layout> : <Navigate to="/login" />;

// driver app has its own minimal mobile chrome (no desktop nav)
const DriverRoute = ({ children }) =>
  localStorage.getItem('token') ? children : <Navigate to="/login" />;

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/driver" element={<DriverRoute><DriverApp /></DriverRoute>} />
        <Route path="/" element={<PrivateRoute><AVLSMap /></PrivateRoute>} />
        <Route path="/history" element={<PrivateRoute><HistoryPage /></PrivateRoute>} />
        <Route path="/scheduling" element={<PrivateRoute><SchedulingDashboard /></PrivateRoute>} />
        <Route path="/ims" element={<PrivateRoute><IMSDashboard /></PrivateRoute>} />
        <Route path="/ims/:id" element={<PrivateRoute><IncidentDetail /></PrivateRoute>} />
        <Route path="/cms" element={<PrivateRoute><CMSDashboard /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}
