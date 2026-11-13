export const date = (value: string | null) =>
  value ? new Date(value).toLocaleString("es-MX") : "—";
