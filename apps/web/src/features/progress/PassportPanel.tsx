import { useEffect, useState } from "react";
import { api } from "../../api";
import { Skeleton } from "../../components/Skeleton";

type Stamp = {
  id: string;
  title: string;
  description: string;
  earned: boolean;
  earnedAt?: string | null;
};

const MARKS: Record<string, string> = {
  first_material: "✎",
  first_question: "?",
  first_resource: "★",
  explorer: "◈",
  first_quiz: "✓",
  perfect_quiz: "✦",
  cards_ten: "▤",
  three_subjects: "Ⅲ",
};

export function PassportPanel() {
  const [stamps, setStamps] = useState<Stamp[] | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    api<{ stamps: Stamp[] }>("/passport")
      .then((value) => active && setStamps(value.stamps))
      .catch(() => active && setFailed(true));
    return () => {
      active = false;
    };
  }, []);
  if (failed) return null;
  const earned = stamps?.filter((s) => s.earned).length ?? 0;
  return (
    <section className="panel passport" aria-labelledby="passport-title">
      <h2 id="passport-title">Mi pasaporte</h2>
      <p>
        Cada estampilla se gana estudiando.
        {stamps && ` Llevas ${earned} de ${stamps.length}.`}
      </p>
      {!stamps ? (
        <Skeleton lines={4} label="Cargando tu pasaporte…" />
      ) : (
        <ul className="stamp-grid">
          {stamps.map((stamp) => (
            <li
              key={stamp.id}
              className={`stamp ${stamp.earned ? "earned" : "locked"}`}
            >
              <span className="stamp-mark" aria-hidden="true">
                {MARKS[stamp.id] ?? "★"}
              </span>
              <strong>{stamp.title}</strong>
              <small>
                {stamp.earned
                  ? `Ganada el ${new Date(stamp.earnedAt ?? "").toLocaleDateString("es-MX", { day: "numeric", month: "long" })}`
                  : stamp.description}
              </small>
              <span className="visually-hidden">
                {stamp.earned ? "Ganada" : "Por ganar"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Short version for the home page: how many stamps so far, and a way in. */
export function PassportSummary({ onOpen }: { onOpen: () => void }) {
  const [counts, setCounts] = useState<{
    earned: number;
    total: number;
  } | null>(null);
  useEffect(() => {
    let active = true;
    api<{ earned: number; total: number }>("/passport")
      .then((value) => active && setCounts(value))
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);
  if (!counts) return <Skeleton lines={2} label="Cargando tu pasaporte…" />;
  return (
    <>
      <p>
        {counts.earned === 0
          ? "Tu pasaporte está vacío. La primera estampilla llega con tus primeros apuntes."
          : `Llevas ${counts.earned} de ${counts.total} estampillas. Cada recurso y cada repaso suman.`}
      </p>
      <button className="text-button" onClick={onOpen}>
        Ver mi pasaporte
      </button>
    </>
  );
}
