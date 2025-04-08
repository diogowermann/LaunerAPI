// frontend/src/components/Login.js
import React, { useState } from 'react';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/login', { username, password });
      const expiresAt = new Date().getTime() + 30 * 60 * 1000; // 30 minutes in milliseconds
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('expires_at', expiresAt);
      navigate('/dashboard');
    } catch (err) {
      console.error('Login error:', err);
      setError('Credenciais inválidas. Tente novamente.');
    }
  };

  return (
    <div className='container'>
      {error && <p style={{color: 'red'}}>{error}</p>}

      <div className="container mt-5" style={{ maxWidth: '300px', padding: '200px 0' }}>
        <form onSubmit={handleLogin} className="card p-4 bg-dark shadow">
          <input 
            className="form-control mb-3" 
            type="text" value={username} 
            onChange={(e) => setUsername(e.target.value)} 
            required 
            placeholder="Usuário (Protheus)" 
            style={{boxShadow: '4px 0px 0px #eb8220'}} 
          />
          <input 
            className="form-control mb-3" 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            required 
            placeholder="Senha" 
            style={{boxShadow: '4px 0px 0px #eb8220'}} />
          
          <button className="login-button" type="submit">Entrar</button>
        </form>
      </div>

    </div>
  );
};

export default Login;
