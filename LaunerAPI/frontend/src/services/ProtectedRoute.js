import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
    const token = localStorage.getItem('access_token');
    const expiresAt = localStorage.getItem('expires_at');
    const isExpired = new Date().getTime() > parseInt(expiresAt, 10);

    if (!token || isExpired) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('expires_at');
        return <Navigate to="/" replace />; // Redirect to login page
    }

    return children;
};

export default ProtectedRoute;