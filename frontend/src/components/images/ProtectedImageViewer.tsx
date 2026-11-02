import { useProtectedMediaState } from "../../hooks/useProtectedMedia";
import ImageViewer from "./ImageViewer";

export default function ProtectedImageViewer({ path }: { path: string }) {
  const media = useProtectedMediaState(path);
  if (media?.url) return <ImageViewer url={media.url} />;
  if (media?.failed) return <div className="diagnostic-image-pending" role="status">Imagen no disponible.</div>;
  return <div className="image-viewer" role="status" aria-label="Cargando imagen clínica" />;
}
