import * as SecureStore from "expo-secure-store";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api, setToken, setUnauthorizedHandler } from "../api";

const TOKEN_KEY = "kca.virtualcampus.token";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [state, setState] = useState({ status: "loading", user: null });

  const clearSession = useCallback(async () => {
    setToken(null);
    try {
      await SecureStore.deleteItemAsync(TOKEN_KEY);
    } catch (error) {
      // Nothing to clear.
    }
    setState({ status: "signedOut", user: null });
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearSession();
    });
    (async () => {
      try {
        const saved = await SecureStore.getItemAsync(TOKEN_KEY);
        if (!saved) {
          setState({ status: "signedOut", user: null });
          return;
        }
        setToken(saved);
        const user = await api.get("/auth/me/");
        setState({ status: "signedIn", user });
      } catch (error) {
        // A rejected token is cleared by the 401 handler. Offline starts keep the saved token.
        setToken(null);
        setState({ status: "signedOut", user: null });
      }
    })();
  }, [clearSession]);

  const signIn = useCallback(async ({ token, user }) => {
    setToken(token);
    try {
      await SecureStore.setItemAsync(TOKEN_KEY, token);
    } catch (error) {
      // The session still works until the app closes.
    }
    setState({ status: "signedIn", user });
  }, []);

  const signOut = useCallback(async () => {
    try {
      await api.post("/auth/logout/");
    } catch (error) {
      // Signing out locally is enough if the server cannot be reached.
    }
    await clearSession();
  }, [clearSession]);

  const updateUser = useCallback((user) => setState((s) => ({ ...s, user })), []);

  const value = useMemo(() => ({ ...state, signIn, signOut, updateUser }), [state, signIn, signOut, updateUser]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
