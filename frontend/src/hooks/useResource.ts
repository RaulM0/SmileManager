import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { queryKeys } from "../query/keys";

/** A URL is the cache identity; changing record IDs cannot reveal the previous record. */
export function useResource<T>(path: string) {
  const query = useQuery<T, Error>({
    queryKey: queryKeys.resource(path),
    queryFn: () => api<T>(path),
  });
  return {
    data: query.data ?? null,
    error: query.error?.message ?? null,
    loading: query.isPending,
    reload: () => {
      void query.refetch();
    },
  };
}
