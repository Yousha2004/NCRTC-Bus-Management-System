import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import AVLSMap from './components/AVLSMap';
import SchedulingDashboard from './pages/SchedulingDashboard';
import IMSDashboard from './pages/IMSDashboard';
import CMSDashboard from './pages/CMSDashboard';
import Login from './pages/Login';

const Layout = ({ children }) => {
  const role = localStorage.getItem('role');
  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/login';
  };
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-blue-900 text-white p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">NCRTC Bus Management</h1>
        <nav className="space-x-4">
          <Link to="/" className="hover:underline">AVLS (Map)</Link>
          <Link to="/scheduling" className="hover:underline">Scheduling</Link>
          <Link to="/ims" className="hover:underline">IMS</Link>
          <Link to="/cms" className="hover:underline">CMS</Link>
          <button onClick={handleLogout} className="bg-red-600 px-3 py-1 rounded">Logout ({role})</button>
        </nav>
      </header>
      <main className="flex-1 overflow-hidden relative">
        {children}
      </main>
    </div>
  );
};

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? <Layout>{children}</Layout> : <Navigate to="/login" />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><AVLSMap /></PrivateRoute>} />
        <Route path="/scheduling" element={<PrivateRoute><SchedulingDashboard /></PrivateRoute>} />
        <Route path="/ims" element={<PrivateRoute><IMSDashboard /></PrivateRoute>} />
        <Route path="/cms" element={<PrivateRoute><CMSDashboard /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;
