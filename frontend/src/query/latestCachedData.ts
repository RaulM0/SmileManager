import type { QueryClient, QueryKey } from "@tanstack/react-query";

/** Return the most recently successful response for a family of list filters. */
export function latestCachedData<T>(client: QueryClient, prefix: QueryKey): T | undefined {
  let latest: T | undefined;
  let updatedAt = 0;
  for (const [key, data] of client.getQueriesData<T>({ queryKey: prefix })) {
    const timestamp = client.getQueryState(key)?.dataUpdatedAt ?? 0;
    if (data !== undefined && timestamp >= updatedAt) {
      latest = data;
      updatedAt = timestamp;
    }
  }
  return latest;
}
