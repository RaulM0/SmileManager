import { useEffect, useId, useRef, useState } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import "./design-system-lab.css";

const directions = [
  {
    id: "a",
    letter: "A",
    name: "Flat Enterprise",
    description: "Precisión plana · bordes definidos",
  },
  {
    id: "b",
    letter: "B",
    name: "Flat 2.0",
    description: "Profundidad mínima · respuesta táctil",
  },
  {
    id: "c",
    letter: "C",
    name: "Fluent-inspired",
    description: "Capas neutras · estados claros",
  },
  {
    id: "d",
    letter: "D",
    name: "Soft Enterprise",
    description: "Superficies suaves · contornos ligeros",
  },
] as const;
type Direction = (typeof directions)[number];
type Intent =
  | "primary"
  | "secondary"
  | "tertiary"
  | "ghost"
  | "danger"
  | "danger-secondary"
  | "icon";
type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  intent?: Intent;
  compact?: boolean;
};

function Button({
  intent = "secondary",
  compact = false,
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`dsl-button dsl-button--${intent}${compact ? " dsl-button--compact" : ""} ${className}`}
      {...props}
    />
  );
}

function Icon({ name }: { name: string }) {
  return <i className={`bi bi-${name}`} aria-hidden="true" />;
}

function FilterGroup({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div
      className="dsl-filter"
      role="group"
      aria-label="Filtrar citas por estado"
    >
      {["Todas", "Pendientes", "Completadas", "Canceladas"].map((label) => (
        <button
          type="button"
          key={label}
          aria-pressed={value === label}
          onClick={() => onChange(label)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function ViewSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="dsl-segment" role="group" aria-label="Vista de agenda">
      {["Agenda", "Mes"].map((label) => (
        <button
          type="button"
          key={label}
          aria-pressed={value === label}
          onClick={() => onChange(label)}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function ChoiceGroup() {
  const name = useId();
  const [value, setValue] = useState("Sin registrar");
  return (
    <fieldset className="dsl-choices">
      <legend>¿Tiene problemas cardíacos?</legend>
      <div>
        {["Sin registrar", "Sí", "No"].map((label) => (
          <label key={label}>
            <input
              type="radio"
              name={name}
              value={label}
              checked={value === label}
              onChange={() => setValue(label)}
            />
            <span>{label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function ExampleTabs() {
  const [active, setActive] = useState(0);
  const id = useId();
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const tabs = ["Resumen", "Antecedentes", "Consultas"];
  function move(event: React.KeyboardEvent<HTMLButtonElement>, index: number) {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft")
      next = (index + tabs.length - 1) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault();
    setActive(next);
    refs.current[next]?.focus();
  }
  return (
    <div>
      <div
        className="dsl-tabs"
        role="tablist"
        aria-label="Secciones de ejemplo"
      >
        {tabs.map((tab, index) => (
          <button
            key={tab}
            ref={(node) => {
              refs.current[index] = node;
            }}
            type="button"
            role="tab"
            id={`${id}-tab-${index}`}
            aria-controls={`${id}-panel`}
            aria-selected={active === index}
            tabIndex={active === index ? 0 : -1}
            onClick={() => setActive(index)}
            onKeyDown={(event) => move(event, index)}
          >
            {tab}
          </button>
        ))}
      </div>
      <div
        className="dsl-tab-content"
        id={`${id}-panel`}
        role="tabpanel"
        aria-labelledby={`${id}-tab-${active}`}
        tabIndex={0}
      >
        Vista de {tabs[active].toLowerCase()} · ejemplo local
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`dsl-status dsl-status--${status.toLowerCase()}`}>
      <span aria-hidden="true" />
      {status}
    </span>
  );
}

function LoadingExample() {
  const [busy, setBusy] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  function start() {
    setBusy(true);
    timer.current = setTimeout(() => setBusy(false), 1600);
  }
  return (
    <>
      <Button intent="primary" disabled={busy} onClick={start}>
        {busy ? (
          <>
            <span className="dsl-spinner" aria-hidden="true" />
            Guardando…
          </>
        ) : (
          "Guardar cambios"
        )}
      </Button>
      <span className="dsl-sr" role="status">
        {busy ? "Guardando ejemplo" : ""}
      </span>
    </>
  );
}

function Scenario({
  direction,
  children,
}: {
  direction: Direction;
  children: ReactNode;
}) {
  return (
    <div className={`dsl-scenario dsl-theme-${direction.id}`}>
      <div className="dsl-scenario-heading">
        <span>{direction.letter}</span>
        <strong>{direction.name}</strong>
      </div>
      {children}
    </div>
  );
}
function Comparison({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: (direction: Direction) => ReactNode;
}) {
  return (
    <section className="dsl-section">
      <div className="dsl-section-header">
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <div className="dsl-comparison">
        {directions.map((direction) => (
          <Scenario key={direction.id} direction={direction}>
            {children(direction)}
          </Scenario>
        ))}
      </div>
    </section>
  );
}

const examples = [
  {
    time: "09:00",
    patient: "Paciente de ejemplo 01",
    reason: "Revisión",
    status: "Pendiente",
  },
  {
    time: "10:30",
    patient: "Paciente de ejemplo 02",
    reason: "Consulta",
    status: "Completada",
  },
  {
    time: "12:00",
    patient: "Paciente de ejemplo 03",
    reason: "Seguimiento",
    status: "Cancelada",
  },
];
function ActionSamples() {
  const [message, setMessage] = useState("");
  return (
    <>
      <div className="dsl-button-row">
        <Button
          intent="primary"
          onClick={() => setMessage("Nueva cita · acción de ejemplo")}
        >
          <Icon name="plus-lg" />
          Nueva cita
        </Button>
        <Button
          intent="primary"
          onClick={() => setMessage("Guardar · acción de ejemplo")}
        >
          Guardar
        </Button>
        <LoadingExample />
      </div>
      <div className="dsl-button-row">
        <Button onClick={() => setMessage("Editar · acción de ejemplo")}>
          Editar
        </Button>
        <Button onClick={() => setMessage("Volver · acción de ejemplo")}>
          Volver
        </Button>
        <Button
          intent="tertiary"
          onClick={() => setMessage("Cancelar · acción de ejemplo")}
        >
          Cancelar
        </Button>
        <Button
          intent="ghost"
          onClick={() => setMessage("Ver expediente · acción de ejemplo")}
        >
          Ver expediente
        </Button>
      </div>
      <div className="dsl-button-row">
        <Button
          intent="danger"
          onClick={() => setMessage("Cancelar cita · acción de ejemplo")}
        >
          Cancelar cita
        </Button>
        <Button
          intent="danger-secondary"
          onClick={() => setMessage("Eliminar · acción de ejemplo")}
        >
          Eliminar
        </Button>
        <Button
          intent="icon"
          aria-label="Editar ejemplo"
          onClick={() => setMessage("Editar · acción de ejemplo")}
        >
          <Icon name="pencil" />
        </Button>
        <Button disabled>Deshabilitado</Button>
      </div>
      <p className="dsl-feedback" role="status">
        {message || "Las acciones son demostrativas."}
      </p>
    </>
  );
}
function TableActions() {
  const [message, setMessage] = useState("");
  return (
    <>
      <div className="dsl-mini-table">
        <div>
          <span>Paciente de ejemplo</span>
          <StatusBadge status="Pendiente" />
        </div>
        <div className="dsl-button-row">
          <Button
            intent="ghost"
            compact
            onClick={() => setMessage("Ver paciente de ejemplo")}
          >
            Ver
          </Button>
          <Button
            compact
            onClick={() => setMessage("Editar paciente de ejemplo")}
          >
            Editar
          </Button>
          <Button
            intent="danger-secondary"
            compact
            onClick={() => setMessage("Eliminar ejemplo")}
          >
            Eliminar
          </Button>
          <Button
            intent="icon"
            compact
            aria-label="Más acciones de ejemplo"
            onClick={() => setMessage("Más acciones de ejemplo")}
          >
            <Icon name="three-dots" />
          </Button>
        </div>
      </div>
      <p className="dsl-feedback" role="status">
        {message || "Acciones compactas · sin cambios reales"}
      </p>
    </>
  );
}
function RealWorld() {
  const [filter, setFilter] = useState("Todas");
  const [view, setView] = useState("Agenda");
  const [message, setMessage] = useState("");
  const visible = examples.filter(
    (item) =>
      filter === "Todas" ||
      (
        {
          Pendiente: "Pendientes",
          Completada: "Completadas",
          Cancelada: "Canceladas",
        } as Record<string, string>
      )[item.status] === filter,
  );
  return (
    <div className="dsl-real">
      <div className="dsl-real-header">
        <div>
          <span>OPERACIÓN · EJEMPLO</span>
          <h3>Agenda</h3>
          <p>Datos ficticios · sin conexión con pacientes</p>
        </div>
        <Button
          intent="primary"
          onClick={() => setMessage("Nueva cita es una acción de ejemplo.")}
        >
          <Icon name="plus-lg" /> Nueva cita
        </Button>
      </div>
      <div className="dsl-real-controls">
        <FilterGroup value={filter} onChange={setFilter} />
        <ViewSelector value={view} onChange={setView} />
      </div>
      <div className="dsl-real-list">
        <div className="dsl-real-list-heading">
          <strong>
            {view === "Agenda" ? "Citas del día" : "Vista mensual"}
          </strong>
          <span>
            {visible.length} {visible.length === 1 ? "cita" : "citas"} de
            ejemplo
          </span>
        </div>
        {visible.map((item) => (
          <div className="dsl-real-row" key={item.patient}>
            <time>{item.time}</time>
            <div>
              <strong>{item.patient}</strong>
              <small>{item.reason}</small>
            </div>
            <StatusBadge status={item.status} />
            <Button
              intent="ghost"
              compact
              onClick={() =>
                setMessage(`Ver ${item.patient.toLowerCase()} · ejemplo local.`)
              }
            >
              Ver
            </Button>
          </div>
        ))}
      </div>
      <p className="dsl-feedback" role="status">
        {message ||
          "Selecciona un filtro o una vista para probar la interacción."}
      </p>
    </div>
  );
}

function FilterSample() {
  const [value, setValue] = useState("Todas");
  return <FilterGroup value={value} onChange={setValue} />;
}
function ViewSample() {
  const [value, setValue] = useState("Agenda");
  return <ViewSelector value={value} onChange={setValue} />;
}

const inputDirections = [
  {
    id: "crisp",
    letter: "1",
    name: "Contorno preciso",
    detail: "Borde fino · superficie blanca",
  },
  {
    id: "lift",
    letter: "2",
    name: "Flat 2.0",
    detail: "Contorno suave · elevación mínima",
  },
  {
    id: "soft",
    letter: "3",
    name: "Superficie suave",
    detail: "Fondo tenue · borde discreto",
  },
  {
    id: "accent",
    letter: "4",
    name: "Línea de acento",
    detail: "Fondo claro · base definida",
  },
] as const;

function InputSamples({
  direction,
}: {
  direction: (typeof inputDirections)[number];
}) {
  const id = useId();
  const [phone, setPhone] = useState("123");
  const error = phone.length > 0 && !/^\d{10}$/.test(phone);
  return (
    <div className={`dsl-input-scenario dsl-input-${direction.id}`}>
      <div className="dsl-input-heading">
        <span>{direction.letter}</span>
        <div>
          <h3>{direction.name}</h3>
          <p>{direction.detail}</p>
        </div>
      </div>
      <div className="dsl-input-field">
        <label htmlFor={`${id}-name`}>Nombre del paciente</label>
        <input
          className="dsl-text-input"
          id={`${id}-name`}
          placeholder="Escribe el nombre"
          autoComplete="off"
        />
        <small>Ejemplo de campo vacío.</small>
      </div>
      <div className="dsl-input-field">
        <label htmlFor={`${id}-search`}>Buscar paciente</label>
        <input
          className="dsl-text-input"
          id={`${id}-search`}
          type="search"
          defaultValue="Paciente de ejemplo"
        />
        <small>Campo con información.</small>
      </div>
      <div className="dsl-input-field">
        <label htmlFor={`${id}-phone`}>Teléfono</label>
        <input
          className="dsl-text-input"
          id={`${id}-phone`}
          type="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          aria-invalid={error}
          aria-describedby={`${id}-phone-help`}
        />
        <small
          id={`${id}-phone-help`}
          className={error ? "dsl-input-error" : ""}
        >
          {error
            ? "Escribe 10 dígitos para continuar."
            : "Ingresa un teléfono de 10 dígitos."}
        </small>
      </div>
      <div className="dsl-input-field">
        <label htmlFor={`${id}-disabled`}>Identificador</label>
        <input
          className="dsl-text-input"
          id={`${id}-disabled`}
          value="Se asigna automáticamente"
          disabled
          readOnly
        />
        <small>Ejemplo deshabilitado.</small>
      </div>
    </div>
  );
}

export default function DesignSystemLab() {
  return (
    <div className="dsl-lab">
      <header className="dsl-header">
        <div>
          <p className="dsl-kicker">SMILEMANAGER / EXPLORACIÓN DE DISEÑO</p>
          <h1>Laboratorio de interacción</h1>
          <p>
            Cuatro maneras de trabajar con los mismos controles clínicos.
            Compara sus estados y jerarquía antes de elegir una dirección.
          </p>
        </div>
        <div className="dsl-header-note">
          <span>PROTOTIPO AISLADO</span>
          <strong>Datos de ejemplo</strong>
          <small>Sin conexión con pacientes ni cambios en la aplicación.</small>
        </div>
      </header>
      <div className="dsl-guide">
        <span>
          <i className="bi bi-cursor" aria-hidden="true" /> Interactúa con cada
          opción
        </span>
        <span>
          <i className="bi bi-keyboard" aria-hidden="true" /> Usa Tab y las
          flechas en pestañas y radios
        </span>
        <span>
          <i className="bi bi-shield-check" aria-hidden="true" /> Ninguna acción
          modifica datos
        </span>
      </div>
      <section className="dsl-section" id="propuestas-inputs">
        <div className="dsl-section-header">
          <h2>Propuestas para cajas de texto</h2>
          <p>
            Cuatro opciones para comparar. Haz clic o usa Tab para ver el foco;
            corrige el teléfono para probar el error.
          </p>
        </div>
        <div className="dsl-input-grid">
          {inputDirections.map((direction) => (
            <InputSamples key={direction.id} direction={direction} />
          ))}
        </div>
        <p className="dsl-input-note">
          Estas opciones son independientes de las alternativas A–D de botones.
          Son ejemplos locales y no cambian los formularios actuales.
        </p>
      </section>
      <div className="dsl-direction-grid">
        {directions.map((d) => (
          <div key={d.id}>
            <span>{d.letter}</span>
            <div>
              <strong>{d.name}</strong>
              <small>{d.description}</small>
            </div>
          </div>
        ))}
      </div>
      <Comparison
        title="01 · Acciones"
        description="Jerarquía, estados y tamaños de trabajo. Pulsa «Guardar cambios» para ver la carga."
      >
        {() => <ActionSamples />}
      </Comparison>
      <Comparison
        title="02 · Filtros de agenda"
        description="Una sola selección persistente; no representa una acción primaria."
      >
        {() => <FilterSample />}
      </Comparison>
      <Comparison
        title="03 · Selector de vista"
        description="Cambia entre dos representaciones de la misma información."
      >
        {() => <ViewSample />}
      </Comparison>
      <Comparison
        title="04 · Navegación local"
        description="Pestañas de ejemplo con selección y navegación por teclado."
      >
        {() => <ExampleTabs />}
      </Comparison>
      <Comparison
        title="05 · Respuestas clínicas"
        description="Tres opciones mutuamente excluyentes; ausencia de información no equivale a «No»."
      >
        {() => <ChoiceGroup />}
      </Comparison>
      <Comparison
        title="06 · Acciones en contexto"
        description="Controles compactos y un estado informativo que no es interactivo."
      >
        {() => <TableActions />}
      </Comparison>
      <section className="dsl-section dsl-real-section">
        <div className="dsl-section-header">
          <h2>07 · Una jornada en contexto</h2>
          <p>
            Las mismas citas ficticias, filtros y acciones en cada alternativa.
            Cada panel funciona de forma independiente.
          </p>
        </div>
        <div className="dsl-real-grid">
          {directions.map((d) => (
            <Scenario key={d.id} direction={d}>
              <RealWorld />
            </Scenario>
          ))}
        </div>
      </section>
      <footer className="dsl-footer">
        Laboratorio visual · Las alternativas son propuestas y no modifican el
        diseño actual.
      </footer>
    </div>
  );
}
