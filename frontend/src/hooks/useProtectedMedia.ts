import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiBlob, getClinicContext } from "../api/client";

export function useProtectedMediaState(path: string | null) {
  const clinic = getClinicContext() ?? "legacy";
  const media = useQuery({
    queryKey: [clinic, "protected-media", path],
    queryFn: () => apiBlob(path!),
    enabled: Boolean(path),
    // Share an in-flight download, but do not keep clinical files in the cache
    // after the last viewer disappears.
    gcTime: 0,
    retry: false,
  });
  const [state, setState] = useState<{
    path: string;
    clinic: string;
    url: string | null;
    failed: boolean;
  } | null>(null);
  useEffect(() => {
    if (!path || !media.data) return;
    const objectUrl = URL.createObjectURL(media.data);
    // An object URL is an external browser resource and must be created and
    // revoked by the same effect, including StrictMode's cleanup cycle.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState({ path, clinic, url: objectUrl, failed: false });
    return () => URL.revokeObjectURL(objectUrl);
  }, [path, clinic, media.data]);
  if (path && media.isError) return { path, url: null, failed: true };
  return state?.path === path && state.clinic === clinic ? state : null;
}

export function useProtectedMedia(path: string | null) {
  return useProtectedMediaState(path)?.url ?? null;
}
