import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DesignSystemLab from "./DesignSystemLab";

describe("laboratorio aislado", () => {
  it("permite probar la corrección del teléfono sin afectar las demás propuestas", () => {
    render(<DesignSystemLab />);
    const phones = screen.getAllByRole("textbox", { name: "Teléfono" });
    expect(phones[0]).toHaveAttribute("aria-invalid", "true");
    fireEvent.change(phones[0], { target: { value: "5512345678" } });
    expect(phones[0]).toHaveAttribute("aria-invalid", "false");
    expect(phones[1]).toHaveAttribute("aria-invalid", "true");
  });
  it("mantiene los filtros exclusivos y actualiza solo su ejemplo", () => {
    render(<DesignSystemLab />);
    const groups = screen.getAllByRole("group", {
      name: "Filtrar citas por estado",
    });
    fireEvent.click(
      within(groups[0]).getByRole("button", { name: "Pendientes" }),
    );
    expect(
      within(groups[0]).getByRole("button", { name: "Pendientes" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(
      within(groups[0]).getByRole("button", { name: "Todas" }),
    ).toHaveAttribute("aria-pressed", "false");
    expect(
      within(groups[1]).getByRole("button", { name: "Todas" }),
    ).toHaveAttribute("aria-pressed", "true");
  });
  it("mantiene radios independientes y mueve el foco de las pestañas con flechas", () => {
    render(<DesignSystemLab />);
    const groups = screen.getAllByRole("group", {
      name: "¿Tiene problemas cardíacos?",
    });
    fireEvent.click(within(groups[0]).getByRole("radio", { name: "Sí" }));
    expect(within(groups[0]).getByRole("radio", { name: "Sí" })).toBeChecked();
    expect(
      within(groups[1]).getByRole("radio", { name: "Sin registrar" }),
    ).toBeChecked();
    const tablist = screen.getAllByRole("tablist", {
      name: "Secciones de ejemplo",
    })[0];
    const first = within(tablist).getByRole("tab", { name: "Resumen" });
    first.focus();
    fireEvent.keyDown(first, { key: "ArrowRight" });
    expect(
      within(tablist).getByRole("tab", { name: "Antecedentes" }),
    ).toHaveFocus();
    expect(
      within(tablist).getByRole("tab", { name: "Antecedentes" }),
    ).toHaveAttribute("aria-selected", "true");
  });
  it("filtra las citas ficticias en una composición sin afectar las demás", () => {
    render(<DesignSystemLab />);
    const group = screen.getAllByRole("group", {
      name: "Filtrar citas por estado",
    })[4];
    const scenario = group.closest(".dsl-real") as HTMLElement;
    fireEvent.click(within(group).getByRole("button", { name: "Canceladas" }));
    expect(
      within(scenario).getByText("Paciente de ejemplo 03"),
    ).toBeInTheDocument();
    expect(
      within(scenario).queryByText("Paciente de ejemplo 01"),
    ).not.toBeInTheDocument();
    fireEvent.click(within(scenario).getByRole("button", { name: "Mes" }));
    expect(within(scenario).getByText("Vista mensual")).toBeInTheDocument();
  });
});
