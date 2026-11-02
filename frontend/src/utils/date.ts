export function formatDate(date: string) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date || "")) return date;
  const [year, month, day] = date.split("-");
  return `${day}/${month}/${year}`;
}
