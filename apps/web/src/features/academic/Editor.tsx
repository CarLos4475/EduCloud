import { FormEvent, useRef, useEffect } from "react";
import { Row } from "../../api";
import { Illustration, illustrations } from "../../components/Illustration";

export type EditorState = { collection: string; row?: Row; subjectId?: string };

export function Editor({
  state,
  subjects,
  periods,
  topics,
  onSave,
  onClose,
  busy,
  error,
}: {
  state: EditorState;
  subjects: Row[];
  periods: Row[];
  topics: Row[];
  onSave: (value: Record<string, unknown>) => void;
  onClose: () => void;
  busy: boolean;
  error: string;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const { collection, row } = state;
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  const labels: Record<string, string> = {
    subjects: "materia",
    periods: "periodo",
    topics: "tema",
    agenda: "pendiente",
    schedule: "bloque de horario",
  };
  const value = (key: string, fallback = "") => String(row?.[key] ?? fallback);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const result: Record<string, unknown> = {};
    for (const [key, value] of data.entries())
      result[key] = String(value) || null;
    for (const key of ["order", "weekday"])
      if (key in result) result[key] = Number(result[key]);
    if (collection === "topics")
      result.prerequisiteIds = data.getAll("prerequisiteIds");
    if (collection === "schedule")
      result.excludedDates = String(data.get("excludedDates") || "")
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean);
    if (collection === "agenda") {
      if (result.dueAt)
        result.dueAt = new Date(String(result.dueAt)).toISOString();
      if (!result.dueDate) delete result.dueDate;
      if (!result.dueAt) delete result.dueAt;
    }
    for (const key of ["description", "notes"])
      if (key in result && result[key] === null) result[key] = "";
    onSave(result);
  }
  return (
    <dialog
      ref={dialog}
      className="editor"
      onCancel={onClose}
      aria-labelledby="editor-title"
    >
      <form onSubmit={submit}>
        <div className="section-heading">
          <span className="eyebrow">A TU MANERA</span>
          <button
            type="button"
            className="icon-button"
            aria-label="Cerrar formulario"
            onClick={onClose}
          >
            ×
          </button>
        </div>
        <h2 id="editor-title">
          {row ? "Editar" : "Crear"} {labels[collection]}.
        </h2>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {collection !== "schedule" && (
          <label>
            {collection === "topics" || collection === "agenda"
              ? "Título"
              : "Nombre"}
            <input
              name={
                collection === "topics" || collection === "agenda"
                  ? "title"
                  : "name"
              }
              maxLength={120}
              required
              autoFocus
              defaultValue={value(
                collection === "topics" || collection === "agenda"
                  ? "title"
                  : "name",
              )}
            />
          </label>
        )}
        {["agenda", "schedule", "topics"].includes(collection) && (
          <label>
            Materia
            <select
              name="subjectId"
              defaultValue={value("subjectId", state.subjectId)}
              required={collection !== "agenda"}
            >
              <option value="">
                {collection === "agenda"
                  ? "Sin materia"
                  : "Selecciona una materia"}
              </option>
              {subjects.map((s) => (
                <option key={s.id} value={s.id}>
                  {String(s.name)}
                </option>
              ))}
            </select>
          </label>
        )}
        {collection === "subjects" && (
          <>
            <label>
              Descripción
              <textarea
                name="description"
                maxLength={1000}
                defaultValue={value("description")}
              />
            </label>
            <label>
              Periodo
              <select name="periodId" defaultValue={value("periodId")}>
                <option value="">Materia independiente</option>
                {periods.map((p) => (
                  <option key={p.id} value={p.id}>
                    {String(p.name)}
                  </option>
                ))}
              </select>
            </label>
            <fieldset>
              <legend>Elige una ilustración</legend>
              <div className="illustration-picker">
                {illustrations.map(([id, label]) => (
                  <label key={id} title={label}>
                    <input
                      type="radio"
                      name="illustrationId"
                      value={id}
                      defaultChecked={value("illustrationId", "grid") === id}
                    />
                    <Illustration id={id} />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </fieldset>
            <label>
              Acento
              <select name="accentId" defaultValue={value("accentId", "gold")}>
                <option value="gold">Oro</option>
                <option value="navy">Azul</option>
                <option value="sand">Arena</option>
              </select>
            </label>
          </>
        )}
        {collection === "periods" && (
          <div className="form-grid">
            <label>
              Inicio
              <input
                type="date"
                name="startDate"
                defaultValue={value("startDate")}
              />
            </label>
            <label>
              Fin
              <input
                type="date"
                name="endDate"
                defaultValue={value("endDate")}
              />
            </label>
          </div>
        )}
        {collection === "topics" && (
          <>
            <label>
              Orden
              <input
                name="order"
                type="number"
                min={0}
                defaultValue={value("order", "0")}
              />
            </label>
            <fieldset>
              <legend>Prerrequisitos (opcionales)</legend>
              {topics
                .filter(
                  (t) =>
                    t.id !== row?.id &&
                    t.subjectId === (row?.subjectId || state.subjectId),
                )
                .map((t) => (
                  <label className="check-label" key={t.id}>
                    <input
                      type="checkbox"
                      name="prerequisiteIds"
                      value={t.id}
                      defaultChecked={(
                        (row?.prerequisiteIds as string[]) || []
                      ).includes(t.id)}
                    />
                    {String(t.title)}
                  </label>
                ))}
            </fieldset>
          </>
        )}
        {collection === "agenda" && (
          <>
            <div className="form-grid">
              <label>
                Tipo
                <select name="kind" defaultValue={value("kind", "task")}>
                  <option value="task">Tarea</option>
                  <option value="exam">Examen</option>
                  <option value="study">Estudio</option>
                  <option value="other">Otro</option>
                </select>
              </label>
              <label>
                Estado
                <select name="status" defaultValue={value("status", "pending")}>
                  <option value="pending">Pendiente</option>
                  <option value="done">Completado</option>
                </select>
              </label>
            </div>
            <p className="quiet">
              Elige día completo o fecha con hora. También puedes dejarlo sin
              fecha.
            </p>
            <div className="form-grid">
              <label>
                Día completo
                <input
                  name="dueDate"
                  type="date"
                  defaultValue={value("dueDate")}
                />
              </label>
              <label>
                Fecha y hora local
                <input
                  name="dueAt"
                  type="datetime-local"
                  defaultValue={
                    row?.dueAt
                      ? new Date(
                          new Date(String(row.dueAt)).getTime() -
                            new Date().getTimezoneOffset() * 60000,
                        )
                          .toISOString()
                          .slice(0, 16)
                      : ""
                  }
                />
              </label>
            </div>
            <label>
              Notas
              <textarea
                name="notes"
                maxLength={2000}
                defaultValue={value("notes")}
              />
            </label>
          </>
        )}
        {collection === "schedule" && (
          <>
            <label>
              Día
              <select name="weekday" defaultValue={value("weekday", "0")}>
                {[
                  "Lunes",
                  "Martes",
                  "Miércoles",
                  "Jueves",
                  "Viernes",
                  "Sábado",
                  "Domingo",
                ].map((d, i) => (
                  <option key={i} value={i}>
                    {d}
                  </option>
                ))}
              </select>
            </label>
            <div className="form-grid">
              <label>
                Desde
                <input
                  type="time"
                  name="localStart"
                  required
                  defaultValue={value("localStart", "09:00")}
                />
              </label>
              <label>
                Hasta
                <input
                  type="time"
                  name="localEnd"
                  required
                  defaultValue={value("localEnd", "10:00")}
                />
              </label>
            </div>
            <label>
              Zona horaria
              <input
                name="timezone"
                required
                defaultValue={value("timezone", "America/Mexico_City")}
              />
            </label>
            <label>
              Días sin clase (opcional)
              <input
                name="excludedDates"
                placeholder="2026-12-25, 2027-01-01"
                defaultValue={((row?.excludedDates as string[]) || []).join(
                  ", ",
                )}
              />
              <small>Fechas YYYY-MM-DD separadas por comas.</small>
            </label>
            <label>
              Notas
              <textarea name="notes" defaultValue={value("notes")} />
            </label>
          </>
        )}
        <div className="form-actions">
          <button type="button" className="secondary" onClick={onClose}>
            Cancelar
          </button>
          <button className="primary" disabled={busy}>
            {busy ? "Guardando…" : "Guardar"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
