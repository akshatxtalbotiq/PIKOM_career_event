"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";

const directoryLists = ["employers", "jobs", "universities", "training_providers", "sessions", "interview_slots", "floor_maps"];

export default function useAttendeeData() {
  const [me, setMe] = useState(null);
  const [data, setData] = useState(null);
  const [schedule, setSchedule] = useState(null);
  const [checkin, setCheckin] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [page, setPage] = useState(1);
  const [loadingMore, setLoadingMore] = useState(false);

  async function load() {
    try {
      const profile = await api("me/");
      setMe(profile);
      const directory = await api(`events/${profile.event.id}/directory/?page=1`);
      setData(directory);
      setPage(1);
      setSchedule(await api("me/schedule/"));
      setCheckin(await api("me/check-in/"));
      setError("");
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function loadMore() {
    if (!data || loadingMore) return;
    setLoadingMore(true);
    try {
      const nextPage = page + 1;
      const next = await api(`events/${me.event.id}/directory/?page=${nextPage}`);
      setData((current) => ({
        ...next,
        ...Object.fromEntries(directoryLists.map((key) => [key, [...(current?.[key] || []), ...(next[key] || [])]])),
      }));
      setPage(nextPage);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoadingMore(false);
    }
  }

  async function action(path, method = "POST", body) {
    setBusy(true);
    setError("");
    try {
      await api(path, { method, body });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return { me, data, schedule, checkin, error, busy, loadingMore, loadMore, action };
}
