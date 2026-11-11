import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

export function useAdmin<T>(path: string) {
  return useQuery<T, Error>({
    queryKey: ["backoffice", path],
    queryFn: () => api<T>(`backoffice/${path}`),
    retry: false,
  });
}
