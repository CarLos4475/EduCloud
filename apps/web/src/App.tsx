import { FormEvent, lazy, Suspense, useEffect, useRef, useState } from "react";
import {
  onAuthStateChanged,
  signOut,
  User,
  reload,
  sendEmailVerification,
} from "firebase/auth";
import { allRows, api, auth, isEmulator, Row } from "./api";
import { Login } from "./features/auth/Login";
import { Editor, EditorState } from "./features/academic/Editor";
import { Illustration } from "./components/Illustration";
import { MaterialsPanel } from "./features/materials/MaterialsPanel";
import { PageSkeleton, Skeleton } from "./components/Skeleton";
import { DataPanel } from "./features/account/DataPanel";
import {
  PassportPanel,
  PassportSummary,
} from "./features/progress/PassportPanel";
import { ResourcesPanel } from "./features/resources/ResourcesPanel";
const TutorPanel = lazy(() =>
  import("./features/tutor/TutorPanel").then((module) => ({
    default: module.TutorPanel,
  })),
);
import "./styles/study.css";

type Data = Record<string, Row[]>;
const empty = (): Data => ({
  subjects: [],
  periods: [],
  topics: [],
  agenda: [],
  schedule: [],
});
const weekdays = [
  "Lunes",
  "Martes",
  "Miércoles",
  "Jueves",
  "Viernes",
  "Sábado",
  "Domingo",
];

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [verified, setVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<Data>(empty);
  const [profile, setProfile] = useState<Row | null>(null);
  const [nav, setNav] = useState("home");
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [archived, setArchived] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [busy, setBusy] = useState(false);
  const [pendingIds, setPendingIds] = useState<string[]>([]);
  const [tutor, setTutor] = useState(false);
  const [openResource, setOpenResource] = useState<string | null>(null);
  const session = useRef(0);

  useEffect(
    () =>
      onAuthStateChanged(auth, (value) => {
        session.current++;
        setData(empty());
        setProfile(null);
        setUser(value);
        setInitializing(false);
        setVerified(Boolean(value?.emailVerified) || isEmulator);
        setSelected(null);
        setEditor(null);
        setTutor(false);
        setNav("home");
        setError("");
      }),
    [],
  );

  async function load() {
    if (!auth.currentUser) return;
    const epoch = session.current;
    setLoading(true);
    try {
      const keys = ["subjects", "periods", "topics", "agenda", "schedule"];
      const [records, me] = await Promise.all([
        Promise.all(keys.map(allRows)),
        api<Row>("/me"),
      ]);
      if (epoch === session.current) {
        setData(Object.fromEntries(keys.map((key, i) => [key, records[i]])));
        setProfile(me);
      }
    } catch (e) {
      if (epoch === session.current) setError((e as Error).message);
    } finally {
      if (epoch === session.current) setLoading(false);
    }
  }
  useEffect(() => {
    if (user && verified) void load();
  }, [user?.uid, verified]);

  async function save(value: Record<string, unknown>) {
    if (!editor) return;
    setBusy(true);
    setError("");
    try {
      await api(
        `/${editor.collection}${editor.row ? `/${editor.row.id}` : ""}`,
        {
          method: editor.row ? "PATCH" : "POST",
          body: JSON.stringify(
            editor.row
              ? { ...value, expectedRevision: editor.row.revision }
              : value,
          ),
        },
      );
      setEditor(null);
      setNotice("Guardado en tu espacio.");
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function update(
    collection: string,
    row: Row,
    changes: Record<string, unknown>,
  ) {
    setError("");
    setPendingIds((ids) => [...ids, row.id]);
    setData((current) => ({
      ...current,
      [collection]: current[collection].map((item) =>
        item.id === row.id ? { ...item, ...changes } : item,
      ),
    }));
    try {
      await api(`/${collection}/${row.id}`, {
        method: "PATCH",
        body: JSON.stringify({ ...changes, expectedRevision: row.revision }),
      });
      await load();
    } catch (e) {
      await load();
      setError((e as Error).message);
    } finally {
      setPendingIds((ids) => ids.filter((id) => id !== row.id));
    }
  }
  async function remove(collection: string, row: Row) {
    if (
      !window.confirm(
        "¿Eliminar este elemento? Esta acción no se puede deshacer.",
      )
    )
      return;
    try {
      await api(`/${collection}/${row.id}`, { method: "DELETE" });
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function removeSubject(subject: Row) {
    if (
      !window.confirm(
        `¿Eliminar "${String(subject.name)}" con todos sus temas, pendientes, apuntes, conversaciones y recursos? Esto no se puede deshacer. Si solo quieres dejarla a un lado, mejor archívala.`,
      )
    )
      return;
    try {
      await api(`/subjects/${subject.id}`, { method: "DELETE" });
      setSelected(null);
      await load();
      setNotice("Materia eliminada.");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  function navigate(key: string) {
    setNav(key);
    setSelected(null);
    setQuery("");
    setNotice("");
  }
  const subjectName = (id: unknown) =>
    String(data.subjects.find((s) => s.id === id)?.name || "Sin materia");
  const activeSubjects = data.subjects.filter(
    (s) =>
      Boolean(s.archived) === archived &&
      String(s.name).toLocaleLowerCase().includes(query.toLocaleLowerCase()),
  );
  const subject = data.subjects.find((s) => s.id === selected);
  const pending = data.agenda
    .filter((item) => item.status !== "done")
    .sort((a, b) =>
      String(a.dueDate || a.dueAt || "9999").localeCompare(
        String(b.dueDate || b.dueAt || "9999"),
      ),
    );
  const displayName = String(
    profile?.displayName || user?.email?.split("@")[0] || "Estudiante",
  );

  function subjectCards(rows: Row[]) {
    return (
      <div className="subject-grid">
        {rows.map((s) => (
          <button
            key={s.id}
            className={`subject-card accent-${s.accentId || "gold"}`}
            onClick={() => {
              setNav("subjects");
              setSelected(s.id);
            }}
          >
            <div>
              <h3>{String(s.name)}</h3>
              <p>
                {String(s.description || "Un nuevo espacio para aprender.")}
              </p>
              <span className="mono">
                {data.topics.filter((t) => t.subjectId === s.id).length} temas{" "}
                <span aria-hidden="true">↗</span>
              </span>
            </div>
            <Illustration id={String(s.illustrationId || "grid")} />
          </button>
        ))}
      </div>
    );
  }
  function agendaRows(rows: Row[]) {
    return (
      <div className="agenda-list">
        {rows.map((item) => (
          <article
            className={`agenda-row ${item.status === "done" ? "completed" : ""}`}
            key={item.id}
          >
            <input
              aria-label={`Completar ${item.title}`}
              type="checkbox"
              checked={item.status === "done"}
              disabled={pendingIds.includes(item.id)}
              onChange={(e) =>
                void update("agenda", item, {
                  status: e.target.checked ? "done" : "pending",
                })
              }
            />
            <div>
              <span className="eyebrow">
                {item.dueDate
                  ? String(item.dueDate)
                  : item.dueAt
                    ? new Date(String(item.dueAt)).toLocaleString("es-MX", {
                        timeZone: String(
                          profile?.timezone || "America/Mexico_City",
                        ),
                        dateStyle: "medium",
                        timeStyle: "short",
                      })
                    : "SIN FECHA"}
              </span>
              <h3>{String(item.title)}</h3>
              <p>{subjectName(item.subjectId)}</p>
              {item.notes ? (
                <p className="quiet">{String(item.notes)}</p>
              ) : null}
            </div>
            <button
              className="text-button"
              aria-label={`Editar ${item.title}`}
              onClick={() => {
                setError("");
                setEditor({ collection: "agenda", row: item });
              }}
            >
              Editar
            </button>
            <button
              className="icon-button"
              aria-label={`Eliminar ${item.title}`}
              onClick={() => void remove("agenda", item)}
            >
              ×
            </button>
          </article>
        ))}
      </div>
    );
  }
  async function skipTutorial() {
    try {
      await api("/me", {
        method: "PUT",
        body: JSON.stringify({
          displayName,
          career: profile?.career || "",
          timezone: profile?.timezone || "America/Mexico_City",
          tutorialStep: 5,
          expectedRevision: Number(profile?.revision || 0),
        }),
      });
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = Object.fromEntries(
      new FormData(event.currentTarget).entries(),
    );
    try {
      await api("/me", {
        method: "PUT",
        body: JSON.stringify({
          ...fields,
          tutorialStep: Number(profile?.tutorialStep || 0),
          expectedRevision: Number(profile?.revision || 0),
        }),
      });
      await load();
      setNotice("Perfil actualizado.");
    } catch (e) {
      setError((e as Error).message);
    }
  }

  if (initializing)
    return (
      <main className="startup">
        <PageSkeleton label="Preparando tu espacio…" />
      </main>
    );
  if (!user) return <Login />;
  if (!user.email?.toLowerCase().endsWith("@pcpuma.acatlan.unam.mx"))
    return (
      <main className="startup">
        <h1>Tu cuenta institucional.</h1>
        <p>
          Este espacio está disponible para correos @pcpuma.acatlan.unam.mx.
        </p>
        <button className="primary" onClick={() => void signOut(auth)}>
          Usar otra cuenta
        </button>
      </main>
    );
  if (!verified)
    return (
      <main className="startup">
        <h1>Verifica tu correo.</h1>
        <p>
          Revisa el mensaje que enviamos a tu correo institucional y abre su
          enlace.
        </p>
        <div className="button-row">
          <button
            className="primary"
            onClick={async () => {
              await reload(user);
              await user.getIdToken(true);
              setVerified(user.emailVerified);
            }}
          >
            Ya lo verifiqué
          </button>
          <button
            className="secondary"
            onClick={() => void sendEmailVerification(user)}
          >
            Reenviar correo
          </button>
          <button className="text-button" onClick={() => void signOut(auth)}>
            Salir
          </button>
        </div>
      </main>
    );
  return (
    <div className="campus-shell">
      <aside className="sidebar">
        <button
          className="brand"
          onClick={() => navigate("home")}
          aria-label="Mi Campus, inicio"
        >
          MI
          <br />
          CAMPUS<span>✦</span>
        </button>
        <nav aria-label="Navegación principal">
          {[
            ["home", "⌂", "Inicio"],
            ["subjects", "▦", "Materias"],
            ["agenda", "▤", "Agenda"],
            ["schedule", "◷", "Horario"],
            ["profile", "◇", "Mi perfil"],
          ].map(([key, icon, label]) => (
            <button
              key={key}
              className={nav === key ? "active" : ""}
              onClick={() => navigate(key)}
            >
              <span aria-hidden="true">{icon}</span>
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="avatar">
            {displayName.slice(0, 1).toUpperCase()}
          </span>
          <div>
            <strong>{displayName}</strong>
            <small>{String(profile?.career || "Mi espacio")}</small>
          </div>
          <button className="text-button" onClick={() => void signOut(auth)}>
            Salir
          </button>
        </div>
      </aside>
      <main className="workspace" id="main-content">
        <header className="topbar">
          <span className="eyebrow">
            {new Date().toLocaleDateString("es-MX", {
              weekday: "long",
              day: "2-digit",
              month: "short",
            })}
          </span>
          <div className="topbar-actions">
            <label className="search-label">
              <span className="sr-only">Buscar materias</span>
              <input
                type="search"
                placeholder="Buscar en tus materias…"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setNav("subjects");
                  setSelected(null);
                }}
              />
            </label>
            <button
              className="primary tutor-button"
              onClick={() => setTutor(true)}
            >
              ✦ Abrir tutor
            </button>
          </div>
        </header>
        {error && !editor && (
          <div className="message error" role="alert">
            {error}
            <button className="text-button" onClick={() => void load()}>
              Reintentar
            </button>
          </div>
        )}
        {notice && (
          <p className="message" role="status">
            {notice}
          </p>
        )}
        {loading && (
          <div className="loading">
            <Skeleton lines={1} label="Actualizando tu espacio…" />
          </div>
        )}

        {nav === "home" && (
          <>
            <section className="hero">
              <span className="eyebrow">HOLA, {displayName.toUpperCase()}</span>
              <h1>
                TU SIGUIENTE
                <br />
                GRAN IDEA.
              </h1>
              <p className="handwritten">Un tema a la vez.</p>
              <div className="hero-mark" aria-hidden="true">
                <Illustration id="geometry" />
              </div>
            </section>
            {profile && Number(profile.tutorialStep || 0) < 5 && (
              <section className="onboarding">
                <div>
                  <span className="eyebrow">PRIMERA PARADA</span>
                  <h3>Construye tu semestre a tu manera.</h3>
                  <p>
                    Crea una materia, elige su dibujo y anota tu primer
                    pendiente. El resto puede esperar.
                  </p>
                </div>
                <div>
                  <button
                    className="primary"
                    onClick={() => {
                      setNav("subjects");
                      setEditor({ collection: "subjects" });
                    }}
                  >
                    Crear mi primera materia
                  </button>
                  <button
                    className="text-button"
                    onClick={() => void skipTutorial()}
                  >
                    Lo haré después
                  </button>
                </div>
              </section>
            )}
            <div className="home-columns">
              <section>
                <div className="section-heading">
                  <h2>Mis materias</h2>
                  <button
                    className="text-button"
                    onClick={() => {
                      setError("");
                      setEditor({ collection: "subjects" });
                    }}
                  >
                    + Agregar materia
                  </button>
                </div>
                {subjectCards(
                  data.subjects.filter((s) => !s.archived).slice(0, 4),
                )}
                {!data.subjects.some((s) => !s.archived) && (
                  <div className="empty-state">
                    <span aria-hidden="true">↗</span>
                    <h3>Aquí empieza tu siguiente idea.</h3>
                    <p>
                      Agrega la materia que quieras. Su nombre, temas e
                      ilustración los eliges tú.
                    </p>
                  </div>
                )}
                <div className="study-note">
                  <span className="eyebrow">A TU RITMO</span>
                  <h2>
                    Un poco de orden.
                    <br />
                    Más espacio para aprender.
                  </h2>
                  <p>
                    Empieza por lo que tienes pendiente y reserva un momento
                    para tus preguntas.
                  </p>
                  <button
                    className="gold-button"
                    onClick={() => navigate("agenda")}
                  >
                    Organizar mi semana →
                  </button>
                </div>
              </section>
              <aside className="upcoming">
                <div className="section-heading">
                  <h2>Lo que viene</h2>
                </div>
                {pending.length ? (
                  agendaRows(pending.slice(0, 4))
                ) : (
                  <div className="empty-state">
                    <h3>Una semana por escribir.</h3>
                    <p>Anota tareas, exámenes o momentos de estudio.</p>
                    <button
                      className="secondary"
                      onClick={() => setEditor({ collection: "agenda" })}
                    >
                      Agregar pendiente
                    </button>
                  </div>
                )}
                <section className="passport-note">
                  <span className="eyebrow">CADA PASO CUENTA</span>
                  <h3>Tu camino, a la vista.</h3>
                  <PassportSummary onOpen={() => navigate("profile")} />
                  <div aria-hidden="true">✧ ── ✧ ── ✧</div>
                </section>
              </aside>
            </div>
          </>
        )}

        {nav === "subjects" && !subject && (
          <>
            <div className="page-heading">
              <span className="eyebrow">TU MAPA DEL SEMESTRE</span>
              <h1>Mis materias.</h1>
              <p>No hay un camino único. Construye el tuyo.</p>
            </div>
            <div className="section-heading">
              <button
                className="secondary"
                onClick={() => setArchived(!archived)}
              >
                {archived ? "Ver activas" : "Ver archivadas"}
              </button>
              <button
                className="primary"
                onClick={() => {
                  setError("");
                  setEditor({ collection: "subjects" });
                }}
              >
                + Nueva materia
              </button>
            </div>
            {subjectCards(activeSubjects)}
            {!activeSubjects.length && (
              <div className="empty-state">
                <h3>
                  {query
                    ? "No encontramos esa materia."
                    : archived
                      ? "No hay materias archivadas."
                      : "Tu próxima materia empieza aquí."}
                </h3>
                <p>
                  {query
                    ? "Prueba con otro nombre."
                    : "Crea una materia con el nombre y la ilustración que quieras."}
                </p>
              </div>
            )}
          </>
        )}

        {nav === "subjects" && subject && (
          <>
            <button className="text-button" onClick={() => setSelected(null)}>
              ← Todas mis materias
            </button>
            <section className="subject-hero">
              <div>
                <span className="eyebrow">TU ESPACIO PARA ENTENDER</span>
                <h1>{String(subject.name)}</h1>
                <p>
                  {String(
                    subject.description || "Cada pregunta abre un camino.",
                  )}
                </p>
                <div className="button-row">
                  <button
                    className="secondary"
                    onClick={() =>
                      setEditor({ collection: "subjects", row: subject })
                    }
                  >
                    Editar materia
                  </button>
                  <button
                    className="text-button"
                    onClick={() =>
                      void update("subjects", subject, {
                        archived: !subject.archived,
                      })
                    }
                  >
                    {subject.archived
                      ? "Restaurar materia"
                      : "Archivar materia"}
                  </button>
                  <button
                    className="text-button danger"
                    onClick={() => void removeSubject(subject)}
                  >
                    Eliminar materia
                  </button>
                </div>
              </div>
              <Illustration id={String(subject.illustrationId)} />
            </section>
            <section className="panel">
              <div className="section-heading">
                <h2>Temas</h2>
                <button
                  className="text-button"
                  onClick={() =>
                    setEditor({ collection: "topics", subjectId: subject.id })
                  }
                >
                  + Agregar tema
                </button>
              </div>
              {data.topics
                .filter((t) => t.subjectId === subject.id)
                .sort((a, b) => Number(a.order) - Number(b.order))
                .map((t, i) => (
                  <div className="topic-row" key={t.id}>
                    <span className="topic-number">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <div>
                      <h3>{String(t.title)}</h3>
                      <p className="quiet">
                        {((t.prerequisiteIds as string[]) || []).length
                          ? `Antes: ${(t.prerequisiteIds as string[]).map((id) => String(data.topics.find((other) => other.id === id)?.title || "Tema")).join(", ")}`
                          : "Sin prerrequisitos"}
                      </p>
                    </div>
                    <button
                      className="text-button"
                      onClick={() =>
                        setEditor({
                          collection: "topics",
                          row: t,
                          subjectId: subject.id,
                        })
                      }
                    >
                      Editar
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`Eliminar ${t.title}`}
                      onClick={() => void remove("topics", t)}
                    >
                      ×
                    </button>
                  </div>
                ))}
              {!data.topics.some((t) => t.subjectId === subject.id) && (
                <p>
                  Divide la materia en temas pequeños para encontrar por dónde
                  empezar.
                </p>
              )}
            </section>
            <section>
              <div className="section-heading">
                <h2>Pendientes de la materia</h2>
                <button
                  className="text-button"
                  onClick={() =>
                    setEditor({ collection: "agenda", subjectId: subject.id })
                  }
                >
                  + Agregar
                </button>
              </div>
              {agendaRows(
                data.agenda.filter((a) => a.subjectId === subject.id),
              )}
            </section>
            <MaterialsPanel
              key={`${user.uid}:${subject.id}`}
              subjectId={subject.id}
              topics={data.topics.filter((t) => t.subjectId === subject.id)}
              onTopicsChanged={() => void load()}
            />
            <ResourcesPanel
              key={`resources:${user.uid}:${subject.id}`}
              subjectId={subject.id}
              openId={openResource}
              onOpened={() => setOpenResource(null)}
            />
          </>
        )}

        {nav === "agenda" && (
          <>
            <div className="page-heading">
              <span className="eyebrow">UN PASO ANTES</span>
              <h1>Mi agenda.</h1>
              <p>Haz espacio para las cosas que importan.</p>
            </div>
            <div className="section-heading">
              <h2>Pendientes y exámenes</h2>
              <button
                className="primary"
                onClick={() => setEditor({ collection: "agenda" })}
              >
                + Nuevo pendiente
              </button>
            </div>
            {agendaRows([
              ...pending,
              ...data.agenda.filter((a) => a.status === "done"),
            ])}
            {!data.agenda.length && (
              <div className="empty-state">
                <h3>Sin pendientes todavía.</h3>
                <p>Agrega una tarea, un examen o un momento de estudio.</p>
              </div>
            )}
          </>
        )}

        {nav === "schedule" && (
          <>
            <div className="page-heading">
              <span className="eyebrow">TU SEMANA, TU RITMO</span>
              <h1>Mi horario.</h1>
              <p>Bloques semanales en la zona horaria de cada clase.</p>
            </div>
            <div className="section-heading">
              <h2>Semana habitual</h2>
              <button
                className="primary"
                onClick={() => setEditor({ collection: "schedule" })}
                disabled={!data.subjects.length}
              >
                + Agregar clase
              </button>
            </div>
            {!data.subjects.length && (
              <p>Crea una materia antes de agregarla al horario.</p>
            )}
            <div className="week-grid">
              {weekdays.map((day, i) => (
                <section className="day-column" key={day}>
                  <h3>{day}</h3>
                  {data.schedule
                    .filter((s) => s.weekday === i)
                    .sort((a, b) =>
                      String(a.localStart).localeCompare(String(b.localStart)),
                    )
                    .map((s) => (
                      <article key={s.id}>
                        <span className="mono">
                          {String(s.localStart).slice(0, 5)}–
                          {String(s.localEnd).slice(0, 5)}
                        </span>
                        <h4>{subjectName(s.subjectId)}</h4>
                        <small>{String(s.timezone)}</small>
                        <p>{String(s.notes || "")}</p>
                        <button
                          className="text-button"
                          onClick={() =>
                            setEditor({ collection: "schedule", row: s })
                          }
                        >
                          Editar
                        </button>
                        <button
                          className="icon-button"
                          aria-label={`Eliminar clase ${subjectName(s.subjectId)}`}
                          onClick={() => void remove("schedule", s)}
                        >
                          ×
                        </button>
                      </article>
                    ))}
                </section>
              ))}
            </div>
          </>
        )}

        {nav === "profile" && (
          <>
            <div className="page-heading">
              <span className="eyebrow">HECHO A TU MEDIDA</span>
              <h1>Mi espacio.</h1>
            </div>
            <div className="profile-grid">
              <PassportPanel />
              <section className="panel">
                <h2>Tu perfil</h2>
                <form onSubmit={saveProfile}>
                  <label>
                    Cómo te llamamos
                    <input
                      name="displayName"
                      required
                      maxLength={100}
                      defaultValue={String(profile?.displayName || displayName)}
                    />
                  </label>
                  <label>
                    Carrera (opcional)
                    <input
                      name="career"
                      maxLength={120}
                      defaultValue={String(profile?.career || "")}
                    />
                  </label>
                  <label>
                    Zona horaria
                    <input
                      name="timezone"
                      required
                      defaultValue={String(
                        profile?.timezone || "America/Mexico_City",
                      )}
                    />
                  </label>
                  <button className="primary">Guardar perfil</button>
                </form>
              </section>
              <section className="panel">
                <div className="section-heading">
                  <h2>Periodos</h2>
                  <button
                    className="text-button"
                    onClick={() => setEditor({ collection: "periods" })}
                  >
                    + Nuevo
                  </button>
                </div>
                {data.periods.map((p) => (
                  <div className="period-row" key={p.id}>
                    <div>
                      <h3>{String(p.name)}</h3>
                      <small>
                        {String(p.startDate || "Sin inicio")} /{" "}
                        {String(p.endDate || "Sin fin")}
                      </small>
                    </div>
                    <button
                      className="text-button"
                      onClick={() =>
                        setEditor({ collection: "periods", row: p })
                      }
                    >
                      Editar
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`Eliminar periodo ${p.name}`}
                      onClick={() => void remove("periods", p)}
                    >
                      ×
                    </button>
                  </div>
                ))}
                {!data.periods.length && (
                  <p>
                    Puedes organizar tus materias por semestre o dejarlas
                    independientes.
                  </p>
                )}
              </section>
            </div>
            <DataPanel />
          </>
        )}
        <footer className="workspace-footer">
          <span>MI CAMPUS · UN TEMA A LA VEZ</span>
          <span>
            {data.subjects.filter((s) => !s.archived).length} materias ·{" "}
            {pending.length} pendientes
          </span>
        </footer>
      </main>
      {editor && (
        <Editor
          state={editor}
          subjects={data.subjects}
          periods={data.periods}
          topics={data.topics}
          busy={busy}
          error={error}
          onSave={save}
          onClose={() => {
            setEditor(null);
            setError("");
          }}
        />
      )}
      {tutor && (
        <Suspense
          fallback={
            <aside className="tutor-drawer study-tutor">
              <Skeleton lines={6} label="Abriendo tu tutor…" />
            </aside>
          }
        >
          <TutorPanel
            key={user.uid}
            subjects={data.subjects.filter((s) => !s.archived)}
            initialSubjectId={selected}
            onClose={() => setTutor(false)}
            onOpenResource={(subjectId, resourceId) => {
              setTutor(false);
              setNav("subjects");
              setSelected(subjectId);
              setOpenResource(resourceId);
            }}
          />
        </Suspense>
      )}
    </div>
  );
}
