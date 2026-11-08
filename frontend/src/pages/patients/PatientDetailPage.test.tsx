import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useNavigate } from "react-router-dom";
import { beforeEach, expect, test, vi } from "vitest";
import { api } from "../../api/client";
import PatientDetailPage from "./PatientDetailPage";
import { ToastProvider } from "../../context/ToastContext";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("../../api/client", () => ({ api: vi.fn(), getClinicContext: () => null }));

function SwitchPatient() {
  const navigate = useNavigate();
  return <button onClick={() => navigate("/patients/2")}>Cambiar expediente</button>;
}

beforeEach(() => vi.clearAllMocks());

test("al cambiar de paciente no muestra el expediente anterior durante carga o error", async () => {
  const pending: Array<{ resolve: (value: unknown) => void; reject: (reason: Error) => void }> = [];
  vi.mocked(api).mockImplementation(() => new Promise((resolve, reject) => pending.push({ resolve, reject })));
  render(
    <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><ToastProvider><MemoryRouter initialEntries={["/patients/1"]}>
      <SwitchPatient />
      <Routes>
        <Route path="/patients/:id" element={<PatientDetailPage />} />
      </Routes>
    </MemoryRouter></ToastProvider></QueryClientProvider>,
  );

  await waitFor(() => expect(pending).toHaveLength(1));
  await act(async () => pending[0].resolve({
    id: 1, nombre: "Ana", appat: "López", apmat: "", fecha_nacimiento: "1990-01-01",
    age: 36, genero: "F", estatus: "A", telefono: "", email: "",
  }));
  await waitFor(() => expect(screen.getByRole("heading", { name: "Ana López" })).toBeInTheDocument());

  fireEvent.click(screen.getByRole("button", { name: "Cambiar expediente" }));
  await waitFor(() => expect(pending).toHaveLength(2));
  expect(screen.getByRole("status", { name: "Cargando paciente" })).toBeInTheDocument();
  expect(screen.queryByText("Ana López")).not.toBeInTheDocument();

  await act(async () => pending[1].reject(new Error("Sin acceso")));
  await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Sin acceso"));
  expect(screen.queryByText("Ana López")).not.toBeInTheDocument();
});
