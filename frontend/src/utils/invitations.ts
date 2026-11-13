export const invitationRoleLabel = (role: string) =>
  (
    ({
      CLINIC_ADMIN: "Administrador de clínica",
      DOCTOR: "Médico",
      STAFF: "Personal de apoyo",
    }) as Record<string, string>
  )[role] || role;
