import { create } from "zustand";

// The access token lives in memory only; the refresh token is an httpOnly cookie the browser holds.
export const useAuthStore = create((set) => ({
  accessToken: null,
  user: null,
  // idle: not checked yet, loading: bootstrap in flight, authenticated, anonymous
  status: "idle",
  setSession: ({ access_token, user }) =>
    set({ accessToken: access_token, user, status: "authenticated" }),
  setUser: (user) => set({ user }),
  setStatus: (status) => set({ status }),
  clear: () => set({ accessToken: null, user: null, status: "anonymous" }),
}));
