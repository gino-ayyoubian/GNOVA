import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('gnova_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (telegramId) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        telegram_id: parseInt(telegramId)
      });
      const newToken = response.data.token;
      setToken(newToken);
      localStorage.setItem('gnova_token', newToken);
      return { success: true };
    } catch (error) {
      // Try to register if login fails
      try {
        const registerResponse = await axios.post(`${API}/auth/register`, {
          telegram_id: parseInt(telegramId),
          username: `user_${telegramId}`
        });
        const newToken = registerResponse.data.token;
        setToken(newToken);
        localStorage.setItem('gnova_token', newToken);
        return { success: true };
      } catch (registerError) {
        return { 
          success: false, 
          error: registerError.response?.data?.detail || 'خطا در ورود' 
        };
      }
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('gnova_token');
  };

  const apiCall = async (method, endpoint, data = null) => {
    const config = {
      method,
      url: `${API}${endpoint}`,
      headers: { Authorization: `Bearer ${token}` },
    };
    if (data) {
      config.data = data;
    }
    return axios(config);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, apiCall, refetch: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
};
