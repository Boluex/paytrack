import { createContext, useContext, useState, useEffect } from 'react';
import client from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('paytrack_token');
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const res = await client.get('/auth/me');
      setUser(res.data);
    } catch {
      localStorage.removeItem('paytrack_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const res = await client.post('/auth/login', { email, password });
    localStorage.setItem('paytrack_token', res.data.access_token);
    await fetchUser();
    return res.data;
  };

  const register = async (email, password, businessName) => {
    const res = await client.post('/auth/register', {
      email, password, business_name: businessName,
    });
    localStorage.setItem('paytrack_token', res.data.access_token);
    await fetchUser();
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('paytrack_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAuthenticated: !!user, refreshUser: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
