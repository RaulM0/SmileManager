import { useToast } from "../../context/ToastContext";
import {
  AdminSection,
  AdminState,
  AdminStatus,
  AdminPagination,
} from "../../components/workspace/Administration";
import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getErrorMessage } from "../../api/client";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { useAuth } from "../../context/AuthContext";
import type { Paginated } from "../../types/domain";

type ClinicStatus = "ACTIVE" | "INACTIVE" | "SUSPENDED";
type Clinic = {
  id: string;
  name: string;
  slug: string;
  status: ClinicStatus;
  ai_enabled: boolean;
  ai_effective: boolean;
  ai_globally_enabled: boolean;
};
type Invitation = { id: string; email: string; expires_at: string };
const labels: Record<ClinicStatus, string> = {
  ACTIVE: "Activa",
  INACTIVE: "Inactiva",
  SUSPENDED: "Suspendida",
};

export default function PlatformClinicsPage() {
  const toast = useToast();
  const { user } = useAuth();
  const client = useQueryClient();
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Clinic | null>(null);
  const [change, setChange] = useState<{
    clinic: Clinic;
    status: ClinicStatus;
  } | null>(null);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [email, setEmail] = useState("");
  const [replacement, setReplacement] = useState("");
  const clinics = useQuery({
    queryKey: ["platform-clinics", page],
    enabled: Boolean(user?.is_platform_admin),
    queryFn: () => api<Paginated<Clinic>>(`backoffice/clinics/?page=${page}`),
  });
  const invitations = useQuery({
    queryKey: ["platform-clinic-invitations", selected?.id],
    enabled: Boolean(user?.is_platform_admin && selected),
    queryFn: () =>
      api<Paginated<Invitation>>(
        `backoffice/clinics/${selected!.id}/initial-admin/`,
      ),
  });
  const mutation = useMutation({
    mutationFn: ({ path, body }: { path: string; body?: object }) =>
      api(path, {
        method: "POST",
        ...(body ? { body: JSON.stringify(body) } : {}),
      }),
    onSuccess: async () => {
      toast.success("Operación realizada.");
      setChange(null);
      await Promise.all([
        client.invalidateQueries({ queryKey: ["platform-clinics"] }),
        client.invalidateQueries({ queryKey: ["platform-clinic-invitations"] }),
      ]);
    },
    onError: (error) => {
      setChange(null);
      toast.error(getErrorMessage(error));
    },
  });
  function create(event: FormEvent) {
    event.preventDefault();
    mutation.mutate(
      {
        path: "backoffice/clinics/",
        body: { name, slug, status: "INACTIVE", initial_admin_email: email },
      },
      {
        onSuccess: () => {
          setName("");
          setSlug("");
          setEmail("");
        },
      },
    );
  }
  function invite(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    mutation.mutate(
      {
        path: `backoffice/clinics/${selected.id}/initial-admin/`,
        body: { email: replacement },
      },
      { onSuccess: () => setReplacement("") },
    );
  }
  if (!user?.is_platform_admin)
    return <div role="alert">No tienes permiso para administrar clínicas.</div>;
  return (
    <>
      <div className="workspace-page-header">
        <div>
          <h1>Clínicas</h1>
          <p className="clinical-page-description">
            Alta, estado operativo y administración inicial
          </p>
        </div>
      </div>
      {clinics.data?.results[0]?.ai_globally_enabled === false && (
        <div className="workspace-inline-warning co-mb-4" role="status">
          IA está apagada para todo el sistema. Puedes preparar clínicas
          individuales, pero no tendrán acceso hasta activar{" "}
          <code>FEATURE_AI_ENABLED</code>.
        </div>
      )}
      <AdminSection
        title="Crear clínica"
        description="Registra la organización e invita a la persona responsable de administrarla."
      >
        <form onSubmit={create} className="clinical-form-body admin-form-grid">
          <label className="clinical-form-label">
            Nombre{" "}
            <input
              className="clinical-form-control"
              required
              maxLength={150}
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
          <label className="clinical-form-label">
            Identificador{" "}
            <input
              className="clinical-form-control"
              required
              maxLength={150}
              pattern="[-a-zA-Z0-9_]+"
              value={slug}
              onChange={(event) => setSlug(event.target.value)}
            />
          </label>
          <label className="clinical-form-label">
            Correo del administrador inicial{" "}
            <input
              className="clinical-form-control"
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <button
            className="clinical-action-primary"
            disabled={mutation.isPending}
          >
            Crear y enviar invitación
          </button>
        </form>
        <p className="clinical-form-help co-px-4 co-pb-4">
          La clínica se crea inactiva. Actívala para que el administrador pueda
          aceptar la invitación.
        </p>
      </AdminSection>
      <AdminSection title="Clínicas registradas">
        {clinics.isPending ? (
          <AdminState pending />
        ) : clinics.isError ? (
          <AdminState error />
        ) : !clinics.data?.results.length ? (
          <AdminState empty="Aún no hay clínicas registradas." />
        ) : (
          <div className="workspace-table-scroll">
            <table className="workspace-data-table">
              <thead>
                <tr>
                  <th>Clínica</th>
                  <th>Identificador</th>
                  <th>Estado</th>
                  <th>IA</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {clinics.data?.results.map((clinic) => (
                  <tr key={clinic.id}>
                    <td data-label="Clínica">{clinic.name}</td>
                    <td data-label="Identificador">{clinic.slug}</td>
                    <td data-label="Estado">
                      <AdminStatus
                        value={clinic.status}
                        label={labels[clinic.status]}
                      />
                    </td>
                    <td data-label="IA">
                      <AdminStatus
                        value={clinic.ai_effective ? "ACTIVE" : "INACTIVE"}
                        label={
                          clinic.ai_effective
                            ? "Activa"
                            : clinic.ai_enabled
                              ? "Preparada; apagada globalmente"
                              : "Desactivada"
                        }
                      />
                    </td>
                    <td data-label="Acciones" className="admin-table-actions">
                      <button
                        type="button"
                        className="clinical-action-outline"
                        disabled={mutation.isPending}
                        onClick={() =>
                          mutation.mutate({
                            path: `backoffice/clinics/${clinic.id}/features/ai/`,
                            body: { enabled: !clinic.ai_enabled },
                          })
                        }
                      >
                        {clinic.ai_enabled ? "Desactivar IA" : "Activar IA"}
                      </button>
                      <button
                        type="button"
                        className="clinical-action-outline"
                        onClick={() => {
                          setSelected(clinic);
                        }}
                      >
                        Administración inicial
                      </button>
                      {clinic.status !== "ACTIVE" && (
                        <button
                          type="button"
                          className="clinical-action-outline"
                          disabled={mutation.isPending}
                          onClick={() =>
                            setChange({ clinic, status: "ACTIVE" })
                          }
                        >
                          Activar
                        </button>
                      )}
                      {clinic.status === "ACTIVE" && (
                        <button
                          type="button"
                          className="clinical-action-outline"
                          disabled={mutation.isPending}
                          onClick={() =>
                            setChange({ clinic, status: "SUSPENDED" })
                          }
                        >
                          Suspender
                        </button>
                      )}
                      {clinic.status !== "INACTIVE" && (
                        <button
                          type="button"
                          className="clinical-action-outline"
                          disabled={mutation.isPending}
                          onClick={() =>
                            setChange({ clinic, status: "INACTIVE" })
                          }
                        >
                          Desactivar
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <AdminPagination
              label="Paginación de clínicas"
              page={page}
              count={clinics.data?.count}
              next={clinics.data?.next}
              busy={clinics.isFetching}
              onPage={setPage}
            />
          </div>
        )}
      </AdminSection>
      {selected && (
        <AdminSection title={`Administración inicial: ${selected.name}`}>
          <p className="clinical-form-help co-px-4 co-pt-4">
            Disponible cuando la clínica no tiene un administrador activo.
          </p>
          <form
            onSubmit={invite}
            className="clinical-form-body admin-form-grid"
          >
            <label className="clinical-form-label">
              Correo de invitación{" "}
              <input
                className="clinical-form-control"
                required
                type="email"
                value={replacement}
                onChange={(event) => setReplacement(event.target.value)}
              />
            </label>
            <button
              className="clinical-action-outline"
              disabled={mutation.isPending}
            >
              Enviar invitación
            </button>
          </form>
          {invitations.isPending ? (
            <AdminState pending />
          ) : invitations.isError ? (
            <AdminState error />
          ) : !invitations.data?.results.length ? (
            <AdminState empty="No hay invitaciones recientes." />
          ) : (
            <ul className="admin-activity-list">
              {invitations.data?.results.map((invitation) => (
                <li key={invitation.id}>
                  {invitation.email} · Vence{" "}
                  {new Date(invitation.expires_at).toLocaleString("es-MX")}{" "}
                  <button
                    type="button"
                    className="clinical-action-danger clinical-action-compact"
                    disabled={mutation.isPending}
                    onClick={() =>
                      mutation.mutate({
                        path: `backoffice/clinics/${selected.id}/initial-admin/${invitation.id}/revoke/`,
                      })
                    }
                  >
                    Revocar
                  </button>
                </li>
              ))}
            </ul>
          )}
        </AdminSection>
      )}
      {change && (
        <ConfirmDialog
          title="Cambiar estado de clínica"
          confirmLabel="Confirmar cambio"
          busy={mutation.isPending}
          onClose={() => setChange(null)}
          onConfirm={() =>
            mutation.mutate({
              path: `backoffice/clinics/${change.clinic.id}/status/`,
              body: { status: change.status },
            })
          }
        >
          <p>
            La clínica {change.clinic.name} quedará{" "}
            {labels[change.status].toLowerCase()}.
          </p>
        </ConfirmDialog>
      )}
    </>
  );
}
