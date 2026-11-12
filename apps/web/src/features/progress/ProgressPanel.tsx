import { useEffect, useState } from "react";
import { api } from "../../api";
import { Skeleton } from "../../components/Skeleton";

type Progress = {
  materialsReady: number;
  resourcesReady: number;
  quizAttempts: number;
  averageScore: number | null;
  lastScore: number | null;
  cardsKnown: number;
  cardsToReview: number;
  recommendations: { text: string; resourceId?: string | null }[];
};

export function ProgressPanel({
  subjectId,
  onOpen,
}: {
  subjectId: string;
  onOpen: (resourceId: string) => void;
}) {
  const [data, setData] = useState<Progress | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let active = true;
    setData(null);
    const refresh = () =>
      api<Progress>(`/subjects/${subjectId}/progress`)
        .then((value) => active && setData(value))
        .catch(() => active && setFailed(true));
    void refresh();
    // Apuntes y recursos terminan de prepararse en segundo plano.
    const timer = setInterval(() => void refresh(), 6000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [subjectId]);
  if (failed) return null;
  if (!data)
    return (
      <div className="progress-panel">
        <Skeleton lines={3} label="Cargando tu progreso…" />
      </div>
    );
  const figures: [string, string][] = [
    ["Apuntes listos", String(data.materialsReady)],
    ["Recursos", String(data.resourcesReady)],
    [
      "Promedio en cuestionarios",
      data.averageScore === null ? "—" : `${data.averageScore}%`,
    ],
    ["Tarjetas sabidas", String(data.cardsKnown)],
  ];
  return (
    <section className="progress-panel" aria-labelledby="progress-title">
      <h3 id="progress-title">Tu progreso</h3>
      <dl className="progress-figures">
        {figures.map(([label, value]) => (
          <div key={label}>
            <dd>{value}</dd>
            <dt>{label}</dt>
          </div>
        ))}
      </dl>
      {data.recommendations.length > 0 && (
        <ul className="progress-tips">
          {data.recommendations.map((tip, i) => (
            <li key={i}>
              {tip.text}{" "}
              {tip.resourceId && (
                <button
                  className="text-button"
                  onClick={() => onOpen(tip.resourceId!)}
                >
                  Abrir
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
