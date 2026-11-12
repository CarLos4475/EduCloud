import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { api, studyRows } from "../../api";
import { Skeleton } from "../../components/Skeleton";
import { ProgressPanel } from "../progress/ProgressPanel";
import { ResourceViewer } from "./ResourceViewer";
import type { MaterialLite, ResourceDetail, ResourceRow, Kind } from "./types";
import { KINDS } from "./types";

const ACTIVE = ["queued", "running", "cancel_requested"];

export function ResourcesPanel({
  subjectId,
  openId,
  onOpened,
}: {
  subjectId: string;
  openId?: string | null;
  onOpened?: () => void;
}) {
  const [rows, setRows] = useState<ResourceRow[] | null>(null);
  const [materials, setMaterials] = useState<MaterialLite[]>([]);
  const [detail, setDetail] = useState<ResourceDetail | null>(null);
  const [opening, setOpening] = useState(false);
  const [creating, setCreating] = useState(false);
  const [kind, setKind] = useState<Kind>("summary");
  const [instruction, setInstruction] = useState("");
  const [chosen, setChosen] = useState<string[]>([]);
  const [allowGeneral, setAllowGeneral] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const key = useRef(crypto.randomUUID());

  const loadList = useCallback(async () => {
    try {
      const page = await studyRows<ResourceRow>(
        `/subjects/${subjectId}/resources`,
      );
      setRows(page.items);
    } catch (e) {
      setError((e as Error).message);
      setRows((current) => current ?? []);
    }
  }, [subjectId]);

  const loadMaterials = useCallback(
    () =>
      studyRows<MaterialLite>(`/subjects/${subjectId}/materials`)
        .then((page) => setMaterials(page.items))
        .catch(() => setMaterials([])),
    [subjectId],
  );

  useEffect(() => {
    void loadList();
    void loadMaterials();
  }, [loadList, loadMaterials]);

  const open = useCallback(async (id: string) => {
    setOpening(true);
    setError("");
    try {
      setDetail(await api<ResourceDetail>(`/resources/${id}`));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setOpening(false);
    }
  }, []);

  useEffect(() => {
    if (!openId) return;
    void open(openId).then(() => onOpened?.());
  }, [openId, open, onOpened]);

  // While something is being prepared, check back until it is ready.
  const latest = detail?.versions[detail.versions.length - 1];
  const waiting = Boolean(latest && ACTIVE.includes(latest.status));
  useEffect(() => {
    if (!detail || !waiting) return;
    const timer = setTimeout(() => {
      api<ResourceDetail>(`/resources/${detail.id}`)
        .then((next) => {
          setDetail(next);
          if (!ACTIVE.includes(next.latestStatus ?? "")) void loadList();
        })
        .catch(() => undefined);
    }, 2000);
    return () => clearTimeout(timer);
  }, [detail, waiting, loadList]);

  async function create(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const value = await api<ResourceDetail>("/resources", {
        method: "POST",
        headers: { "Idempotency-Key": key.current },
        body: JSON.stringify({
          subjectId,
          kind,
          instruction,
          materialIds: chosen,
          allowGeneral,
        }),
      });
      key.current = crypto.randomUUID();
      setDetail(value);
      setCreating(false);
      setInstruction("");
      void loadList();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const usable = materials.filter((m) =>
    ["ready", "partial"].includes(m.status),
  );

  if (detail)
    return (
      <section className="resources-panel" aria-label="Recurso de estudio">
        <button
          className="text-button"
          onClick={() => {
            setDetail(null);
            void loadList();
          }}
        >
          ← Volver a mis recursos
        </button>
        <ResourceViewer
          detail={detail}
          onChange={setDetail}
          onRefreshList={() => void loadList()}
          onClose={() => {
            setDetail(null);
            void loadList();
          }}
        />
      </section>
    );

  return (
    <section className="resources-panel" aria-labelledby="resources-title">
      <div className="section-heading">
        <div>
          <span className="eyebrow">ESTUDIA A TU MANERA</span>
          <h2 id="resources-title">Recursos para estudiar</h2>
        </div>
        {!creating && (
          <button
            className="primary"
            onClick={() => {
              setCreating(true);
              void loadMaterials();
            }}
          >
            + Crear un recurso
          </button>
        )}
      </div>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {!creating && (
        <ProgressPanel subjectId={subjectId} onOpen={(id) => void open(id)} />
      )}
      {creating && (
        <form className="resource-composer" onSubmit={create}>
          <fieldset className="kind-picker">
            <legend>¿Qué quieres crear?</legend>
            {KINDS.map((k) => (
              <label
                key={k.id}
                className={`kind-card ${kind === k.id ? "selected" : ""}`}
              >
                <input
                  type="radio"
                  name="kind"
                  checked={kind === k.id}
                  onChange={() => setKind(k.id)}
                />
                <strong>{k.label}</strong>
                <span>{k.hint}</span>
              </label>
            ))}
          </fieldset>
          <label>
            ¿Algo en particular? (opcional)
            <textarea
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              maxLength={1000}
              rows={2}
              placeholder="Por ejemplo: enfócate en la ley de Ohm"
            />
          </label>
          <fieldset className="source-picker">
            <legend>¿Con qué apuntes?</legend>
            {usable.length ? (
              usable.map((m) => (
                <label className="check-label" key={m.id}>
                  <input
                    type="checkbox"
                    checked={chosen.includes(m.id)}
                    onChange={(e) =>
                      setChosen((current) =>
                        e.target.checked
                          ? [...current, m.id]
                          : current.filter((id) => id !== m.id),
                      )
                    }
                  />
                  {m.name}
                </label>
              ))
            ) : (
              <p className="quiet-panel">
                Aún no tienes apuntes listos en esta materia. Sube uno arriba o
                permite usar conocimiento general.
              </p>
            )}
          </fieldset>
          <label className="check-label">
            <input
              type="checkbox"
              checked={allowGeneral}
              onChange={(e) => setAllowGeneral(e.target.checked)}
            />
            Puedes complementar con conocimiento general si hace falta.
          </label>
          <div className="button-row">
            <button
              className="primary"
              disabled={busy || (!chosen.length && !allowGeneral)}
            >
              {busy ? "Preparando…" : "Crear recurso"}
            </button>
            <button
              type="button"
              className="secondary"
              onClick={() => setCreating(false)}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}
      {rows === null ? (
        <div className="resource-grid" role="status" aria-label="Cargando">
          {[0, 1, 2].map((i) => (
            <div key={i} className="resource-card skeleton-card">
              <Skeleton lines={3} />
            </div>
          ))}
        </div>
      ) : rows.length ? (
        <div className="resource-grid">
          {rows.map((r) => {
            const meta = KINDS.find((k) => k.id === r.kind);
            const pending = ACTIVE.includes(r.latestStatus ?? "");
            return (
              <button
                key={r.id}
                className="resource-card"
                disabled={opening}
                onClick={() => void open(r.id)}
              >
                <span className="resource-kind">{meta?.label ?? r.kind}</span>
                <strong>{r.title}</strong>
                <small>
                  {pending
                    ? "Preparándose…"
                    : r.latestStatus === "failed"
                      ? r.currentVersionId
                        ? "Última versión sin completar"
                        : "No se pudo crear"
                      : `${r.versionCount} ${r.versionCount === 1 ? "versión" : "versiones"}`}
                </small>
              </button>
            );
          })}
        </div>
      ) : (
        !creating && (
          <div className="empty-state">
            <h3>Todavía no tienes recursos.</h3>
            <p>
              Crea un resumen, tarjetas o un cuestionario a partir de tus
              apuntes.
            </p>
          </div>
        )
      )}
    </section>
  );
}
