export default function ComingSoonPage({ title }) {
  return (
    <div className="container py-5">
      <div className="alert alert-info">
        <h1 className="h4">{title}</h1>
        <p className="mb-0">
          Esta sección continúa disponible en la interfaz legacy mientras se
          completa y verifica su migración.
        </p>
      </div>
    </div>
  );
}
