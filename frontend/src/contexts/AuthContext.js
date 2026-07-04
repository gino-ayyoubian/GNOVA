import React, { createContext, useState, useContext, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Auth token is stored in a secure httpOnly cookie set by the backend.
// All requests send credentials so the cookie is included automatically.
const authAxios = axios.create({
  baseURL: API,
  withCredentials: true,
});

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
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const response = await authAxios.get('/auth/me');
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback(async (telegramId) => {
    try {
      await authAxios.post('/auth/login', {
        telegram_id: parseInt(telegramId, 10),
      });
      await fetchUser();
      return { success: true };
    } catch (error) {
      // Try to register if login fails
      try {
        await authAxios.post('/auth/register', {
          telegram_id: parseInt(telegramId, 10),
          username: `user_${telegramId}`,
        });
        await fetchUser();
        return { success: true };
      } catch (registerError) {
        return {
          success: false,
          error: registerError.response?.data?.detail || 'خطا در ورود',
        };
      }
    }
  }, [fetchUser]);

  const logout = useCallback(async () => {
    try {
      await authAxios.post('/auth/logout');
    } catch (error) {
      // Ignore network errors on logout; clear local state regardless
    }
    setUser(null);
  }, []);

  const apiCall = useCallback(async (method, endpoint, data = null) => {
    const config = { method, url: endpoint };
    if (data) {
      config.data = data;
    }
    return authAxios(config);
  }, []);

  const contextValue = useMemo(
    () => ({ user, loading, login, logout, apiCall, refetch: fetchUser }),
    [user, loading, login, logout, apiCall, fetchUser]
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};
