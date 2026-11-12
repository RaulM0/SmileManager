import { renderWithToast as render } from "../test/renderWithToast";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, test, vi } from "vitest";
import { api } from "../api/client";
import InvitationPage from "./InvitationPage";

vi.mock("../api/client", () => ({
  api: vi.fn(),
  getErrorMessage: (error: Error) => error.message,
}));

beforeEach(() => {
  vi.clearAllMocks();
});

test("muestra la clínica y requiere aceptación explícita", async () => {
  vi.mocked(api)
    .mockResolvedValueOnce({ clinic: "Clínica A", role: "DOCTOR" })
    .mockResolvedValueOnce(undefined);
  render(
    <MemoryRouter initialEntries={["/invitations/accept#token"]}>
      <Routes>
        <Route path="/invitations/accept" element={<InvitationPage />} />
      </Routes>
    </MemoryRouter>,
  );
  expect(await screen.findByText("Clínica A")).toBeInTheDocument();
  expect(api).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Aceptar invitación" }));
  await waitFor(() =>
    expect(screen.getByRole("status")).toHaveTextContent(
      "Aceptaste la invitación",
    ),
  );
  expect(api).toHaveBeenCalledTimes(2);
});
