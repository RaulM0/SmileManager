import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, test, vi } from "vitest";
import { AppointmentCalendar } from "./AppointmentsPage";

describe("AppointmentCalendar", () => {
  test("muestra las citas y permite navegar entre meses", () => {
    vi.setSystemTime(new Date(2026, 9, 23, 12));
    const onMonthChange = vi.fn();
    render(
      <MemoryRouter>
        <AppointmentCalendar
          onMonthChange={onMonthChange}
          appointments={[
            {
              id: 7,
              fecha: "2026-10-24",
              hora: "10:00:00",
              estatus: "P",
              motivo: "Control",
              observaciones: "",
              paciente: {
                id: 1,
                nombre: "ANA",
                appat: "LOPEZ",
                apmat: "",
                full_name: "ANA LOPEZ",
                estatus: "A",
              },
            },
          ]}
        />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("heading", { name: /octubre de 2026/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: /10:00.*ANA LOPEZ/ }),
    ).toHaveLength(2);
    screen
      .getAllByRole("link", { name: /10:00.*ANA LOPEZ/ })
      .forEach((link) => {
        expect(link).toHaveAttribute("href", "/appointments/7");
      });
    expect(screen.getByRole("button", { name: "Agenda" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    fireEvent.click(screen.getByRole("button", { name: "Mes" }));
    expect(screen.getByRole("button", { name: "Mes" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    fireEvent.click(screen.getByRole("button", { name: "Mes siguiente" }));
    expect(onMonthChange).toHaveBeenCalledWith(new Date(2026, 10, 1));
    expect(
      screen.getByRole("heading", { name: /noviembre de 2026/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No hay citas para este mes con los filtros actuales."),
    ).toBeInTheDocument();
    vi.useRealTimers();
  });
});
