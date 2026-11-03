import { FormEvent, useState } from "react";
import {
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  sendEmailVerification,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
} from "firebase/auth";
import { auth, isEmulator, persistenceReady } from "../../api";

export function Login() {
  const [register, setRegister] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = new FormData(event.currentTarget);
    if (
      !String(data.get("email"))
        .trim()
        .toLowerCase()
        .endsWith("@pcpuma.acatlan.unam.mx")
    ) {
      setError("Usa tu correo @pcpuma.acatlan.unam.mx.");
      setBusy(false);
      return;
    }
    try {
      await persistenceReady;
      const credential = await (
        register ? createUserWithEmailAndPassword : signInWithEmailAndPassword
      )(auth, String(data.get("email")).trim(), String(data.get("password")));
      if (register && !isEmulator) await sendEmailVerification(credential.user);
    } catch {
      setError(
        "No pudimos iniciar la sesión. Comprueba tus datos y que el servicio esté disponible.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-layout">
      <section className="login-story">
        <span className="eyebrow">MI CAMPUS · TU ESPACIO DE ESTUDIO</span>
        <h1>
          LA SIGUIENTE
          <br />
          GRAN IDEA
          <br />
          ES TUYA.
        </h1>
        <p className="handwritten">Un tema a la vez.</p>
        <p>
          Organiza tus materias. Encuentra tu ritmo.
          <br />
          Dale espacio a lo que quieres entender.
        </p>
        <div className="story-grid" aria-hidden="true">
          <span>∫</span>
          <span>↗</span>
          <span>∿</span>
          <span>∴</span>
        </div>
      </section>
      <section className="login-form">
        <span className="eyebrow">ABRE TU ESPACIO</span>
        <h2>{register ? "Empieza por aquí." : "Qué bueno verte."}</h2>
        <p>
          {register
            ? "Crea tu cuenta y construye tu semestre a tu manera."
            : "Tus materias y pendientes te esperan."}
        </p>
        <p className="quiet">Acceso con correo @pcpuma.acatlan.unam.mx.</p>
        <form onSubmit={submit}>
          <label>
            Correo electrónico
            <input type="email" name="email" autoComplete="email" required />
          </label>
          <label>
            Contraseña
            <input
              type="password"
              name="password"
              minLength={6}
              autoComplete={register ? "new-password" : "current-password"}
              required
            />
          </label>
          <button className="primary" disabled={busy}>
            {busy
              ? "Conectando…"
              : register
                ? "Crear cuenta"
                : "Entrar a mi campus"}
          </button>
        </form>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <button
          className="text-button"
          onClick={() => {
            setRegister(!register);
            setError("");
          }}
        >
          {register ? "Ya tengo una cuenta" : "Es mi primera visita"}
        </button>
        <button
          className="secondary"
          onClick={async () => {
            try {
              const credential = await signInWithPopup(
                auth,
                new GoogleAuthProvider(),
              );
              if (
                !credential.user.email
                  ?.toLowerCase()
                  .endsWith("@pcpuma.acatlan.unam.mx")
              ) {
                await signOut(auth);
                setError("Usa tu cuenta institucional de Acatlán.");
              }
            } catch {
              setError(
                "No pudimos conectar con Google. Intenta con correo y contraseña.",
              );
            }
          }}
        >
          Continuar con Google
        </button>
        {isEmulator && (
          <p className="quiet">
            Entorno de desarrollo local · usa cuentas de prueba.
          </p>
        )}
      </section>
    </main>
  );
}
