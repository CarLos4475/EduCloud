import { FormEvent, useState } from "react";
import { deleteUser, signOut } from "firebase/auth";
import { api, auth } from "../../api";

export function DataPanel() {
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function erase(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api("/me/delete", {
        method: "POST",
        body: JSON.stringify({ confirm: "ELIMINAR" }),
      });
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
      return;
    }
    // Quitar también el acceso; si Google pide volver a entrar, solo cerramos sesión.
    try {
      if (auth.currentUser) await deleteUser(auth.currentUser);
    } catch {
      await signOut(auth);
    }
  }

  return (
    <section className="panel data-panel" aria-labelledby="data-title">
      <h2 id="data-title">Tus datos</h2>
      <p>
        Lo que guardas aquí es solo tuyo y se queda mientras uses tu cuenta. Al
        eliminar una materia se borran al momento sus temas, apuntes,
        conversaciones y recursos.
      </p>
      <details>
        <summary>Borrar todo lo que he guardado</summary>
        <form onSubmit={erase}>
          <p>
            Se borrarán tus materias, apuntes, recursos, progreso y pasaporte, y
            se cerrará tu cuenta. No se puede deshacer.
          </p>
          <label>
            Escribe ELIMINAR para confirmar
            <input
              value={typed}
              onChange={(e) => setTyped(e.target.value)}
              autoComplete="off"
            />
          </label>
          {error && (
            <p role="alert" className="form-error">
              {error}
            </p>
          )}
          <button
            className="secondary danger-button"
            disabled={busy || typed !== "ELIMINAR"}
          >
            {busy ? "Borrando…" : "Borrar todo"}
          </button>
        </form>
      </details>
    </section>
  );
}
