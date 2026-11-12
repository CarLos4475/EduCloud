import { ArtImage } from "./Icons";
export const illustrations = [
  ["grid", "Retícula"],
  ["wave", "Ondas"],
  ["orbit", "Órbitas"],
  ["geometry", "Geometría"],
  ["terminal", "Terminal"],
  ["circuit", "Circuitos"],
  ["blocks", "Bloques"],
  ["compass", "Brújula"],
  ["vector", "Vectores"],
  ["graph", "Gráficas"],
  ["cube", "Volumen"],
  ["nodes", "Conexiones"],
] as const;

function IllustrationSvg({ id }: { id: string }) {
  const index = illustrations.findIndex(([key]) => key === id);
  return (
    <svg
      viewBox="0 0 160 130"
      aria-hidden="true"
      className="illustration"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
    >
      {index === 0 && (
        <>
          {[30, 55, 80, 105, 130].map((n) => (
            <path key={n} d={`M${n} 20V110 M20 ${n - 5}H140`} />
          ))}
          <path
            stroke="var(--gold)"
            strokeWidth="12"
            opacity=".5"
            d="M24 96L130 33"
          />
        </>
      )}
      {index === 1 && (
        <>
          <path d="M10 70Q30 0 50 65T90 65T130 65T170 65" />
          <path
            stroke="var(--gold)"
            d="M10 95Q30 25 50 90T90 90T130 90T170 90"
          />
        </>
      )}
      {index === 2 && (
        <>
          <ellipse
            cx="80"
            cy="65"
            rx="65"
            ry="35"
            transform="rotate(-25 80 65)"
          />
          <circle cx="80" cy="65" r="16" fill="var(--gold)" />
          <circle cx="135" cy="31" r="7" fill="currentColor" />
        </>
      )}
      {index === 3 && (
        <>
          <path d="M20 110L80 15L140 110Z M20 110L110 65L80 15 M80 15V110" />
          <circle cx="80" cy="80" r="28" stroke="var(--gold)" />
        </>
      )}
      {index === 4 && (
        <>
          <rect x="17" y="20" width="125" height="90" />
          <path d="M30 40L48 55L30 70 M62 72H95" />
          <path stroke="var(--gold)" d="M17 90H142" />
        </>
      )}
      {index === 5 && (
        <>
          <rect x="55" y="37" width="50" height="50" />
          <path d="M15 20H40V50H55 M105 65H140 M80 87V115 M105 40H130V15" />
          <circle cx="15" cy="20" r="7" fill="var(--gold)" />
          <circle cx="140" cy="65" r="7" fill="var(--gold)" />
        </>
      )}
      {index === 6 && (
        <>
          <rect x="20" y="60" width="50" height="50" />
          <rect x="70" y="10" width="50" height="50" fill="var(--gold)" />
          <rect x="70" y="60" width="50" height="50" />
        </>
      )}
      {index === 7 && (
        <>
          <circle cx="80" cy="65" r="45" />
          <path d="M80 8V122 M23 65H137 M60 85L80 30L100 85L80 65Z" />
          <path d="M80 65L100 85L80 105Z" fill="var(--gold)" />
        </>
      )}
      {index === 8 && (
        <>
          <path d="M20 110H140 M20 110V15 M20 110L130 25 M109 27L130 25L128 46" />
          <path stroke="var(--gold)" d="M20 110L100 75 M82 70L100 75L91 91" />
        </>
      )}
      {index === 9 && (
        <>
          <path d="M15 110H145 M25 120V10 M30 100Q65 100 80 55T135 15" />
          <path stroke="var(--gold)" strokeDasharray="6 5" d="M80 110V55H25" />
        </>
      )}
      {index === 10 && (
        <>
          <path d="M80 15L135 43V95L80 122L25 95V43Z M25 43L80 70L135 43 M80 70V122" />
          <path stroke="var(--gold)" d="M80 15V70" />
        </>
      )}
      {index === 11 && (
        <>
          <path d="M30 30L85 65L130 25 M85 65L25 105 M85 65L130 110" />
          {[
            [30, 30],
            [130, 25],
            [25, 105],
            [130, 110],
            [85, 65],
          ].map(([x, y], n) => (
            <circle
              key={n}
              cx={x}
              cy={y}
              r={n === 4 ? 15 : 9}
              fill={n === 4 ? "var(--gold)" : "var(--paper)"}
            />
          ))}
        </>
      )}
    </svg>
  );
}

/** Usa la ilustración de /art/subjects si existe; si no, el dibujo vectorial. */
export function Illustration({ id }: { id: string }) {
  return (
    <ArtImage src={`/art/subjects/${id}.png`} className="illustration">
      <IllustrationSvg id={id} />
    </ArtImage>
  );
}
