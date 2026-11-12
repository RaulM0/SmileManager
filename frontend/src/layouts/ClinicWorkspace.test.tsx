import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import ClinicWorkspace from "./ClinicWorkspace";

const state = vi.hoisted(() => ({
  clinic: null as string | null,
  api: vi.fn(),
  clear: vi.fn(),
  cancel: vi.fn(),
}));
vi.mock("../api/client", () => ({
  api: state.api,
  getClinicContext: () => state.clinic,
  setClinicContext: (value: string | null) => {
    state.clinic = value;
  },
  getErrorMessage: (error: Error) => error.message,
}));
vi.mock("../query/client", () => ({
  queryClient: { clear: state.clear, cancelQueries: state.cancel },
}));
vi.mock("../hooks/useUnsavedChanges", () => ({
  hasUnsavedChanges: () => false,
  discardDraftsFor: (action: () => Promise<unknown>) => action(),
}));
vi.mock("./AppLayout", () => ({
  default: ({
    activeClinic,
    onClinicChange,
  }: {
    activeClinic: { name: string };
    onClinicChange: (id: string) => void;
  }) => (
    <div>
      <span>Activa: {activeClinic?.name}</span>
      <button onClick={() => onClinicChange("b")}>Cambiar a B</button>
    </div>
  ),
}));

afterEach(() => {
  cleanup();
  state.clinic = null;
  vi.clearAllMocks();
});

it("validates each selection and clears clinical cache when changing clinics", async () => {
  const a = { id: "a", name: "Clínica A", slug: "a", role: "DOCTOR" };
  const b = { id: "b", name: "Clínica B", slug: "b", role: "DOCTOR" };
  state.api.mockImplementation((path: string, options?: RequestInit) => {
    if (path === "clinics/memberships/") return Promise.resolve([a, b]);
    const requested = new Headers(options?.headers).get("X-Clinic-ID");
    return Promise.resolve(requested === "a" ? a : b);
  });
  state.cancel.mockResolvedValue(undefined);
  const router = createMemoryRouter(
    [{ path: "/", element: <ClinicWorkspace /> }],
    { initialEntries: ["/"] },
  );
  render(<RouterProvider router={router} />);
  fireEvent.click(await screen.findByRole("button", { name: "Clínica A" }));
  expect(await screen.findByText("Activa: Clínica A")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Cambiar a B" }));
  expect(await screen.findByText("Activa: Clínica B")).toBeTruthy();
  expect(state.clinic).toBe("b");
  expect(state.clear).toHaveBeenCalledTimes(2);
  await waitFor(() => expect(state.cancel).toHaveBeenCalledTimes(2));
});

it("retains the current clinic when the server rejects a context change", async () => {
  const a = { id: "a", name: "Clínica A", slug: "a", role: "DOCTOR" };
  const b = { id: "b", name: "Clínica B", slug: "b", role: "DOCTOR" };
  state.api.mockImplementation((path: string, options?: RequestInit) => {
    if (path === "clinics/memberships/") return Promise.resolve([a, b]);
    return new Headers(options?.headers).get("X-Clinic-ID") === "a"
      ? Promise.resolve(a)
      : Promise.reject(new Error("Acceso denegado"));
  });
  const router = createMemoryRouter(
    [{ path: "/", element: <ClinicWorkspace /> }],
    { initialEntries: ["/"] },
  );
  render(<RouterProvider router={router} />);
  fireEvent.click(await screen.findByRole("button", { name: "Clínica A" }));
  expect(await screen.findByText("Activa: Clínica A")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Cambiar a B" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Acceso denegado");
  expect(state.clinic).toBe("a");
  expect(state.clear).toHaveBeenCalledTimes(1);
});
