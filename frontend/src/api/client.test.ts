import { afterEach, expect, it, vi } from "vitest";
import { api, getAccessToken, setAccessToken } from "./client";

afterEach(() => {
  setAccessToken(null);
  vi.unstubAllGlobals();
});

it("sends the JWT in the Authorization header for API requests", async () => {
  setAccessToken("access-one");
  const fetchMock = vi.fn().mockResolvedValue(Response.json({ id: 5 }));
  vi.stubGlobal("fetch", fetchMock);

  await expect(api("patients/5/")).resolves.toEqual({ id: 5 });
  expect(fetchMock).toHaveBeenCalledTimes(1);
  const [url, options] = fetchMock.mock.calls[0];
  expect(url).toBe("/api/v1/patients/5/");
  expect((options.headers as Headers).get("Authorization")).toBe("Bearer access-one");
  expect((options.headers as Headers).has("X-CSRFToken")).toBe(false);
});

it("shares one refresh request between concurrent expired API calls", async () => {
  setAccessToken("expired");
  const fetchMock = vi.fn().mockImplementation((url: string, options: RequestInit) => {
    if (url === "/api/v1/auth/refresh/") return Promise.resolve(Response.json({ access: "renewed" }));
    const token = new Headers(options.headers).get("Authorization");
    return Promise.resolve(token === "Bearer renewed"
      ? Response.json({ ok: true })
      : Response.json({ detail: "Expired" }, { status: 401 }));
  });
  vi.stubGlobal("fetch", fetchMock);

  await expect(Promise.all([api("patients/"), api("appointments/")]))
    .resolves.toEqual([{ ok: true }, { ok: true }]);
  expect(fetchMock.mock.calls.filter(([url]) => url === "/api/v1/auth/refresh/")).toHaveLength(1);
  expect(getAccessToken()).toBe("renewed");
});

it("coalesces only simultaneous identical reads and does not cache their result", async () => {
  let resolveFetch!: (response: Response) => void;
  const fetchMock = vi.fn().mockImplementationOnce(() => new Promise<Response>((resolve) => { resolveFetch = resolve; }))
    .mockResolvedValue(Response.json({ id: 5 }));
  vi.stubGlobal("fetch", fetchMock);
  const first = api("patients/5/");
  const second = api("patients/5/");
  expect(fetchMock).toHaveBeenCalledTimes(1);
  resolveFetch(Response.json({ id: 5 }));
  await expect(Promise.all([first, second])).resolves.toEqual([{ id: 5 }, { id: 5 }]);
  await api("patients/5/");
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

it("does not share reads across access-token changes or requests with options", async () => {
  const resolvers: Array<(response: Response) => void> = [];
  const fetchMock = vi.fn().mockImplementation(() => new Promise<Response>((resolve) => { resolvers.push(resolve); }));
  vi.stubGlobal("fetch", fetchMock);
  setAccessToken("user-a");
  const first = api("patients/5/");
  setAccessToken("user-b");
  const second = api("patients/5/");
  const third = api("patients/5/", { signal: new AbortController().signal });
  expect(fetchMock).toHaveBeenCalledTimes(3);
  resolvers.forEach((resolve) => resolve(Response.json({ id: 5 })));
  await Promise.all([first, second, third]);
});
