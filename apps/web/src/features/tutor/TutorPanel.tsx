import { FormEvent, useEffect, useRef, useState } from "react";
import { api, authorizedFetch, studyRows, Row } from "../../api";
import { SafeMarkdown } from "../../components/SafeMarkdown";
import { Skeleton } from "../../components/Skeleton";
import { ArtImage, Icon, type IconName } from "../../components/Icons";
import {
  Material,
  SourceRef,
  SourceViewer,
  referenceLabel,
} from "../materials/MaterialsPanel";

type Conversation = Row & {
  title: string;
  subjectId: string;
  personalityId: string;
  assistanceMode: string;
  sourceMode: string;
  materialIds: string[];
  preferences: string;
};
type Turn = Row & {
  question: string;
  text: string;
  status: string;
  stage: string;
  citations: SourceRef[];
  jobId: string;
  sequence: number;
  needsConsent: boolean;
  usageUnknown: boolean;
  sourcesChanged: boolean;
  partialSources: boolean;
  usage?: { total_tokens?: number };
};
const terminal = (turn: Turn) =>
  ["succeeded", "failed", "canceled"].includes(turn.status);

const PERSONALITIES: {
  id: string;
  label: string;
  hint: string;
  icon: IconName;
}[] = [
  {
    id: "patient",
    label: "Paso a paso",
    hint: "Explica con calma y ejemplos.",
    icon: "steps",
  },
  {
    id: "socratic",
    label: "Preguntemos",
    hint: "Te guía con preguntas.",
    icon: "bulb",
  },
  {
    id: "direct",
    label: "Al grano",
    hint: "Respuestas claras y cortas.",
    icon: "bolt",
  },
];
const MODES: { id: string; label: string; icon: IconName }[] = [
  { id: "explain", label: "Explicación", icon: "book" },
  { id: "hints", label: "Pistas", icon: "compass" },
  { id: "solution", label: "Solución completa", icon: "check" },
  { id: "practice", label: "Práctica", icon: "target" },
];
const SUGGESTIONS = [
  "Explícame el tema paso a paso",
  "Dame un ejemplo resuelto",
  "¿Qué debo repasar primero?",
];

export function TutorPanel({
  subjects,
  initialSubjectId,
  onClose,
  onOpenResource,
}: {
  subjects: Row[];
  initialSubjectId: string | null;
  onClose: () => void;
  onOpenResource: (subjectId: string, resourceId: string) => void;
}) {
  const [subject, setSubject] = useState(
    initialSubjectId || subjects[0]?.id || "",
  );
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [conversationId, setConversationId] = useState("");
  const [materials, setMaterials] = useState<Material[]>([]);
  const [materialIds, setMaterialIds] = useState<string[]>([]);
  const [personalityId, setPersonalityId] = useState("patient");
  const [assistanceMode, setAssistanceMode] = useState("explain");
  const [sourceMode, setSourceMode] = useState("selected_material");
  const [preferences, setPreferences] = useState("");
  const [general, setGeneral] = useState(false);
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [error, setError] = useState("");
  const [connection, setConnection] = useState("");
  const [busy, setBusy] = useState(false);
  const [source, setSource] = useState<SourceRef | null>(null);
  const [acceptCharge, setAcceptCharge] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [made, setMade] = useState<{ turnId: string; id: string } | null>(null);
  async function makeResource(turn: Turn, kind: string) {
    setBusy(true);
    setError("");
    try {
      const created = await api<{ id: string }>("/resources", {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({
          subjectId: subject,
          kind,
          instruction: turn.question,
          materialIds,
          allowGeneral:
            general || sourceMode === "general" || !materialIds.length,
        }),
      });
      setMade({ turnId: turn.id, id: created.id });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const lastRequest = useRef<{ payload: string; key: string } | null>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const pending = turns.find((t) => !terminal(t));
  useEffect(() => {
    closeButton.current?.focus();
    return () => {
      window.speechSynthesis?.cancel();
    };
  }, []);
  useEffect(() => {
    let active = true;
    setConversationId("");
    setTurns([]);
    setMaterialIds([]);
    setError("");
    if (!subject) return;
    void Promise.all([
      studyRows<Conversation>(`/conversations?subjectId=${subject}`),
      studyRows<Material>(`/subjects/${subject}/materials`),
    ])
      .then(([chats, files]) => {
        if (active) {
          setConversations(chats.items);
          setMaterials(files.items);
        }
      })
      .catch((e) => {
        if (active) setError((e as Error).message);
      });
    return () => {
      active = false;
    };
  }, [subject]);
  useEffect(() => {
    if (!pending) return;
    const controller = new AbortController();
    let sequence = 0;
    const update = (turn: Turn) => {
      if (controller.signal.aborted) return;
      sequence = turn.sequence;
      setTurns((previous) =>
        previous.map((t) => (t.id === turn.id ? turn : t)),
      );
    };
    const recover = async () => {
      while (!controller.signal.aborted) {
        try {
          const response = await authorizedFetch(
            `/turns/${pending.id}/events?after=${sequence}`,
            { signal: controller.signal },
          );
          if (!response.ok || !response.body)
            throw new Error("No se pudo recuperar el turno.");
          setConnection("Conectado");
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = "";
          let done = false;
          while (!controller.signal.aborted) {
            const next = await reader.read();
            if (next.done) break;
            buffer += decoder.decode(next.value, { stream: true });
            let separator;
            while ((separator = buffer.indexOf("\n\n")) >= 0) {
              const event = buffer.slice(0, separator);
              buffer = buffer.slice(separator + 2);
              const data = event
                .split("\n")
                .find((line) => line.startsWith("data: "));
              if (data) {
                const value = JSON.parse(data.slice(6)) as Turn;
                update(value);
                if (terminal(value)) {
                  done = true;
                  break;
                }
              }
            }
            if (done) {
              await reader.cancel();
              break;
            }
          }
          if (done) break;
        } catch (e) {
          if (controller.signal.aborted) break;
          setConnection("Reconectando; tu pregunta sigue guardada.");
        }
        try {
          const value = await api<Turn>(`/turns/${pending.id}`, {
            signal: controller.signal,
          });
          update(value);
          if (terminal(value)) break;
        } catch {
          if (controller.signal.aborted) break;
        }
        await new Promise((resolve) => setTimeout(resolve, 1500));
      }
    };
    void recover();
    return () => controller.abort();
  }, [pending?.id]);

  async function chooseConversation(id: string) {
    setConversationId(id);
    setTurns([]);
    setError("");
    if (!id) return;
    setBusy(true);
    try {
      const [value, history] = await Promise.all([
        api<Conversation>(`/conversations/${id}`),
        studyRows<Turn>(`/conversations/${id}/turns`),
      ]);
      setMaterialIds(value.materialIds);
      setPersonalityId(value.personalityId);
      setAssistanceMode(value.assistanceMode);
      setSourceMode(value.sourceMode);
      setPreferences(value.preferences);
      setTurns(history.items);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function send(override?: { question: string; general: boolean }) {
    const query = override?.question || question;
    if (!query.trim() || !subject) return;
    setBusy(true);
    setError("");
    try {
      const context = {
        subjectId: subject,
        title: query.slice(0, 70),
        personalityId,
        assistanceMode,
        sourceMode,
        materialIds,
        preferences,
      };
      let id = conversationId;
      if (!id) {
        const chat = await api<Conversation>("/conversations", {
          method: "POST",
          body: JSON.stringify(context),
        });
        id = chat.id;
        setConversations((rows) => [...rows, chat]);
        setConversationId(id);
      } else {
        const current = await api<Conversation>(`/conversations/${id}`);
        await api(`/conversations/${id}`, {
          method: "PATCH",
          body: JSON.stringify({
            ...context,
            title: current.title,
            expectedRevision: current.revision,
          }),
        });
      }
      const body = {
        question: query,
        allowGeneralForTurn: override?.general ?? general,
      };
      const payload = JSON.stringify(body);
      if (lastRequest.current?.payload !== payload)
        lastRequest.current = { payload, key: crypto.randomUUID() };
      const turn = await api<Turn>(`/conversations/${id}/turns`, {
        method: "POST",
        headers: { "Idempotency-Key": lastRequest.current.key },
        body: payload,
      });
      setTurns((previous) =>
        previous.some((t) => t.id === turn.id) ? previous : [...previous, turn],
      );
      setQuestion("");
      setGeneral(false);
      lastRequest.current = null;
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    void send();
  }
  function speak(text: string) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    if (speaking) {
      setSpeaking(false);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "es-MX";
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
    setSpeaking(true);
  }
  return (
    <aside
      className="tutor-drawer study-tutor"
      role="dialog"
      aria-label="Tutor"
      aria-modal="false"
      onKeyDown={(e) => {
        if (e.key === "Escape" && !source) onClose();
      }}
    >
      <header className="tutor-heading">
        <div className="tutor-title">
          <span className="tutor-avatar large" aria-hidden="true">
            <ArtImage src="/art/tutor-avatar.png">
              <Icon name="spark" size={28} />
            </ArtImage>
          </span>
          <div>
            <span className="eyebrow">TU COMPAÑERO DE ESTUDIO</span>
            <h2>Vamos a entenderlo.</h2>
          </div>
        </div>
        <button
          ref={closeButton}
          className="icon-button"
          aria-label="Cerrar tutor"
          onClick={onClose}
        >
          <Icon name="close" />
        </button>
      </header>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {!subjects.length ? (
        <p className="tutor-none">
          Crea una materia para empezar a estudiar con tu tutor.
        </p>
      ) : (
        <>
          <div className="tutor-context">
            <div className="tutor-pickers">
              <label>
                <span className="field-label">
                  <Icon name="book" size={16} /> Materia del tutor
                </span>
                <select
                  value={subject}
                  disabled={busy || Boolean(pending)}
                  onChange={(e) => setSubject(e.target.value)}
                >
                  {subjects.map((s) => (
                    <option key={s.id} value={s.id}>
                      {String(s.name)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span className="field-label">
                  <Icon name="chat" size={16} /> Conversación
                </span>
                <select
                  value={conversationId}
                  disabled={busy || Boolean(pending)}
                  onChange={(e) => void chooseConversation(e.target.value)}
                >
                  <option value="">Nueva conversación</option>
                  {conversations.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="tutor-summary" aria-hidden="true">
              <span className="chip tone-gold">
                <Icon
                  name={
                    PERSONALITIES.find((p) => p.id === personalityId)?.icon ??
                    "steps"
                  }
                  size={14}
                />
                {PERSONALITIES.find((p) => p.id === personalityId)?.label}
              </span>
              <span className={`chip mode-${assistanceMode}`}>
                <Icon
                  name={
                    MODES.find((m) => m.id === assistanceMode)?.icon ?? "book"
                  }
                  size={14}
                />
                {MODES.find((m) => m.id === assistanceMode)?.label}
              </span>
              <span className="chip tone-navy">
                <Icon
                  name={sourceMode === "general" ? "globe" : "file"}
                  size={14}
                />
                {sourceMode === "general"
                  ? "Conocimiento general"
                  : `${materialIds.length} ${materialIds.length === 1 ? "apunte" : "apuntes"}`}
              </span>
            </div>
            <details open={!conversationId}>
              <summary>
                <Icon name="compass" size={18} /> Tu tutor y sus fuentes
              </summary>
              <div className="tutor-settings">
                <fieldset className="card-choices" disabled={Boolean(pending)}>
                  <legend>¿Cómo quieres que te ayude?</legend>
                  {PERSONALITIES.map((p) => (
                    <label
                      key={p.id}
                      className={`choice-card ${personalityId === p.id ? "selected" : ""}`}
                    >
                      <input
                        type="radio"
                        name="personality"
                        checked={personalityId === p.id}
                        onChange={() => setPersonalityId(p.id)}
                      />
                      <span className="choice-icon">
                        <ArtImage src={`/art/personalities/${p.id}.png`}>
                          <Icon name={p.icon} size={22} />
                        </ArtImage>
                      </span>
                      <strong>{p.label}</strong>
                      <small>{p.hint}</small>
                    </label>
                  ))}
                </fieldset>
                <fieldset className="segmented" disabled={Boolean(pending)}>
                  <legend>¿Qué necesitas ahora?</legend>
                  {MODES.map((m) => (
                    <label
                      key={m.id}
                      className={`segment mode-${m.id} ${assistanceMode === m.id ? "selected" : ""}`}
                    >
                      <input
                        type="radio"
                        name="assistance"
                        checked={assistanceMode === m.id}
                        onChange={() => setAssistanceMode(m.id)}
                      />
                      <ArtImage src={`/art/icons/mode-${m.id}.png`}>
                        <Icon name={m.icon} size={16} />
                      </ArtImage>
                      {m.label}
                    </label>
                  ))}
                </fieldset>
                <fieldset className="segmented" disabled={Boolean(pending)}>
                  <legend>¿De dónde saca la información?</legend>
                  {[
                    ["selected_material", "Mis apuntes primero", "file"],
                    ["general", "Conocimiento general", "globe"],
                  ].map(([id, label, icon]) => (
                    <label
                      key={id}
                      className={`segment ${sourceMode === id ? "selected" : ""}`}
                    >
                      <input
                        type="radio"
                        name="source-mode"
                        checked={sourceMode === id}
                        onChange={() => setSourceMode(id)}
                      />
                      <Icon name={icon as IconName} size={16} />
                      {label}
                    </label>
                  ))}
                </fieldset>
                <fieldset className="source-chips" disabled={Boolean(pending)}>
                  <legend>Apuntes que puede usar (hasta 10)</legend>
                  {materials
                    .filter((m) => ["ready", "partial"].includes(m.status))
                    .map((m) => (
                      <label
                        className={`source-chip ${materialIds.includes(m.id) ? "selected" : ""}`}
                        key={m.id}
                      >
                        <input
                          aria-label={`Fuente: ${m.name}`}
                          type="checkbox"
                          checked={materialIds.includes(m.id)}
                          onChange={(e) =>
                            setMaterialIds((ids) =>
                              e.target.checked
                                ? ids.length < 10
                                  ? [...ids, m.id]
                                  : ids
                                : ids.filter((id) => id !== m.id),
                            )
                          }
                        />
                        <Icon name="file" size={16} />
                        <span>
                          {m.name}
                          {m.status === "partial" ? " · cobertura parcial" : ""}
                        </span>
                      </label>
                    ))}
                  {!materials.some((m) =>
                    ["ready", "partial"].includes(m.status),
                  ) && (
                    <p>
                      No hay apuntes listos. Puedes subirlos desde tu materia o
                      autorizar conocimiento general.
                    </p>
                  )}
                </fieldset>
                <label className="tutor-notes">
                  <span className="field-label">
                    <Icon name="pencil" size={16} /> Preferencias para esta
                    conversación
                  </span>
                  <textarea
                    value={preferences}
                    disabled={Boolean(pending)}
                    onChange={(e) => setPreferences(e.target.value)}
                    maxLength={500}
                    rows={2}
                    placeholder="Por ejemplo: usa analogías y notación de mis apuntes."
                  />
                </label>
              </div>
            </details>
          </div>
          <div className="conversation-history" aria-live="polite">
            {!turns.length && (
              <div className="tutor-empty">
                <span className="tutor-avatar hero" aria-hidden="true">
                  <ArtImage src="/art/tutor-empty.png">
                    <Icon name="spark" size={44} />
                  </ArtImage>
                </span>
                <p className="handwritten">Una pregunta abre el camino.</p>
                <p>
                  Elige tus apuntes y pide una explicación, pistas o una
                  solución completa. Tu conversación queda guardada por materia.
                </p>
                <div className="suggestions">
                  {SUGGESTIONS.map((text) => (
                    <button
                      type="button"
                      key={text}
                      className="suggestion"
                      onClick={() => setQuestion(text)}
                    >
                      {text}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {turns.map((t) => (
              <article className="turn" key={t.id}>
                <div className="student-message">
                  <span className="who">
                    <Icon name="pencil" size={14} /> Tú
                  </span>
                  <p>{t.question}</p>
                </div>
                <div className="tutor-row">
                  <span className="tutor-avatar" aria-hidden="true">
                    <ArtImage src="/art/tutor-avatar.png">
                      <Icon name="spark" size={20} />
                    </ArtImage>
                  </span>
                  <div className="tutor-message">
                    <span
                      className={`source-badge ${t.sourceMode === "general" ? "general" : "notes"}`}
                    >
                      <Icon
                        name={t.sourceMode === "general" ? "globe" : "file"}
                        size={14}
                      />
                      {t.sourceMode === "general"
                        ? "Conocimiento general autorizado"
                        : "Con tus apuntes"}
                    </span>
                    {t.text && <SafeMarkdown text={t.text} />}
                    {t.sourcesChanged && (
                      <p className="source-warning">
                        Estos apuntes cambiaron después de iniciar la respuesta.
                        Las citas muestran la versión utilizada.
                      </p>
                    )}
                    {t.partialSources && (
                      <p className="source-warning">
                        Cobertura parcial: algunas páginas del material no
                        pudieron procesarse y no respaldan esta respuesta.
                      </p>
                    )}
                    <div className="citation-list">
                      {t.citations.map((ref, index) => (
                        <button
                          className="citation-chip"
                          key={index}
                          aria-label={`Abrir cita ${ref.sourceId || index + 1}, ${ref.locator}`}
                          onClick={() => setSource(ref)}
                        >
                          <Icon name="file" size={14} />
                          {ref.sourceId || index + 1} ·{" "}
                          {referenceLabel(ref.locator)}
                        </button>
                      ))}
                    </div>
                    {t.needsConsent && (
                      <button
                        className="secondary"
                        disabled={busy || Boolean(pending)}
                        onClick={() =>
                          void send({ question: t.question, general: true })
                        }
                      >
                        <Icon name="globe" size={16} /> Responder con
                        conocimiento general esta vez
                      </button>
                    )}
                    {!terminal(t) && (
                      <>
                        <p role="status">
                          {t.stage === "queued"
                            ? "Tu pregunta está en la fila…"
                            : "Buscando la respuesta en tus apuntes…"}{" "}
                          {connection}
                        </p>
                        <Skeleton lines={3} />
                        <button
                          className="text-button"
                          onClick={() =>
                            void api(`/jobs/${t.jobId}/cancel`, {
                              method: "POST",
                            }).catch((e) => setError((e as Error).message))
                          }
                        >
                          Cancelar respuesta
                        </button>
                      </>
                    )}
                    {t.status === "succeeded" && (
                      <div className="turn-actions">
                        <button
                          className="text-button with-icon"
                          disabled={!("speechSynthesis" in window)}
                          onClick={() => speak(t.text)}
                        >
                          <Icon
                            name={speaking ? "stop" : "speaker"}
                            size={16}
                          />
                          {speaking ? "Detener lectura" : "Escuchar respuesta"}
                        </button>
                      </div>
                    )}
                    {t.status === "succeeded" && (
                      <div className="make-resource">
                        {made?.turnId === t.id ? (
                          <p role="status">
                            ¡Listo! Lo estamos preparando.{" "}
                            <button
                              className="text-button"
                              onClick={() => onOpenResource(subject, made.id)}
                            >
                              Verlo en mis recursos
                            </button>
                          </p>
                        ) : (
                          <>
                            <span>Llévalo a tu repaso:</span>
                            {(
                              [
                                ["flashcards", "Tarjetas", "cards"],
                                ["quiz", "Cuestionario", "quiz"],
                                ["summary", "Resumen", "summary"],
                              ] as const
                            ).map(([kind, label, icon]) => (
                              <button
                                key={kind}
                                className="secondary with-icon"
                                disabled={busy}
                                onClick={() => void makeResource(t, kind)}
                              >
                                <Icon name={icon} size={16} />
                                {label}
                              </button>
                            ))}
                          </>
                        )}
                      </div>
                    )}
                    {["failed", "canceled"].includes(t.status) && (
                      <div>
                        <p>
                          {t.status === "canceled"
                            ? "Respuesta cancelada."
                            : "No se pudo completar la respuesta. Tu pregunta sigue guardada."}
                        </p>
                        {t.usageUnknown && (
                          <label className="check-label">
                            <input
                              type="checkbox"
                              checked={acceptCharge}
                              onChange={(e) =>
                                setAcceptCharge(e.target.checked)
                              }
                            />
                            Puede que el intento anterior ya cuente en tu límite
                            de hoy. Quiero intentarlo de nuevo.
                          </label>
                        )}
                        <button
                          className="secondary with-icon"
                          disabled={busy || (t.usageUnknown && !acceptCharge)}
                          onClick={() => {
                            setBusy(true);
                            void api(`/jobs/${t.jobId}/retry`, {
                              method: "POST",
                              body: JSON.stringify({
                                acceptPossibleCharge: acceptCharge,
                              }),
                            })
                              .then(() => api<Turn>(`/turns/${t.id}`))
                              .then((value) =>
                                setTurns((rows) =>
                                  rows.map((row) =>
                                    row.id === value.id ? value : row,
                                  ),
                                ),
                              )
                              .catch((e) => setError((e as Error).message))
                              .finally(() => setBusy(false));
                          }}
                        >
                          <Icon name="retry" size={16} />
                          Reintentar respuesta
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
          <form
            className={`tutor-composer ${turns.length ? "sticky" : ""}`}
            onSubmit={submit}
          >
            <label>
              <span className="field-label">Tu pregunta</span>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                maxLength={2000}
                rows={2}
                required
                disabled={busy || Boolean(pending)}
                placeholder="Escribe lo que no te queda claro…"
              />
            </label>
            <div className="composer-row">
              {sourceMode === "selected_material" ? (
                <label
                  className={`general-toggle ${general ? "selected" : ""}`}
                >
                  <input
                    type="checkbox"
                    checked={general}
                    onChange={(e) => setGeneral(e.target.checked)}
                    disabled={Boolean(pending)}
                  />
                  <Icon name="globe" size={16} />
                  Autorizar conocimiento general solo para esta pregunta
                </label>
              ) : (
                <span />
              )}
              <button
                className="primary with-icon"
                disabled={busy || Boolean(pending) || !question.trim()}
              >
                Enviar pregunta
                <Icon name="send" size={18} />
              </button>
            </div>
            <small>
              La IA puede equivocarse. Comprueba las fuentes y los cálculos.
            </small>
          </form>
        </>
      )}
      {source && (
        <SourceViewer source={source} onClose={() => setSource(null)} />
      )}
    </aside>
  );
}
