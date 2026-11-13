import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, test, vi } from "vitest";
import { api } from "../../api/client";
import PatientListPage from "./PatientListPage";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../../api/client", () => ({
  api: vi.fn(),
  getClinicContext: () => null,
}));

beforeEach(() => vi.clearAllMocks());

test("una respuesta anterior no reemplaza el resultado del filtro vigente", async () => {
  const pending: Array<(value: unknown) => void> = [];
  vi.mocked(api).mockImplementation(
    () => new Promise((resolve) => pending.push(resolve)),
  );
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <MemoryRouter initialEntries={["/patients/search"]}>
        <Routes>
          <Route
            path="/patients/search"
            element={<PatientListPage searchable />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

  await waitFor(() => expect(pending).toHaveLength(1));
  fireEvent.change(
    screen.getByRole("searchbox", { name: "Buscar pacientes" }),
    {
      target: { value: "Lucía" },
    },
  );
  fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
  await waitFor(() => expect(pending).toHaveLength(2));

  await act(async () =>
    pending[1]({
      count: 1,
      previous: null,
      next: null,
      results: [
        {
          id: 2,
          nombre: "Lucía",
          appat: "Mora",
          apmat: "",
          telefono: "",
          email: "",
          estatus: "A",
        },
      ],
    }),
  );
  await waitFor(() =>
    expect(screen.getByRole("table")).toHaveTextContent("Lucía Mora"),
  );

  await act(async () =>
    pending[0]({
      count: 1,
      previous: null,
      next: null,
      results: [
        {
          id: 1,
          nombre: "Ana",
          appat: "López",
          apmat: "",
          telefono: "",
          email: "",
          estatus: "A",
        },
      ],
    }),
  );
  expect(screen.getByRole("table")).toHaveTextContent("Lucía Mora");
  expect(screen.queryByText(/Ana López/)).not.toBeInTheDocument();
});
