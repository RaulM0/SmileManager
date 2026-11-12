import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  api,
  getClinicContext,
  getErrorMessage,
  setClinicContext,
} from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import {
  discardDraftsFor,
  hasUnsavedChanges,
} from "../hooks/useUnsavedChanges";
import { queryClient } from "../query/client";
import AppLayout from "./AppLayout";

export interface ClinicOption {
  id: string;
  name: string;
  slug: string;
  role: "DOCTOR" | "CLINIC_ADMIN" | "STAFF";
  ai_enabled: boolean;
  ai_effective: boolean;
  ai_globally_enabled: boolean;
}

export default function ClinicWorkspace() {
  const navigate = useNavigate();
  const location = useLocation();
  const [clinics, setClinics] = useState<ClinicOption[] | null>(null);
  const [active, setActive] = useState<ClinicOption | null>(null);
  const [pending, setPending] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const [validatedRoute, setValidatedRoute] = useState("");

  useEffect(() => {
    let live = true;
    api<ClinicOption[]>("clinics/memberships/")
      .then((rows) => {
        if (!live) return;
        setClinics(rows);
        const prior = rows.find((row) => row.id === getClinicContext());
        if (prior) setActive(prior);
        else if (getClinicContext()) {
          setClinicContext(null);
          queryClient.clear();
        } else if (rows.length === 1) {
          // A sole membership has no ambiguous selection; still authorize it on
          // the server before rendering any clinical screen.
          void api<ClinicOption>("clinics/context/", {
            headers: { "X-Clinic-ID": rows[0].id },
          })
            .then((verified) => {
              if (!live) return;
              setClinicContext(verified.id);
              queryClient.clear();
              setActive(verified);
            })
            .catch((reason) => {
              if (live) setError(getErrorMessage(reason));
            });
        }
      })
      .catch((reason) => {
        if (live) setError(getErrorMessage(reason));
      });
    return () => {
      live = false;
    };
  }, [reload]);

  const routeKey = active ? `${active.id}:${location.pathname}` : "";
  useEffect(() => {
    if (!active || validatedRoute === routeKey) return undefined;
    let live = true;
    api<ClinicOption>("clinics/context/", {
      headers: { "X-Clinic-ID": active.id },
    })
      .then((verified) => {
        if (!live) return;
        if (verified.role !== active.role) {
          void queryClient.cancelQueries();
          queryClient.clear();
          setActive(verified);
        }
        setValidatedRoute(routeKey);
      })
      .catch(() => {
        if (!live) return;
        setClinicContext(null);
        void queryClient.cancelQueries();
        queryClient.clear();
        setActive(null);
        setClinics(null);
        setError(
          "No fue posible verificar el acceso a la clínica. Selecciona una clínica autorizada.",
        );
        setReload((value) => value + 1);
      });
    return () => {
      live = false;
    };
  }, [active, routeKey, validatedRoute]);

  async function selectClinic(id: string) {
    if (!id || busy || active?.id === id) return;
    setBusy(true);
    try {
      const verified = await api<ClinicOption>("clinics/context/", {
        headers: { "X-Clinic-ID": id },
      });
      await discardDraftsFor(async () => {
        setClinicContext(verified.id);
        void queryClient.cancelQueries();
        queryClient.clear();
        setActive(verified);
        navigate("/", { replace: true });
      });
      setError("");
    } catch (reason) {
      setError(getErrorMessage(reason));
    } finally {
      setPending(null);
      setBusy(false);
    }
  }

  function requestClinic(id: string) {
    if (id === active?.id) return;
    if (hasUnsavedChanges()) setPending(id);
    else void selectClinic(id);
  }

  if (!clinics)
    return (
      <div className="workspace-page" role="status">
        {error ? (
          <>
            <p role="alert">{error}</p>
            <button type="button" onClick={() => setReload((n) => n + 1)}>
              Reintentar
            </button>
          </>
        ) : (
          "Cargando clínicas…"
        )}
      </div>
    );
  if (clinics.length && !active)
    return (
      <main className="workspace-page">
        <h1>Selecciona una clínica</h1>
        <p>Elige la organización con la que deseas trabajar.</p>
        {error && <p role="alert">{error}</p>}
        {clinics.map((clinic) => (
          <p key={clinic.id}>
            <button
              type="button"
              className="clinical-action-outline"
              disabled={busy}
              onClick={() => void selectClinic(clinic.id)}
            >
              {clinic.name}
            </button>
          </p>
        ))}
      </main>
    );
  if (active && validatedRoute !== routeKey)
    return (
      <div className="workspace-page" role="status">
        Comprobando acceso a la clínica…
      </div>
    );

  return (
    <>
      <AppLayout
        clinics={clinics}
        activeClinic={active}
        onClinicChange={requestClinic}
        clinicBusy={busy}
      />
      {error && (
        <div role="alert" className="workspace-inline-error">
          {error}
        </div>
      )}
      {pending && (
        <ConfirmDialog
          title="Cambiar de clínica"
          confirmLabel="Descartar y cambiar"
          busy={busy}
          onClose={() => setPending(null)}
          onConfirm={() => void selectClinic(pending)}
        >
          <p>Perderás los cambios que todavía no has guardado.</p>
        </ConfirmDialog>
      )}
    </>
  );
}
