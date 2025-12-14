import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import api from '../services/api';

interface User {
  id: string;
  username: string;
  email?: string;
  full_name?: string;
  role: string;
  profile_picture_url?: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        try {
          const response = await api.post('/auth/login', { username, password });
          const { access_token, refresh_token } = response.data;
          
          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
          });
          
          // Get user info including role
          const userResponse = await api.get('/auth/me', {
            headers: { Authorization: `Bearer ${access_token}` },
          });
          
          set({ user: userResponse.data });
        } catch (error) {
          throw error;
        }
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      setTokens: (accessToken: string, refreshToken: string) => {
        set({
          accessToken,
          refreshToken,
          isAuthenticated: true,
        });
      },

      setUser: (user: User) => {
        set({ user });
      }
    }),
    {
      name: 'auth-storage',
    }
  )
);
