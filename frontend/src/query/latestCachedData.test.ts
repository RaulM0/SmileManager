import { QueryClient } from "@tanstack/react-query";
import { expect, it } from "vitest";
import { latestCachedData } from "./latestCachedData";
import { queryKeys } from "./keys";

it("preserves the last successful appointment list when another filter fails", () => {
  const client = new QueryClient();
  client.setQueryData(queryKeys.appointmentList("P", ""), [{ id: 1 }]);
  const last = latestCachedData<Array<{ id: number }>>(client, [
    ...queryKeys.appointments,
    "list",
  ]);
  expect(last).toEqual([{ id: 1 }]);
  expect(
    latestCachedData(client, [...queryKeys.diagnostics, "list"]),
  ).toBeUndefined();
  client.clear();
  expect(
    latestCachedData(client, [...queryKeys.appointments, "list"]),
  ).toBeUndefined();
});
