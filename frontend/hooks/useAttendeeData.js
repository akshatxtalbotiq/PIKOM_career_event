"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "../lib/api";

const directoryLists = [
  "employers",
  "jobs",
  "universities",
  "training_providers",
  "sessions",
  "interview_slots",
  "floor_maps",
];

// Persistent client-side session cache across route transitions
let globalCache = {
  me: null,
  data: null,
  schedule: null,
  checkin: null,
  error: "",
  page: 1,
  loaded: false,
};

let activeLoadPromise = null;
const subscribers = new Set();

function notifySubscribers() {
  subscribers.forEach((callback) => {
    try {
      callback({ ...globalCache });
    } catch (e) {
      // ignore
    }
  });
}

export function resetAttendeeCache() {
  globalCache = {
    me: null,
    data: null,
    schedule: null,
    checkin: null,
    error: "",
    page: 1,
    loaded: false,
  };
  activeLoadPromise = null;
  notifySubscribers();
}

async function fetchAttendeeData(force = false) {
  if (activeLoadPromise && !force) {
    return activeLoadPromise;
  }

  activeLoadPromise = (async () => {
    try {
      const profile = await api("me/");
      globalCache.me = profile;

      // Parallelize requests for lightning-fast loading
      const [directory, schedule, checkin] = await Promise.all([
        api(`events/${profile.event.id}/directory/?page=1`),
        api("me/schedule/"),
        api("me/check-in/"),
      ]);

      globalCache.data = directory;
      globalCache.schedule = schedule;
      globalCache.checkin = checkin;
      globalCache.page = 1;
      globalCache.error = "";
      globalCache.loaded = true;
    } catch (e) {
      globalCache.error = e.message;
      if (!globalCache.me) {
        globalCache.loaded = false;
      }
    } finally {
      activeLoadPromise = null;
      notifySubscribers();
    }
  })();

  return activeLoadPromise;
}

export default function useAttendeeData() {
  // Synchronously initialize with cached data to prevent flash of loading screen
  const [state, setState] = useState(() => ({ ...globalCache }));
  const [busy, setBusy] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    const handleUpdate = (updated) => setState(updated);
    subscribers.add(handleUpdate);

    // Initial load if not already populated
    if (!globalCache.loaded && !activeLoadPromise) {
      fetchAttendeeData();
    }

    return () => {
      subscribers.delete(handleUpdate);
    };
  }, []);

  const loadMore = useCallback(async () => {
    if (!globalCache.data || !globalCache.me || loadingMore) return;
    setLoadingMore(true);
    try {
      const nextPage = globalCache.page + 1;
      const next = await api(`events/${globalCache.me.event.id}/directory/?page=${nextPage}`);
      globalCache.data = {
        ...next,
        ...Object.fromEntries(
          directoryLists.map((key) => [
            key,
            [...(globalCache.data?.[key] || []), ...(next[key] || [])],
          ])
        ),
      };
      globalCache.page = nextPage;
      notifySubscribers();
    } catch (e) {
      globalCache.error = e.message;
      notifySubscribers();
    } finally {
      setLoadingMore(false);
    }
  }, [loadingMore]);

  const action = useCallback(async (path, method = "POST", body) => {
    setBusy(true);
    try {
      await api(path, { method, body });
      await fetchAttendeeData(true);
    } catch (e) {
      globalCache.error = e.message;
      notifySubscribers();
    } finally {
      setBusy(false);
    }
  }, []);

  return {
    me: state.me,
    data: state.data,
    schedule: state.schedule,
    checkin: state.checkin,
    error: state.error,
    busy,
    loadingMore,
    loadMore,
    action,
  };
}

