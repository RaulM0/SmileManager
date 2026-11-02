export const appointmentStatus = {
  P: { label: "Pendiente", className: "is-pending" },
  C: { label: "Completada", className: "is-completed" },
  A: { label: "Cancelada", className: "is-cancelled" },
} as const;
