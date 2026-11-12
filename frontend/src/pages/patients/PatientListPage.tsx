import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  keepPreviousData,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { Paginated, Patient } from "../../types/domain";
import { patientsService } from "../../services/patients";
import { queryKeys } from "../../query/keys";
import { latestCachedData } from "../../query/latestCachedData";

export default function PatientListPage({
  searchable = false,
}: {
  searchable?: boolean;
}) {
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const query = params.get("q") || "";
  const page = params.get("page") || "1";
  const [term, setTerm] = useState(query);
  const records = useQuery({
    queryKey: queryKeys.patientList(query, page),
    queryFn: () => patientsService.list(query, page),
    placeholderData: keepPreviousData,
  });
  const data: Paginated<Patient> | undefined =
    records.data ??
    latestCachedData<Paginated<Patient>>(queryClient, [
      ...queryKeys.patients,
      "list",
    ]);
  const error = records.error?.message ?? "";
  function search(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setParams(term ? { q: term } : {});
  }
  return (
    <div className="workspace-page co-mx-auto co-max-w-[1320px]">
      <div className="workspace-page-header">
        <div>
          <h1>{searchable ? "Buscar pacientes" : "Todos los pacientes"}</h1>
        </div>
        <Link to="/patients/new" className="clinical-action-primary">
          <i className="bi bi-person-plus" aria-hidden="true" />
          Registrar
        </Link>
      </div>
      {
        <form onSubmit={search} className="clinical-search-form" role="search">
          <input
            type="search"
            aria-label="Buscar pacientes"
            className="clinical-form-control"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="Nombre, teléfono o correo"
          />
          <button className="clinical-action-primary">Buscar</button>
        </form>
      }
      {error && (
        <div
          className={
            data
              ? "workspace-inline-warning co-mb-4"
              : "workspace-inline-error co-mb-4"
          }
          role="alert"
        >
          {error}
          {data && <span> Se muestran los pacientes de la última carga.</span>}
          <button
            className="clinical-action-outline co-ml-3"
            onClick={() => void records.refetch()}
          >
            Reintentar
          </button>
        </div>
      )}
      {records.isFetching && data && (
        <p className="clinical-loading-note" role="status">
          Actualizando pacientes…
        </p>
      )}
      {!data ? (
        error ? null : (
          <div
            className="page-loader"
            role="status"
            aria-label="Cargando pacientes"
          >
            <div className="workspace-loader-spinner" />
          </div>
        )
      ) : data.results.length ? (
        <div className="workspace-table-frame">
          <div className="workspace-table-scroll">
            <p className="table-scroll-hint">
              <i className="bi bi-arrow-left-right" aria-hidden="true" />
              Desliza la tabla para ver todas las columnas
            </p>
            <table
              className="workspace-data-table"
              aria-busy={records.isFetching}
            >
              <caption className="co-sr-only">Registros de pacientes</caption>
              <thead>
                <tr>
                  <th scope="col">Paciente</th>
                  <th scope="col">Teléfono</th>
                  <th scope="col">Correo</th>
                  <th scope="col">Estado</th>
                  <th scope="col">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((p) => (
                  <tr key={p.id}>
                    <td data-label="Paciente">
                      {p.nombre} {p.appat} {p.apmat}
                    </td>
                    <td data-label="Teléfono">{p.telefono}</td>
                    <td data-label="Correo">{p.email}</td>
                    <td data-label="Estado">
                      <span
                        className={`patient-status ${p.estatus === "A" ? "is-active" : "is-inactive"}`}
                      >
                        {p.estatus === "A" ? "Activo" : "Inactivo"}
                      </span>
                    </td>
                    <td data-label="Acciones">
                      <Link
                        aria-label={`Ver ${p.nombre}`}
                        className="clinical-icon-action co-mr-1"
                        to={`/patients/${p.id}`}
                      >
                        <i className="bi bi-eye" aria-hidden="true" />
                      </Link>
                      <Link
                        aria-label={`Editar ${p.nombre}`}
                        className="clinical-icon-action"
                        to={`/patients/${p.id}/edit`}
                      >
                        <i className="bi bi-pencil" aria-hidden="true" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="workspace-empty-state">
          <span>No se encontraron pacientes.</span>
          {query && (
            <button
              className="clinical-action-outline co-mt-3"
              type="button"
              onClick={() => {
                setTerm("");
                setParams({});
              }}
            >
              Limpiar búsqueda
            </button>
          )}
        </div>
      )}
      {data && (
        <nav
          className="workspace-pagination"
          aria-label="Paginación de pacientes"
        >
          <button
            className="clinical-action-outline clinical-action-compact"
            disabled={!data.previous}
            onClick={() =>
              setParams({
                ...Object.fromEntries(params),
                page: String(Number(page) - 1),
              })
            }
          >
            Anterior
          </button>
          <span className="workspace-pagination-summary" aria-live="polite">
            Página {page} · {data.count} registros
          </span>
          <button
            className="clinical-action-outline clinical-action-compact"
            disabled={!data.next}
            onClick={() =>
              setParams({
                ...Object.fromEntries(params),
                page: String(Number(page) + 1),
              })
            }
          >
            Siguiente
          </button>
        </nav>
      )}
    </div>
  );
}
