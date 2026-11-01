import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, getErrorMessage } from "../../api/client";
import ProtectedImageViewer from "../../components/images/ProtectedImageViewer";
import type { ClinicalImage, Detection } from "../../types/domain";
import { useToast } from "../../context/ToastContext";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "../../query/keys";
import { imagesService } from "../../services/images";

export default function DiagnosticResultPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const { id } = useParams();
  const [image, setImage] = useState<ClinicalImage | null>(null);
  const [detections, setDetections] = useState<Detection[]>([]);
  const [running, setRunning] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [sourceMissing, setSourceMissing] = useState(false);
  const [reload, setReload] = useState(0);
  const analyze = useCallback(async () => {
    setRunning(true);
    try {
      const result = await imagesService.analyze(id!, Boolean(image?.resultados_url));
      if (result.disposition === 'running') {
        toast.info('Ya hay un análisis en curso. Vuelve a consultar en unos momentos.');
        return;
      }
      setSourceMissing(false);
      setImage(result.image);
      setDetections(result.detections);
      queryClient.setQueryData(queryKeys.resource(`clinical-images/${id}/`), result.image);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.diagnostics }),
        queryClient.invalidateQueries({ queryKey: ["protected-media", `clinical-images/${id}/result-file/`] }),
      ]);
    } catch (err) {
      setSourceMissing(err instanceof ApiError && err.payload?.code === "source_image_missing");
      toast.error(getErrorMessage(err));
    } finally {
      setRunning(false);
    }
  }, [id, image?.resultados_url, toast, queryClient]);
  useEffect(() => {
    imagesService.get(id!).then((result) => {
      setImage(result);
      setLoadError("");
    }).catch((requestError) => setLoadError(requestError.message));
  }, [id, reload]);
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1560px]">
      <div className="workspace-page-header">
        <div><div className="workspace-context-note">Imagen clínica #{id}</div><h1>Resultados de análisis odontológico</h1>{image && <p className="clinical-page-description"><Link to={`/patients/${image.paciente}`}>{image.patient_name}</Link> · {image.tipo_imagen} · {new Date(image.fecha_subida).toLocaleDateString("es-MX")}</p>}</div>
        <button
          type="button"
          disabled={running || !image}
          className="clinical-action-primary"
          onClick={analyze}
        >
          {running ? "Analizando…" : image?.resultados_url ? "Analizar nuevamente" : "Analizar imagen"}
        </button>
      </div>
      {loadError && <div className="workspace-inline-error co-mb-4" role="alert">{loadError}<button className="clinical-action-outline co-ml-3" onClick={() => setReload((value) => value + 1)}>Reintentar</button></div>}
      {running && (
        <div className="workspace-inline-info co-mb-4" role="status" aria-live="polite">
          <span className="clinical-form-spinner" aria-hidden="true" />
          Procesando imagen con YOLO…
        </div>
      )}
      {image && (
        <div className="diagnostic-image-grid">
            <section className="diagnostic-image-panel" aria-label="Imagen original">
              <h2>Imagen original</h2>
              <ProtectedImageViewer path={`clinical-images/${image.id}/file/`} />
              {sourceMissing && <><p className="clinical-form-help">La nueva carga crea un registro independiente; el registro anterior se conserva.</p><Link className="clinical-action-outline co-mt-3" to={`/patients/${image.paciente}/images/upload`}>Cargar imagen en el expediente</Link></>}
            </section>
            <section className="diagnostic-image-panel" aria-label="Imagen analizada">
              <h2>Imagen analizada</h2>
              {image.resultados_url ? (
                <ProtectedImageViewer path={`clinical-images/${image.id}/result-file/`} />
              ) : (
                <div className="diagnostic-image-pending">Pendiente</div>
              )}
            </section>
        </div>
      )}
      {image?.resultados_url && !detections.length && !running && <p className="clinical-page-description">Se muestra el resultado guardado. Las detecciones detalladas aparecen al ejecutar un nuevo análisis.</p>}
      {detections.length > 0 && (
        <section className="workspace-section co-mt-5" aria-labelledby="detection-heading">
            <div className="workspace-section-heading"><h2 id="detection-heading">Detecciones</h2></div>
            <div className="workspace-table-scroll">
              <p className="table-scroll-hint"><i className="bi bi-arrow-left-right" aria-hidden="true" />Desliza la tabla para ver todas las columnas</p>
              <table className="clinical-detection-table">
                <thead>
                  <tr>
                    <th scope="col">Clase</th>
                    <th scope="col">Confianza</th>
                    <th scope="col">Coordenadas</th>
                  </tr>
                </thead>
                <tbody>
                  {detections.map((d, index) => (
                    <tr key={index}>
                      <td data-label="Clase">{d.clase}</td>
                      <td data-label="Confianza">{(d.confianza * 100).toFixed(2)}%</td>
                      <td data-label="Coordenadas">{d.coordenadas.map(Math.round).join(", ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
        </section>
      )}
    </div>
  );
}
