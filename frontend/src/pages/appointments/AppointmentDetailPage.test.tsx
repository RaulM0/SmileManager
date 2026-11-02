import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import AppointmentDetailPage from "./AppointmentDetailPage";

vi.mock("../../hooks/useResource", () => ({ useResource: () => ({ data: { id: 3, fecha: "2026-10-24", hora: "10:00:00", estatus: "A", estatus_display: "Anulada", motivo: "Control", observaciones: "", paciente: { id: 7, full_name: "ANA LOPEZ" } }, error: null, reload: vi.fn() }) }));

test("el detalle usa Cancelada y enlaza al paciente correcto", () => {
  render(<MemoryRouter initialEntries={["/appointments/3"]}><Routes><Route path="/appointments/:id" element={<AppointmentDetailPage />} /></Routes></MemoryRouter>);
  expect(screen.getByText("Cancelada")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "ANA LOPEZ" })).toHaveAttribute("href", "/patients/7");
});
