import { useEffect, useMemo, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { useParams } from "react-router-dom";
import { api, getErrorMessage } from "../../api/client";
import type { OdontogramData } from "../../types/domain";
import { useToast } from "../../context/ToastContext";
import { clinicalService } from "../../services/clinical";
import { useUnsavedChanges } from "../../hooks/useUnsavedChanges";

const states = [
  ["sin_registrar", "Sin registrar"],
  ["sano", "Sano"],
  ["caries", "Caries"],
  ["restauracion", "Restauración"],
  ["ausente", "Ausente"],
  ["extraccion", "Extracción"],
  ["protesis", "Prótesis"],
];
const surfaces = ["mesial", "oclusal", "distal", "lingual", "vestibular"];
const quadrantLabels = [
  "Superior derecha",
  "Superior izquierda",
  "Inferior derecha",
  "Inferior izquierda",
];
const permanent = [
  [18, 17, 16, 15, 14, 13, 12, 11],
  [21, 22, 23, 24, 25, 26, 27, 28],
  [48, 47, 46, 45, 44, 43, 42, 41],
  [31, 32, 33, 34, 35, 36, 37, 38],
];
const deciduous = [
  [55, 54, 53, 52, 51],
  [61, 62, 63, 64, 65],
  [85, 84, 83, 82, 81],
  [71, 72, 73, 74, 75],
];
const unrecorded = () =>
  Object.fromEntries(surfaces.map((surface) => [surface, "sin_registrar"]));
type DentitionData = Record<string, Record<string, string>>;

function fullDentition(
  groups: number[][],
  saved: DentitionData,
): DentitionData {
  return Object.fromEntries(
    groups
      .flat()
      .map((number) => [
        number,
        { ...unrecorded(), ...(saved?.[number] || {}) },
      ]),
  );
}
function recordedDentition(data: DentitionData): DentitionData {
  return Object.fromEntries(
    Object.entries(data).flatMap(([tooth, values]) => {
      const recorded = Object.fromEntries(
        Object.entries(values).filter(([, state]) => state !== "sin_registrar"),
      );
      return Object.keys(recorded).length ? [[tooth, recorded]] : [];
    }),
  );
}
function Tooth({
  number,
  data,
  onSurface,
}: {
  number: number;
  data: Record<string, string>;
  onSurface: (number: number, surface: string) => void;
}) {
  return (
    <div className="tooth">
      <div className="tooth-grid">
        {surfaces.map((surface) => (
          <button
            aria-label={`${number} ${surface} ${data[surface] === "sin_registrar" ? "sin registrar" : data[surface]}`}
            title={surface}
            type="button"
            key={surface}
            className={`tooth-surface tooth-${surface} state-${data[surface]}`}
            onClick={() => onSurface(number, surface)}
          />
        ))}
      </div>
      <span className="tooth-number">{number}</span>
    </div>
  );
}
function Dentition({
  title,
  groups,
  data,
  onSurface,
}: {
  title: string;
  groups: number[][];
  data: Record<string, Record<string, string>>;
  onSurface: (number: number, surface: string) => void;
}) {
  const [activeQuadrant, setActiveQuadrant] = useState(0);
  return (
    <section className="clinical-dentition-section" aria-label={title}>
      <div className="clinical-dentition-body">
        <h2>{title}</h2>
        <div
          className="odontogram-quadrant-tabs"
          role="group"
          aria-label={`Cuadrante de ${title}`}
        >
          {quadrantLabels.map((label, index) => (
            <button
              type="button"
              key={label}
              aria-pressed={activeQuadrant === index}
              onClick={() => setActiveQuadrant(index)}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="odontogram-quadrants">
          {groups.map((group, index) => (
            <div
              className={`odontogram-quadrant${activeQuadrant === index ? " is-mobile-current" : ""}`}
              key={index}
            >
              <h3>{quadrantLabels[index]}</h3>
              <div className="tooth-row">
                {group.map((number) => (
                  <Tooth
                    key={number}
                    number={number}
                    data={data[number]}
                    onSurface={onSurface}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function OdontogramPage({
  administrative = false,
}: {
  administrative?: boolean;
}) {
  const toast = useToast();
  const { id } = useParams();
  const [active, setActive] = useState("sano");
  const [permanentData, setPermanent] = useState<DentitionData | null>(null);
  const [deciduousData, setDeciduous] = useState<DentitionData | null>(null);
  const [baseline, setBaseline] = useState<string | null>(null);
  const guard = useUnsavedChanges(
    baseline !== null &&
      JSON.stringify([permanentData, deciduousData]) !== baseline,
  );
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [loadVersion, setLoadVersion] = useState(0);
  const [existingRecord, setExistingRecord] = useState(false);
  const [version, setVersion] = useState(0);
  useEffect(() => {
    // Clear the previous patient's clinical record while the new one loads.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPermanent(null);
    setDeciduous(null);
    (administrative
      ? api<OdontogramData>(`backoffice/patients/${id}/records/odontogram/`)
      : clinicalService.odontogram(id!)
    )
      .then((data) => {
        const permanentResult = fullDentition(
          permanent,
          data.denticion_permanente,
        );
        const deciduousResult = fullDentition(
          deciduous,
          data.denticion_decidua,
        );
        setPermanent(permanentResult);
        setDeciduous(deciduousResult);
        setBaseline(JSON.stringify([permanentResult, deciduousResult]));
        setExistingRecord(data.id != null);
        setVersion(data.version ?? 0);
        setError("");
      })
      .catch((requestError) => setError(requestError.message));
  }, [id, loadVersion, administrative]);
  const summary = useMemo(() => {
    if (!permanentData || !deciduousData) return {};
    const all = [
      ...Object.values(permanentData),
      ...Object.values(deciduousData),
    ];
    return {
      total_dientes: all.length,
      dientes_sanos: all.filter((tooth) =>
        Object.values(tooth).every((state) => state === "sano"),
      ).length,
      dientes_afectados: all.filter((tooth) =>
        Object.values(tooth).some(
          (state) => state !== "sano" && state !== "sin_registrar",
        ),
      ).length,
      dientes_sin_registrar: all.filter((tooth) =>
        Object.values(tooth).some((state) => state === "sin_registrar"),
      ).length,
      superficies_caries: all
        .flatMap(Object.values)
        .filter((state) => state === "caries").length,
      superficies_restauradas: all
        .flatMap(Object.values)
        .filter((state) => state === "restauracion").length,
    };
  }, [permanentData, deciduousData]);
  if (error && !permanentData)
    return (
      <div className="workspace-page co-mx-auto co-max-w-[1560px]">
        <div className="workspace-inline-error" role="alert">
          {error}
        </div>
        <button
          className="clinical-action-outline co-mt-3"
          onClick={() => setLoadVersion((value) => value + 1)}
        >
          Reintentar
        </button>
      </div>
    );
  if (!permanentData || !deciduousData)
    return (
      <div
        className="page-loader"
        role="status"
        aria-label="Cargando odontograma"
      >
        <div className="workspace-loader-spinner" />
      </div>
    );
  const change =
    (setter: Dispatch<SetStateAction<DentitionData | null>>) =>
    (number: number, surface: string) => {
      setter((current) => ({
        ...current,
        [number]: { ...current?.[number], [surface]: active },
      }));
    };
  async function save() {
    if (saving) return;
    setSaving(true);
    setError("");
    try {
      const values = {
        denticion_permanente: recordedDentition(permanentData!),
        denticion_decidua: recordedDentition(deciduousData!),
        resumen: summary as Record<string, number>,
        version,
      };
      const saved = administrative
        ? await api<OdontogramData>(
            `backoffice/patients/${id}/records/odontogram/`,
            { method: "PUT", body: JSON.stringify(values) },
          )
        : await clinicalService.saveOdontogram(id!, values);
      setVersion(saved.version ?? version + 1);
      setBaseline(JSON.stringify([permanentData, deciduousData]));
      toast.success("Odontograma guardado correctamente.");
    } catch (requestError) {
      toast.error(getErrorMessage(requestError));
    } finally {
      setSaving(false);
    }
  }
  function clear() {
    if (
      !window.confirm(
        "¿Confirma que desea limpiar completamente el odontograma?",
      )
    )
      return;
    setPermanent(fullDentition(permanent, {}));
    setDeciduous(fullDentition(deciduous, {}));
    toast.info(
      "Odontograma limpio en pantalla. Guarda para aplicar los cambios.",
    );
  }
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1560px]">
      <div className="workspace-page-header">
        <div>
          <h1>Odontograma</h1>
          <p className="clinical-page-description">
            Sistema FDI · Dentición permanente y decidua
          </p>
        </div>
      </div>
      <p className="clinical-page-description">
        Las superficies sin registrar no se consideran sanas. Confirma
        clínicamente los estados existentes.
      </p>
      {existingRecord && (
        <p className="workspace-inline-warning">
          En odontogramas anteriores a esta actualización, algunos estados sanos
          podrían proceder de valores predeterminados. Verifica el registro
          clínicamente.
        </p>
      )}
      <div className="odontogram-toolbar">
        <h2>Herramientas de diagnóstico</h2>
        <p>Selecciona un estado y después una superficie dental.</p>
        <div
          className="odontogram-state-options"
          role="group"
          aria-label="Estado para pintar superficies"
        >
          {states.map(([value, label]) => (
            <button
              type="button"
              key={value}
              className={`odontogram-state-button ${active === value ? "is-active" : ""}`}
              aria-pressed={active === value}
              onClick={() => setActive(value)}
            >
              <span
                className={`odontogram-state-swatch state-${value}`}
                aria-hidden="true"
              />
              {label}
            </button>
          ))}
        </div>
      </div>
      <Dentition
        title="Dentición Permanente"
        groups={permanent}
        data={permanentData}
        onSurface={change(setPermanent)}
      />
      <Dentition
        title="Dentición Decidua (Temporal)"
        groups={deciduous}
        data={deciduousData}
        onSurface={change(setDeciduous)}
      />
      <dl className="odontogram-summary" aria-label="Resumen del odontograma">
        <div>
          <dt>Posiciones FDI</dt>
          <dd>{summary.total_dientes}</dd>
        </div>
        <div>
          <dt>Sanos</dt>
          <dd>{summary.dientes_sanos}</dd>
        </div>
        <div>
          <dt>Afectados</dt>
          <dd>{summary.dientes_afectados}</dd>
        </div>
        <div>
          <dt>Con superficies sin registrar</dt>
          <dd>{summary.dientes_sin_registrar}</dd>
        </div>
        <div>
          <dt>Caries</dt>
          <dd>{summary.superficies_caries}</dd>
        </div>
        <div>
          <dt>Restauradas</dt>
          <dd>{summary.superficies_restauradas}</dd>
        </div>
      </dl>
      <div className="odontogram-actions">
        <button
          className="clinical-action-primary"
          onClick={save}
          disabled={saving}
        >
          {saving ? "Guardando…" : "Guardar odontograma"}
        </button>
        <button className="clinical-action-outline" onClick={clear}>
          Limpiar todo
        </button>
      </div>
      {guard.prompt}
    </div>
  );
}
