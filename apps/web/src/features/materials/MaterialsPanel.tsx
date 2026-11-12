import { FormEvent, useEffect, useRef, useState } from "react";
import { api, authorizedFetch, studyRows, Row } from "../../api";
import { Skeleton } from "../../components/Skeleton";

export type SourceRef = {
  materialId: string;
  extractionVersion: string;
  blockId: string;
  locator: string;
  quote?: string;
  sourceId?: string;
};
export type Block = SourceRef & {
  text: string;
  status: string;
  warning?: string;
};
export type Material = Row & {
  name: string;
  status: string;
  mediaType: string;
  jobId?: string;
  blocks?: Block[];
  topicIds?: string[];
  suggestedTopicIds?: string[];
};
const labels: Record<string, string> = {
  uploading: "Carga pendiente",
  queued: "En la fila",
  processing: "Procesando",
  needs_review: "Revisa la transcripción",
  ready: "Listo para estudiar",
  partial: "Cobertura parcial",
  failed: "No se pudo procesar",
};
export function referenceLabel(locator: string) {
  const [kind, number] = locator.split(":");
  return `${({ page: "Página", slide: "Diapositiva", section: "Sección", image: "Imagen" } as Record<string, string>)[kind] || "Referencia"} ${number || ""}`;
}
function stageLabel(stage: string) {
  const page = stage.match(/^page:(\d+)\/(\d+)$/);
  if (page) return `Página ${page[1]} de ${page[2]}`;
  return (
    (
      {
        queued: "En la fila",
        started: "Empezando",
        transcribing: "Leyendo tus apuntes",
        receiving: "Preparando la respuesta",
        succeeded: "Listo",
        needs_review: "Por revisar",
        failed: "Fallido",
        canceled: "Cancelado",
        cancel_requested: "Cancelando",
      } as Record<string, string>
    )[stage] || "Procesando"
  );
}

export async function loadOriginal(materialId: string): Promise<string> {
  const response = await authorizedFetch(`/materials/${materialId}/original`);
  if (!response.ok) throw new Error("No se pudo abrir el archivo privado.");
  return URL.createObjectURL(await response.blob());
}

export function SourceViewer({
  source,
  onClose,
}: {
  source: SourceRef;
  onClose: () => void;
}) {
  const [block, setBlock] = useState<Block | null>(null);
  const [url, setUrl] = useState("");
  const [media, setMedia] = useState("");
  const [error, setError] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  useEffect(() => {
    let active = true;
    let objectUrl = "";
    const { materialId, extractionVersion, blockId, locator, quote } = source;
    void Promise.all([
      api<Block>("/citations/resolve", {
        method: "POST",
        body: JSON.stringify({
          materialId,
          extractionVersion,
          blockId,
          locator,
          quote,
        }),
      }),
      api<Material>(`/materials/${source.materialId}`),
      loadOriginal(source.materialId),
    ])
      .then(([value, material, original]) => {
        objectUrl = original;
        if (active) {
          setBlock(value);
          setUrl(original);
          setMedia(material.mediaType);
        } else URL.revokeObjectURL(original);
      })
      .catch((e) => {
        if (active) setError((e as Error).message);
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [source]);
  return (
    <dialog
      ref={dialog}
      aria-label="Fuente citada"
      aria-modal="true"
      className="source-viewer"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
    >
      <button
        className="secondary"
        onClick={onClose}
        autoFocus
        aria-label="Cerrar fuente"
      >
        Cerrar fuente ×
      </button>
      <h2>La página detrás de la respuesta.</h2>
      {error && <p role="alert">{error}</p>}
      {block ? (
        <>
          <p className="eyebrow">
            {referenceLabel(block.locator)} · Versión{" "}
            {block.extractionVersion.slice(0, 8)}
          </p>
          {source.quote && <blockquote>{source.quote}</blockquote>}
          <pre className="source-text">{block.text}</pre>
          {url && media.startsWith("image/") && (
            <img className="original-image" src={url} alt="Apunte original" />
          )}
          {url && media === "application/pdf" && (
            <iframe
              title="Página del PDF original"
              sandbox=""
              className="pdf-preview"
              src={`${url}#page=${Number(block.locator.split(":")[1]) || 1}`}
            />
          )}
          {url && (
            <a
              className="secondary"
              href={url}
              download={`material.${media === "application/pdf" ? "pdf" : media.includes("presentation") ? "pptx" : media.startsWith("image/") ? media.split("/")[1] : "txt"}`}
            >
              Descargar original
            </a>
          )}
        </>
      ) : (
        <Skeleton lines={5} label="Abriendo tus apuntes…" />
      )}
    </dialog>
  );
}

export function MaterialsPanel({
  subjectId,
  topics,
  onTopicsChanged,
}: {
  subjectId: string;
  topics: Row[];
  onTopicsChanged: () => void;
}) {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [current, setCurrent] = useState<Material | null>(null);
  const [page, setPage] = useState("block-1");
  const [text, setText] = useState("");
  const [topicIds, setTopicIds] = useState<string[]>([]);
  const [noteTitle, setNoteTitle] = useState("");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [source, setSource] = useState<SourceRef | null>(null);
  const [newTopic, setNewTopic] = useState("");
  const [job, setJob] = useState<Row | null>(null);
  const [acceptCharge, setAcceptCharge] = useState(false);
  useEffect(() => {
    let active = true,
      running = false;
    const load = async () => {
      if (running) return;
      running = true;
      try {
        const value = await studyRows<Material>(
          `/subjects/${subjectId}/materials`,
        );
        if (active) setMaterials(value.items);
      } catch (e) {
        if (active) setError((e as Error).message);
      } finally {
        running = false;
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, [subjectId]);
  const processing = materials.some(
    (m) => Boolean(m.jobId) && ["queued", "processing"].includes(m.status),
  );
  useEffect(() => {
    if (!processing) return;
    const controller = new AbortController();
    let running = false;
    const timer = setInterval(() => {
      if (running) return;
      running = true;
      void studyRows<Material>(`/subjects/${subjectId}/materials`, {
        signal: controller.signal,
      })
        .then((value) => {
          if (!controller.signal.aborted) setMaterials(value.items);
        })
        .catch((e) => {
          if (!controller.signal.aborted) setError((e as Error).message);
        })
        .finally(() => {
          running = false;
        });
    }, 2000);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [subjectId, processing]);
  useEffect(() => {
    if (
      !current?.jobId ||
      !job ||
      !["queued", "running", "cancel_requested"].includes(String(job.status))
    )
      return;
    const controller = new AbortController();
    const timer = setInterval(() => {
      void api<Row>(`/jobs/${current.jobId}`, { signal: controller.signal })
        .then(async (value) => {
          if (controller.signal.aborted) return;
          setJob(value);
          if (
            !["queued", "running", "cancel_requested"].includes(
              String(value.status),
            )
          ) {
            clearInterval(timer);
            const material = await api<Material>(`/materials/${current.id}`, {
              signal: controller.signal,
            });
            if (!controller.signal.aborted) {
              setCurrent(material);
              const first = material.blocks?.[0];
              setPage(first?.blockId || "block-1");
              setText(first?.text || "");
            }
          }
        })
        .catch((e) => {
          if (!controller.signal.aborted) setError((e as Error).message);
        });
    }, 2000);
    return () => {
      controller.abort();
      clearInterval(timer);
    };
  }, [current?.id, current?.jobId, job?.id]);
  async function refresh() {
    setMaterials(
      (await studyRows<Material>(`/subjects/${subjectId}/materials`)).items,
    );
  }
  async function perform(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function upload(file: File, displayName?: string) {
    await perform(async () => {
      if (!file.size || file.size > 20 * 1024 * 1024)
        throw new Error("El archivo debe tener entre 1 byte y 20 MiB.");
      const bytes = await file.arrayBuffer();
      const hash = Array.from(
        new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
      )
        .map((n) => n.toString(16).padStart(2, "0"))
        .join("");
      const mediaType =
        file.type ||
        (
          {
            pdf: "application/pdf",
            pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            md: "text/markdown",
            txt: "text/plain",
          } as Record<string, string>
        )[file.name.split(".").pop() || ""];
      const ticket = await api<{
        uploadId: string;
        signedUrl: string;
        requiredHeaders: Record<string, string>;
      }>(`/subjects/${subjectId}/uploads`, {
        method: "POST",
        body: JSON.stringify({
          name: displayName || file.name,
          mediaType,
          size: file.size,
          sha256: hash,
        }),
      });
      const saved = await api<{ generation: string }>(ticket.signedUrl, {
        method: "PUT",
        headers: { ...ticket.requiredHeaders, "Content-Type": mediaType },
        body: file,
      });
      await api(`/uploads/${ticket.uploadId}/complete`, {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ generation: saved.generation }),
      });
      setNote("");
      setNoteTitle("");
      setNotice(
        "Material recibido. Puedes cerrar esta pantalla mientras se procesa.",
      );
      await refresh();
    });
  }
  async function open(material: Material) {
    await perform(async () => {
      const value = await api<Material>(`/materials/${material.id}`);
      setCurrent(value);
      setTopicIds(value.topicIds || []);
      const first = value.blocks?.[0];
      setPage(first?.blockId || "block-1");
      setText(first?.text || "");
      setJob(value.jobId ? await api<Row>(`/jobs/${value.jobId}`) : null);
    });
  }
  async function saveTranscript(event: FormEvent) {
    event.preventDefault();
    if (!current) return;
    await perform(async () => {
      await api(`/materials/${current.id}/transcript`, {
        method: "PATCH",
        body: JSON.stringify({
          expectedRevision: current.revision,
          edits: text.trim() ? [{ blockId: page, text }] : [],
          topicIds,
        }),
      });
      await refresh();
      await open(current);
      setNotice(
        "Nueva versión guardada. Las citas anteriores conservan su texto.",
      );
    });
  }
  return (
    <section className="materials-panel" aria-label="Biblioteca de estudio">
      <div className="section-heading">
        <h2>Tu biblioteca de estudio</h2>
        <span className="eyebrow">TUS APUNTES PRIMERO</span>
      </div>
      <p>
        PDF, presentaciones, imágenes y notas. Las transcripciones dudosas
        necesitan tu revisión antes de usarse con el tutor.
      </p>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <div className="material-upload-grid">
        <label className="upload-drop">
          Subir material
          <input
            aria-label="Subir material"
            type="file"
            accept=".pdf,.pptx,.txt,.md,.png,.jpg,.jpeg,.webp"
            disabled={busy}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) void upload(file);
              e.target.value = "";
            }}
          />
          <small>Hasta 20 MiB por documento; 10 MiB por imagen.</small>
        </label>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void upload(
              new File([note], `${noteTitle.trim() || "Nota"}.txt`, {
                type: "text/plain",
              }),
              noteTitle.trim(),
            );
          }}
        >
          <label>
            Título de la nota
            <input
              value={noteTitle}
              onChange={(e) => setNoteTitle(e.target.value)}
              maxLength={160}
              required
            />
          </label>
          <label>
            Contenido de la nota
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
              maxLength={50000}
              required
            />
          </label>
          <button className="primary" disabled={busy}>
            {busy ? "Guardando…" : "Guardar nota"}
          </button>
        </form>
      </div>
      <div className="material-list">
        {materials.map((m) => (
          <article className="material-card" key={m.id}>
            <div>
              <h3>{m.name}</h3>
              <p role="status">
                {m.status === "failed" && m.error === "processing_canceled"
                  ? "Cancelado"
                  : labels[m.status] || "Procesando"}
              </p>
            </div>
            <button
              className="secondary"
              onClick={() => void open(m)}
              disabled={busy}
            >
              Abrir material
            </button>
          </article>
        ))}
      </div>
      {!materials.length && (
        <p className="quiet-panel">
          Todavía no hay apuntes. Guarda una nota o sube tu primer documento.
        </p>
      )}
      {current && (
        <section
          className="transcript-editor"
          aria-label="Revisión del material"
        >
          <button className="text-button" onClick={() => setCurrent(null)}>
            Cerrar material ×
          </button>
          <h3>{current.name}</h3>
          {current.blocks?.length ? (
            <form onSubmit={(e) => void saveTranscript(e)}>
              <label>
                Página o sección
                <select
                  value={page}
                  onChange={(e) => {
                    setPage(e.target.value);
                    setText(
                      current.blocks?.find((b) => b.blockId === e.target.value)
                        ?.text || "",
                    );
                  }}
                >
                  {current.blocks.map((b) => (
                    <option key={b.blockId} value={b.blockId}>
                      {referenceLabel(b.locator)} ·{" "}
                      {(
                        {
                          text: "Texto extraído",
                          reviewed: "Confirmado",
                          needs_review: "Por revisar",
                          failed: "Sin extraer",
                        } as Record<string, string>
                      )[b.status] || "Por revisar"}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Texto de la transcripción
                <textarea
                  rows={8}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  maxLength={30000}
                />
              </label>
              <p>
                Confirma el texto con el original, especialmente signos,
                exponentes y fórmulas. Guardar crea una versión nueva.
              </p>
              <fieldset>
                <legend>Asociar a temas (opcional)</legend>
                {topics.map((t) => (
                  <label className="check-label" key={t.id}>
                    <input
                      type="checkbox"
                      checked={topicIds.includes(t.id)}
                      onChange={(e) =>
                        setTopicIds(
                          e.target.checked
                            ? [...topicIds, t.id]
                            : topicIds.filter((id) => id !== t.id),
                        )
                      }
                    />
                    {String(t.title)}
                    {current.suggestedTopicIds?.includes(t.id)
                      ? " · sugerido"
                      : ""}
                  </label>
                ))}
              </fieldset>
              <div className="button-row">
                <button className="primary" disabled={busy || !text.trim()}>
                  Confirmar página y guardar versión
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={() => {
                    const block = current.blocks?.find(
                      (b) => b.blockId === page,
                    );
                    if (block)
                      setSource({
                        materialId: current.id,
                        extractionVersion: block.extractionVersion,
                        blockId: block.blockId,
                        locator: block.locator,
                      });
                  }}
                >
                  Ver original y texto
                </button>
              </div>
            </form>
          ) : (
            <p>
              Todavía estamos preparando tus apuntes. Puede tardar un poco o
              necesitar que lo intentes de nuevo.
            </p>
          )}
          <label>
            Nuevo tema para esta materia
            <input
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              maxLength={160}
            />
          </label>
          <button
            className="secondary"
            disabled={!newTopic.trim() || busy}
            onClick={() =>
              void perform(async () => {
                const value = await api<Row>("/topics", {
                  method: "POST",
                  body: JSON.stringify({ subjectId, title: newTopic }),
                });
                setTopicIds((ids) => [...ids, value.id]);
                setNewTopic("");
                onTopicsChanged();
              })
            }
          >
            Crear tema y seleccionarlo
          </button>
          {job && (
            <div className="job-detail">
              <p>Estado: {stageLabel(String(job.stage))}</p>
              {["queued", "running"].includes(String(job.status)) && (
                <button
                  className="secondary"
                  onClick={() =>
                    void perform(async () => {
                      await api(`/jobs/${job.id}/cancel`, { method: "POST" });
                      await open(current);
                    })
                  }
                >
                  Cancelar
                </button>
              )}
              {["failed", "canceled"].includes(String(job.status)) && (
                <>
                  <label className="check-label">
                    <input
                      type="checkbox"
                      checked={acceptCharge}
                      onChange={(e) => setAcceptCharge(e.target.checked)}
                    />
                    Entiendo que intentarlo de nuevo puede contar en mi límite
                    de hoy.
                  </label>
                  <button
                    className="secondary"
                    disabled={Boolean(job.usageUnknown) && !acceptCharge}
                    onClick={() =>
                      void perform(async () => {
                        await api(`/jobs/${job.id}/retry`, {
                          method: "POST",
                          body: JSON.stringify({
                            acceptPossibleCharge: acceptCharge,
                          }),
                        });
                        await refresh();
                        await open(current);
                      })
                    }
                  >
                    Reintentar procesamiento
                  </button>
                </>
              )}
            </div>
          )}
        </section>
      )}
      {source && (
        <SourceViewer source={source} onClose={() => setSource(null)} />
      )}
    </section>
  );
}
