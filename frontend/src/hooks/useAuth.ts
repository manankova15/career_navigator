import { useState, useEffect } from "react";
import { getMe, MeResponse, clearAuth } from "../api/auth";
import { getToken } from "../api/client";

export function useAuth() {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) { setLoading(false); return; }
    getMe()
      .then(setUser)
      .catch(() => { clearAuth(); setUser(null); })
      .finally(() => setLoading(false));
  }, []);

  function logout() { clearAuth(); setUser(null); }

  return { user, setUser, logout, loading };
}
