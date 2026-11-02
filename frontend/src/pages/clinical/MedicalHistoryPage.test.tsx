import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { ToastProvider } from "../../context/ToastContext";
import { clinicalService } from "../../services/clinical";
import MedicalHistoryPage from "./MedicalHistoryPage";

vi.mock("../../services/patients", () => ({ patientsService: { get: vi.fn().mockResolvedValue({ nombre: "ANA", appat: "LOPEZ" }) } }));
vi.mock("../../services/clinical", () => ({ clinicalService: { medicalHistory: vi.fn(), saveMedicalHistory: vi.fn() } }));

test("un antecedente sin registrar se puede responder y volver a dejar sin información", async () => {
  vi.mocked(clinicalService.medicalHistory).mockResolvedValue({ id: null, problemas_cardiacos: null });
  vi.mocked(clinicalService.saveMedicalHistory).mockResolvedValue({ id: 1, problemas_cardiacos: null });
  const router = createMemoryRouter([{ path: "/patients/:id/medical-history", element: <MedicalHistoryPage /> }], { initialEntries: ["/patients/1/medical-history"] });
  render(<ToastProvider><RouterProvider router={router} /></ToastProvider>);
  await screen.findByRole("heading", { name: /Antecedentes de ANA/ });
  const unknown = document.getElementById("problemas_cardiacos-unknown") as HTMLInputElement;
  const yes = document.getElementById("problemas_cardiacos-yes") as HTMLInputElement;
  expect(unknown).toBeChecked();
  expect(yes).not.toBeChecked();
  fireEvent.click(yes);
  expect(yes).toBeChecked();
  fireEvent.click(unknown);
  fireEvent.click(screen.getByRole("button", { name: "Guardar antecedentes" }));
  await waitFor(() => expect(clinicalService.saveMedicalHistory).toHaveBeenCalledWith("1", expect.objectContaining({ problemas_cardiacos: null })));
});
