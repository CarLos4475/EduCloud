import { useState, type ReactNode } from "react";

/** Línea fina, esquinas redondeadas: el mismo trazo en toda la app. */
const PATHS = {
  spark:
    "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z M19 16l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7.7-2z",
  book: "M4 4.5A2.5 2.5 0 016.5 2H20v17H6.5A2.5 2.5 0 004 21.5v-17z M8 6.5h8 M8 10.5h6",
  chat: "M4 5h16v11H9l-5 4V5z M8 9.5h8 M8 12.5h5",
  file: "M7 3h7l5 5v13H7V3z M14 3v5h5 M10 13h6 M10 17h6",
  steps: "M3 20h6v-5h6v-5h6 M18 4l3 3-3 3",
  bulb: "M9 18h6 M10 21h4 M12 3a6 6 0 00-3.5 10.9c.6.5 1 1.2 1 2V17h5v-1.1c0-.8.4-1.5 1-2A6 6 0 0012 3z",
  bolt: "M13 2L4 14h7l-1 8 9-12h-7l1-8z",
  target:
    "M12 3a9 9 0 100 18 9 9 0 000-18z M12 8a4 4 0 100 8 4 4 0 000-8z M12 11.5a.5.5 0 100 1 .5.5 0 000-1z",
  pencil: "M4 20l1-4L16 5l3 3L8 19l-4 1z M14 7l3 3",
  check: "M5 12.5l4.5 4.5L19 7.5",
  cards: "M8 6h11v14H8z M5 17V3h11",
  quiz: "M12 3a9 9 0 100 18 9 9 0 000-18z M9.5 9.5a2.5 2.5 0 114 2c-.9.6-1.5 1-1.5 2 M12 17h.01",
  summary: "M5 4h14v16H5z M8 8h8 M8 12h8 M8 16h5",
  send: "M4 12L20 4l-6 16-3-7-7-1z M11 13l9-9",
  speaker: "M4 9v6h4l5 4V5L8 9H4z M16 9a4 4 0 010 6 M18.5 6.5a8 8 0 010 11",
  stop: "M7 7h10v10H7z",
  close: "M6 6l12 12 M18 6L6 18",
  globe:
    "M12 3a9 9 0 100 18 9 9 0 000-18z M3 12h18 M12 3c3 3 3 15 0 18 M12 3c-3 3-3 15 0 18",
  retry: "M4 12a8 8 0 108-8 M4 4v5h5",
  compass: "M12 3a9 9 0 100 18 9 9 0 000-18z M15.5 8.5l-2 5-5 2 2-5 5-2z",
  home: "M4 11l8-7 8 7 M6 10v10h12V10",
  clock: "M12 3a9 9 0 100 18 9 9 0 000-18z M12 7v5l3.5 2",
  user: "M12 4a4 4 0 100 8 4 4 0 000-8z M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7",
  calendar: "M4 6h16v14H4z M4 10h16 M8 3v4 M16 3v4",
  flask: "M9 3h6 M10 3v6l-5 9a2 2 0 002 3h10a2 2 0 002-3l-5-9V3 M8 15h8",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {PATHS[name].split(" M").map((d, i) => (
        <path key={i} d={i === 0 ? d : "M" + d} />
      ))}
    </svg>
  );
}

/**
 * Muestra una imagen de /art si existe; si todavía no está, usa el respaldo
 * (un icono), así la app se ve completa antes y después de añadir ilustraciones.
 */
export function ArtImage({
  src,
  alt = "",
  className,
  children,
}: {
  src: string;
  alt?: string;
  className?: string;
  children: ReactNode;
}) {
  const [failed, setFailed] = useState(false);
  if (failed) return <>{children}</>;
  return (
    <img
      className={className}
      src={src}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
