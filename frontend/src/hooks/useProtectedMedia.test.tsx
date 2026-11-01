import { StrictMode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { apiBlob } from "../api/client";
import { useProtectedMedia } from "./useProtectedMedia";

vi.mock("../api/client", () => ({ apiBlob: vi.fn() }));
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

it("shares an in-flight protected file request in StrictMode and revokes object URLs", async () => {
  const create = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:test");
  const revoke = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
  vi.mocked(apiBlob).mockResolvedValue(new Blob(["synthetic"]));
  function Viewer() { const url = useProtectedMedia("clinical-images/1/file/"); return <span>{url}</span>; }
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const view = render(<StrictMode><QueryClientProvider client={client}><Viewer /><Viewer /></QueryClientProvider></StrictMode>);
  expect(await screen.findAllByText("blob:test")).toHaveLength(2);
  expect(apiBlob).toHaveBeenCalledTimes(1);
  view.unmount();
  expect(revoke).toHaveBeenCalledTimes(create.mock.calls.length);
  client.clear();
});
