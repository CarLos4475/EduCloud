import { FormEvent, useEffect, useRef, useState } from "react";
import { api } from "../../api";
import { SafeMarkdown } from "../../components/SafeMarkdown";
import { Skeleton } from "../../components/Skeleton";
import type { Citation, ResourceDetail, ResourceVersion } from "./types";
import { KINDS } from "./types";

const ACTIVE = ["queued", "running", "cancel_requested"];
const RENDERER_URL =
  import.meta.env.VITE_RENDERER_URL || "http://127.0.0.1:5174";

/* ---------- viewers for each kind ---------- */

function Summary({ content }: { content: any }) {
  return (
    <article className="resource-body">
      <div className="resource-lead">
        <SafeMarkdown text={content.overview} />
      </div>
      {content.sections?.map((s: any, i: number) => (
        <section key={i}>
          <h3>{s.heading}</h3>
          <SafeMarkdown text={s.body} />
        </section>
      ))}
      {content.keyPoints?.length > 0 && (
        <section className="key-points">
          <h3>Para recordar</h3>
          <ul>
            {content.keyPoints.map((p: string, i: number) => (
              <li key={i}>
                <SafeMarkdown text={p} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}

function Concepts({ content }: { content: any }) {
  return (
    <div className="concept-list">
      {content.concepts.map((c: any, i: number) => (
        <article className="concept-card" key={i}>
          <h3>{c.term}</h3>
          <SafeMarkdown text={c.definition} />
          {c.example && (
            <div className="concept-example">
              <strong>Ejemplo</strong>
              <SafeMarkdown text={c.example} />
            </div>
          )}
        </article>
      ))}
    </div>
  );
}

function Flashcards({
  content,
  versionId,
}: {
  content: any;
  versionId: string;
}) {
  const cards = content.cards as { front: string; back: string }[];
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [marks, setMarks] = useState<Record<string, string>>({});
  const [note, setNote] = useState("");
  useEffect(() => {
    api<{ cards: Record<string, string> }>(
      `/resources/versions/${versionId}/review`,
    )
      .then((review) => setMarks(review.cards))
      .catch(() => undefined);
  }, [versionId]);
  const card = cards[index];
  const go = (step: number) => {
    setFlipped(false);
    setIndex((index + step + cards.length) % cards.length);
  };
  const mark = (value: "known" | "again") => {
    const next = { ...marks, [String(index)]: value };
    setMarks(next);
    api(`/resources/versions/${versionId}/review`, {
      method: "PUT",
      body: JSON.stringify({ cards: next }),
    })
      .then(() => setNote(""))
      .catch(() => setNote("No pudimos guardar tu repaso. Intenta de nuevo."));
    go(1);
  };
  const known = Object.values(marks).filter((v) => v === "known").length;
  const again = Object.values(marks).filter((v) => v === "again").length;
  const current = marks[String(index)];
  return (
    <div className="flashcards">
      <p role="status" className="flash-count">
        Tarjeta {index + 1} de {cards.length} · Sabidas: {known} · Por repasar:{" "}
        {again}
      </p>
      <button
        className={`flashcard ${flipped ? "flipped" : ""}`}
        onClick={() => setFlipped(!flipped)}
        aria-label={flipped ? "Ver la pregunta" : "Ver la respuesta"}
      >
        <small>{flipped ? "Respuesta" : "Pregunta"}</small>
        <SafeMarkdown text={flipped ? card.back : card.front} />
        <span className="flash-hint">
          {current === "known"
            ? "Marcada como sabida · "
            : current === "again"
              ? "Marcada para repasar · "
              : ""}
          {flipped ? "Toca para volver" : "Toca para voltear"}
        </span>
      </button>
      {flipped && (
        <div className="button-row">
          <button className="secondary" onClick={() => mark("again")}>
            Repasar otra vez
          </button>
          <button className="primary" onClick={() => mark("known")}>
            La sabía
          </button>
        </div>
      )}
      <div className="button-row">
        <button className="text-button" onClick={() => go(-1)}>
          Anterior
        </button>
        <button className="text-button" onClick={() => go(1)}>
          Saltar
        </button>
      </div>
      {note && (
        <p role="alert" className="form-error">
          {note}
        </p>
      )}
    </div>
  );
}

function Quiz({ content, versionId }: { content: any; versionId: string }) {
  const questions = content.questions as {
    prompt: string;
    options: string[];
    correctIndex: number;
    explanation: string;
  }[];
  const [answers, setAnswers] = useState<(number | null)[]>(
    questions.map(() => null),
  );
  const [saved, setSaved] = useState<{ score: number; total: number } | null>(
    null,
  );
  const [problem, setProblem] = useState("");
  const done = answers.every((a) => a !== null);
  useEffect(() => {
    if (!done || saved) return;
    api<{ score: number; total: number }>(
      `/resources/versions/${versionId}/attempts`,
      { method: "POST", body: JSON.stringify({ answers }) },
    )
      .then(setSaved)
      .catch(() => setProblem("No pudimos guardar este intento."));
  }, [done, saved, answers, versionId]);
  return (
    <div className="quiz">
      {questions.map((q, i) => {
        const answered = answers[i] !== null;
        return (
          <div
            className="quiz-question"
            role="group"
            aria-labelledby={`q-${i}`}
            key={i}
          >
            <div id={`q-${i}`} className="quiz-prompt">
              <span>{i + 1}.</span> <SafeMarkdown text={q.prompt} />
            </div>
            {q.options.map((option, j) => {
              const state = !answered
                ? ""
                : j === q.correctIndex
                  ? "right"
                  : answers[i] === j
                    ? "wrong"
                    : "";
              return (
                <button
                  key={j}
                  className={`quiz-option ${state}`}
                  disabled={answered}
                  onClick={() =>
                    setAnswers((a) => a.map((v, k) => (k === i ? j : v)))
                  }
                >
                  <SafeMarkdown text={option} />
                </button>
              );
            })}
            {answered && (
              <div role="status" className="quiz-feedback">
                <strong>
                  {answers[i] === q.correctIndex ? "¡Bien!" : "Casi."}
                </strong>
                <SafeMarkdown text={q.explanation} />
              </div>
            )}
          </div>
        );
      })}
      {done && (
        <p role="status" className="quiz-score">
          {saved
            ? `Acertaste ${saved.score} de ${saved.total}. Quedó guardado en tu progreso.`
            : problem || "Guardando tu resultado…"}{" "}
          <button
            className="text-button"
            onClick={() => {
              setAnswers(questions.map(() => null));
              setSaved(null);
              setProblem("");
            }}
          >
            Intentarlo otra vez
          </button>
        </p>
      )}
    </div>
  );
}

function Interactive({ version }: { version: ResourceVersion }) {
  const frame = useRef<HTMLIFrameElement>(null);
  const channel = useRef(crypto.randomUUID());
  const sequence = useRef(0);
  const revision = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const send = (type: string, payload: unknown) =>
    frame.current?.contentWindow?.postMessage(
      {
        protocolVersion: 1,
        channelId: channel.current,
        sequence: ++sequence.current,
        type,
        payload,
      },
      RENDERER_URL,
    );
  const load = async () => {
    channel.current = crypto.randomUUID();
    sequence.current = 0;
    let state = version.content.initialState;
    try {
      const saved = await api<{
        state: Record<string, unknown>;
        revision: number;
      }>(`/resources/versions/${version.id}/state`);
      revision.current = saved.revision;
      if (saved.revision > 0) state = saved.state;
    } catch {
      // Si no se puede leer el avance, empieza desde cero.
    }
    send("load", { package: version.content, state });
  };
  useEffect(() => {
    void load();
    return () => clearTimeout(timer.current);
  }, [version.id]); // eslint-disable-line react-hooks/exhaustive-deps
  const [height, setHeight] = useState(520);
  const [saved, setSaved] = useState("");
  useEffect(() => {
    const listen = (event: MessageEvent) => {
      if (
        event.origin !== RENDERER_URL ||
        event.source !== frame.current?.contentWindow ||
        event.data?.channelId !== channel.current
      )
        return;
      if (event.data.type === "size") {
        const next = Number(event.data.payload?.height);
        if (Number.isFinite(next))
          setHeight(Math.min(1600, Math.max(320, next)));
      } else if (event.data.type === "state") {
        const state = event.data.payload;
        clearTimeout(timer.current);
        timer.current = setTimeout(() => {
          api<{ revision: number }>(`/resources/versions/${version.id}/state`, {
            method: "PUT",
            body: JSON.stringify({
              state,
              expectedRevision: revision.current || undefined,
            }),
          })
            .then((value) => {
              revision.current = value.revision;
              setSaved("Tu avance se guarda solo.");
            })
            .catch(() => setSaved("No pudimos guardar tu avance."));
        }, 800);
      }
    };
    window.addEventListener("message", listen);
    return () => window.removeEventListener("message", listen);
  }, [version.id]);
  return (
    <div className="interactive">
      <iframe
        ref={frame}
        style={{ height }}
        title={version.content.title}
        sandbox="allow-scripts allow-same-origin"
        src={RENDERER_URL}
        onLoad={() => void load()}
      />
      <div className="button-row">
        <button
          className="secondary"
          onClick={() => {
            clearTimeout(timer.current);
            void api(`/resources/versions/${version.id}/state`, {
              method: "DELETE",
            })
              .then(() => {
                revision.current = 0;
                setSaved("");
              })
              .catch(() => undefined);
            send("reset", {});
          }}
        >
          Reiniciar
        </button>
        {saved && <small role="status">{saved}</small>}
      </div>
      <details className="alt-text">
        <summary>Descripción en texto</summary>
        <p>{version.textAlternative}</p>
      </details>
    </div>
  );
}

/* ---------- the viewer ---------- */

export function ResourceViewer({
  detail,
  onChange,
  onRefreshList,
  onClose,
}: {
  detail: ResourceDetail;
  onChange: (d: ResourceDetail) => void;
  onRefreshList: () => void;
  onClose: () => void;
}) {
  const last = detail.versions[detail.versions.length - 1];
  const [selectedId, setSelectedId] = useState(
    detail.currentVersionId ?? last?.id,
  );
  const [title, setTitle] = useState(detail.title);
  const [editingTitle, setEditingTitle] = useState(false);
  const [request, setRequest] = useState("");
  const [general, setGeneral] = useState(false);
  const [acceptCharge, setAcceptCharge] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const key = useRef(crypto.randomUUID());

  // Follow new versions as they appear and finish.
  const count = detail.versions.length;
  useEffect(() => {
    setSelectedId(last?.id);
  }, [count]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (last?.status === "succeeded") setSelectedId(last.id);
  }, [last?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  const version =
    detail.versions.find((v) => v.id === selectedId) ?? last ?? undefined;
  const kind = KINDS.find((k) => k.id === detail.kind);
  const reload = async () =>
    onChange(await api<ResourceDetail>(`/resources/${detail.id}`));

  async function run(action: () => Promise<unknown>) {
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

  const rename = (e: FormEvent) => {
    e.preventDefault();
    void run(async () => {
      onChange(
        await api<ResourceDetail>(`/resources/${detail.id}`, {
          method: "PATCH",
          body: JSON.stringify({
            expectedRevision: detail.revision,
            title: title.trim() || detail.title,
          }),
        }),
      );
      setEditingTitle(false);
      onRefreshList();
    });
  };

  const askChange = (e: FormEvent) => {
    e.preventDefault();
    void run(async () => {
      onChange(
        await api<ResourceDetail>(`/resources/${detail.id}/versions`, {
          method: "POST",
          headers: { "Idempotency-Key": key.current },
          body: JSON.stringify({ instruction: request, allowGeneral: general }),
        }),
      );
      key.current = crypto.randomUUID();
      setRequest("");
    });
  };

  const waiting = version && ACTIVE.includes(version.status);
  const failed = version && ["failed", "canceled"].includes(version.status);

  return (
    <div className="resource-viewer">
      <header className="resource-header">
        <span className="resource-kind">{kind?.label}</span>
        {editingTitle ? (
          <form className="rename-form" onSubmit={rename}>
            <label>
              <span className="visually-hidden">Nombre del recurso</span>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={120}
                autoFocus
              />
            </label>
            <button className="primary" disabled={busy}>
              Guardar
            </button>
          </form>
        ) : (
          <>
            <h2>{detail.title}</h2>
            <button
              className="text-button"
              onClick={() => setEditingTitle(true)}
            >
              Cambiar nombre
            </button>
          </>
        )}
        <button
          className="text-button"
          disabled={busy}
          onClick={() =>
            void run(async () => {
              await api(`/resources/${detail.id}`, {
                method: "PATCH",
                body: JSON.stringify({
                  expectedRevision: detail.revision,
                  archived: true,
                }),
              });
              onClose();
            })
          }
        >
          Archivar
        </button>
      </header>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {detail.versions.length > 1 && (
        <nav className="version-tabs" aria-label="Versiones">
          {detail.versions.map((v) => (
            <button
              key={v.id}
              className={v.id === version?.id ? "selected" : ""}
              aria-current={v.id === version?.id}
              onClick={() => setSelectedId(v.id)}
            >
              Versión {v.number}
              {ACTIVE.includes(v.status)
                ? " · en camino"
                : v.status === "succeeded"
                  ? ""
                  : " · sin completar"}
            </button>
          ))}
        </nav>
      )}
      {version?.instruction && (
        <p className="quiet-panel">Pediste: “{version.instruction}”</p>
      )}
      {waiting && (
        <div role="status" className="resource-waiting">
          <p>
            {version.status === "queued"
              ? "Tu recurso está en la fila…"
              : "Estamos preparando tu recurso…"}
          </p>
          <Skeleton lines={5} />
          <button
            className="text-button"
            onClick={() =>
              void run(async () => {
                await api(`/jobs/${version.jobId}/cancel`, { method: "POST" });
                await reload();
              })
            }
          >
            Cancelar
          </button>
        </div>
      )}
      {failed && (
        <div className="resource-failed">
          <p>
            {version.status === "canceled"
              ? "Cancelaste esta versión."
              : "No pudimos crear esta versión. Puedes intentarlo de nuevo."}
          </p>
          {detail.currentVersionId && (
            <button
              className="text-button"
              onClick={() => setSelectedId(detail.currentVersionId!)}
            >
              Ver la última versión que sí quedó
            </button>
          )}
          {version.usageUnknown && (
            <label className="check-label">
              <input
                type="checkbox"
                checked={acceptCharge}
                onChange={(e) => setAcceptCharge(e.target.checked)}
              />
              Puede que el intento anterior ya cuente en tu límite de hoy.
              Quiero intentarlo de nuevo.
            </label>
          )}
          <button
            className="secondary"
            disabled={busy || (version.usageUnknown && !acceptCharge)}
            onClick={() =>
              void run(async () => {
                await api(`/jobs/${version.jobId}/retry`, {
                  method: "POST",
                  body: JSON.stringify({ acceptPossibleCharge: acceptCharge }),
                });
                await reload();
              })
            }
          >
            Intentar de nuevo
          </button>
        </div>
      )}
      {version?.status === "succeeded" && version.content && (
        <>
          {version.sourcesChanged && (
            <p role="status" className="quiet-panel">
              Tus apuntes cambiaron después de crear esto. Pide una versión
              nueva para ponerlo al día.
            </p>
          )}
          {detail.kind === "summary" && <Summary content={version.content} />}
          {detail.kind === "concepts" && <Concepts content={version.content} />}
          {detail.kind === "flashcards" && (
            <Flashcards
              key={version.id}
              content={version.content}
              versionId={version.id}
            />
          )}
          {detail.kind === "quiz" && (
            <Quiz
              key={version.id}
              content={version.content}
              versionId={version.id}
            />
          )}
          {detail.kind === "interactive" && <Interactive version={version} />}
          <Sources items={version.citations} />
        </>
      )}
      {!waiting && (
        <form className="resource-change" onSubmit={askChange}>
          <label>
            ¿Quieres cambiar algo?
            <textarea
              value={request}
              onChange={(e) => setRequest(e.target.value)}
              maxLength={1000}
              rows={2}
              required
              placeholder="Por ejemplo: hazlo más corto, con más ejemplos…"
            />
          </label>
          <label className="check-label">
            <input
              type="checkbox"
              checked={general}
              onChange={(e) => setGeneral(e.target.checked)}
            />
            Puedes complementar con conocimiento general.
          </label>
          <button className="secondary" disabled={busy || !request.trim()}>
            {busy ? "Enviando…" : "Crear una versión nueva"}
          </button>
        </form>
      )}
    </div>
  );
}

function place(locator: string) {
  const [kind, n] = locator.split(":");
  const label: Record<string, string> = {
    page: "Página",
    slide: "Diapositiva",
    section: "Tus apuntes",
  };
  if (kind === "section") return label.section;
  return label[kind] && n ? `${label[kind]} ${n}` : "Tus apuntes";
}

function Sources({ items }: { items: Citation[] }) {
  if (!items.length) return null;
  return (
    <section className="resource-sources">
      <h3>De dónde sale</h3>
      <ul>
        {items.map((c, i) => (
          <li key={i}>
            <strong>{place(c.locator)}</strong>
            {c.quote && <q>{c.quote}</q>}
          </li>
        ))}
      </ul>
    </section>
  );
}
