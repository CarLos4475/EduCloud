import { initializeApp } from "firebase/app";
import {
  browserSessionPersistence,
  connectAuthEmulator,
  getAuth,
  setPersistence,
} from "firebase/auth";

export const firebaseApp = initializeApp({
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "demo-key",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "demo-campus",
  authDomain:
    import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "demo-campus.firebaseapp.com",
});
export const auth = getAuth(firebaseApp);
export const isEmulator =
  import.meta.env.VITE_USE_EMULATORS !== "false" &&
  (import.meta.env.VITE_FIREBASE_PROJECT_ID || "demo-campus").startsWith(
    "demo-",
  );
if (isEmulator)
  connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
export const persistenceReady = setPersistence(auth, browserSessionPersistence);

export type Row = { id: string; revision: number; [key: string]: unknown };
export type Page<T> = { items: T[]; nextCursor: string | null };

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await auth.currentUser?.getIdToken();
  const response = await fetch(
    (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api/v1") + path,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    },
  );
  if (response.status === 204) return undefined as T;
  const result = await response.json();
  if (!response.ok)
    throw new Error(result.message || "No se pudo completar la operación.");
  return result as T;
}

export async function allRows(collection: string): Promise<Row[]> {
  const result: Row[] = [];
  let cursor: string | null = null;
  do {
    const page: Page<Row> = await api(
      `/${collection}?limit=50${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`,
    );
    result.push(...page.items);
    cursor = page.nextCursor;
  } while (cursor);
  return result;
}
