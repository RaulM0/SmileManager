export default function ComingSoonPage({ title }: { title: string }) {
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-inline-info co-block">
        <h1 className="co-mb-2 co-text-lg co-font-semibold">{title}</h1>
        <p className="co-m-0">
          Esta sección continúa disponible en la interfaz legacy mientras se
          completa y verifica su migración.
        </p>
      </div>
    </div>
  );
}
