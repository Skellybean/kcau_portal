import { useFocusEffect } from "@react-navigation/native";
import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "./api";

// Loads a GET endpoint, reloads when the screen regains focus, and supports pull to refresh.
export function useResource(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [refreshing, setRefreshing] = useState(false);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const load = useCallback(
    async (pulled = false) => {
      if (pulled) setRefreshing(true);
      try {
        const data = await api.get(path);
        if (alive.current) setState({ data, error: null, loading: false });
      } catch (error) {
        if (alive.current) setState((s) => ({ data: s.data, error: error.message, loading: false }));
      } finally {
        if (alive.current) setRefreshing(false);
      }
    },
    [path]
  );

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load])
  );

  return { ...state, refreshing, refresh: () => load(true), reload: load };
}
