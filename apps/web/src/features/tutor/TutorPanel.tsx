import { FormEvent, useEffect, useRef, useState } from "react";
import { api, authorizedFetch, studyRows, Row } from "../../api";
import { SafeMarkdown } from "../../components/SafeMarkdown";
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

export function TutorPanel({
  subjects,
  initialSubjectId,
  onClose,
}: {
  subjects: Row[];
  initialSubjectId: string | null;
  onClose: () => void;
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
        <div>
          <span className="eyebrow">TU COMPAÑERO DE ESTUDIO</span>
          <h2>Vamos a entenderlo.</h2>
        </div>
        <button
          ref={closeButton}
          className="icon-button"
          aria-label="Cerrar tutor"
          onClick={onClose}
        >
          ×
        </button>
      </header>
      {error && (
        <p role="alert" className="error-banner">
          {error}
        </p>
      )}
      {!subjects.length ? (
        <p>Crea una materia para empezar a estudiar con tu tutor.</p>
      ) : (
        <>
          <div className="tutor-context">
            <label>
              Materia del tutor
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
              Conversación
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
            <details open={!conversationId}>
              <summary>Tu tutor y sus fuentes</summary>
              <div className="tutor-settings">
                <label>
                  Personalidad
                  <select
                    value={personalityId}
                    disabled={Boolean(pending)}
                    onChange={(e) => setPersonalityId(e.target.value)}
                  >
                    <option value="patient">Paso a paso</option>
                    <option value="socratic">Preguntemos</option>
                    <option value="direct">Al grano</option>
                  </select>
                </label>
                <label>
                  Tipo de ayuda
                  <select
                    value={assistanceMode}
                    disabled={Boolean(pending)}
                    onChange={(e) => setAssistanceMode(e.target.value)}
                  >
                    <option value="explain">Explicación</option>
                    <option value="hints">Pistas</option>
                    <option value="solution">Solución completa</option>
                    <option value="practice">Práctica</option>
                  </select>
                </label>
                <label>
                  Modo de fuentes
                  <select
                    value={sourceMode}
                    disabled={Boolean(pending)}
                    onChange={(e) => setSourceMode(e.target.value)}
                  >
                    <option value="selected_material">
                      Priorizar mis apuntes
                    </option>
                    <option value="general">
                      Conocimiento general autorizado para este chat
                    </option>
                  </select>
                </label>
                <fieldset disabled={Boolean(pending)}>
                  <legend>Apuntes seleccionados (hasta 10)</legend>
                  {materials
                    .filter((m) => ["ready", "partial"].includes(m.status))
                    .map((m) => (
                      <label className="check-label" key={m.id}>
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
                        {m.name}
                        {m.status === "partial" ? " · cobertura parcial" : ""}
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
                <label>
                  Preferencias para esta conversación
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
                <p className="handwritten">Una pregunta abre el camino.</p>
                <p>
                  Elige tus fuentes y pide una explicación, pistas o una
                  solución completa. Tu conversación queda guardada por materia.
                </p>
              </div>
            )}
            {turns.map((t) => (
              <article className="turn" key={t.id}>
                <div className="student-message">
                  <span className="eyebrow">TU PREGUNTA</span>
                  <p>{t.question}</p>
                </div>
                <div className="tutor-message">
                  <span className="eyebrow">
                    TU TUTOR ·{" "}
                    {t.sourceMode === "general"
                      ? "CONOCIMIENTO GENERAL AUTORIZADO"
                      : "TUS APUNTES"}
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
                      Responder con conocimiento general esta vez
                    </button>
                  )}
                  {!terminal(t) && (
                    <>
                      <p role="status">
                        {t.stage === "queued"
                          ? "Tu pregunta está en cola…"
                          : "Preparando una respuesta con tus fuentes…"}{" "}
                        {connection}
                      </p>
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
                        className="text-button"
                        disabled={!("speechSynthesis" in window)}
                        onClick={() => speak(t.text)}
                      >
                        {speaking ? "Detener lectura" : "Escuchar respuesta"}
                      </button>
                      <small>
                        {t.usage?.total_tokens !== undefined
                          ? `${t.usage.total_tokens} tokens observados`
                          : ""}
                      </small>
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
                            onChange={(e) => setAcceptCharge(e.target.checked)}
                          />
                          El consumo anterior es desconocido; acepto un posible
                          consumo adicional al reintentar.
                        </label>
                      )}
                      <button
                        className="secondary"
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
                        Reintentar respuesta
                      </button>
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
          <form className="tutor-composer" onSubmit={submit}>
            <label>
              Tu pregunta
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                maxLength={2000}
                rows={3}
                required
                disabled={busy || Boolean(pending)}
              />
            </label>
            {sourceMode === "selected_material" && (
              <label className="check-label">
                <input
                  type="checkbox"
                  checked={general}
                  onChange={(e) => setGeneral(e.target.checked)}
                  disabled={Boolean(pending)}
                />
                Autorizar conocimiento general solo para esta pregunta
              </label>
            )}
            <button
              className="primary"
              disabled={busy || Boolean(pending) || !question.trim()}
            >
              Enviar pregunta
            </button>
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
