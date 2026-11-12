export type Kind =
  "summary" | "concepts" | "flashcards" | "quiz" | "interactive";

export const KINDS: { id: Kind; label: string; hint: string }[] = [
  {
    id: "summary",
    label: "Resumen",
    hint: "Lo esencial de tus apuntes en pocas líneas.",
  },
  {
    id: "concepts",
    label: "Conceptos clave",
    hint: "Los términos importantes, bien explicados.",
  },
  {
    id: "flashcards",
    label: "Tarjetas",
    hint: "Para repasar y memorizar con calma.",
  },
  {
    id: "quiz",
    label: "Cuestionario",
    hint: "Preguntas para ver qué tanto dominas.",
  },
  {
    id: "interactive",
    label: "Experimento interactivo",
    hint: "Mueve los controles y mira cómo cambia la idea.",
  },
];

export type MaterialLite = { id: string; name: string; status: string };

export type Citation = {
  materialId: string;
  extractionVersion: string;
  blockId: string;
  locator: string;
  quote?: string | null;
};

export type ResourceVersion = {
  id: string;
  resourceId: string;
  number: number;
  instruction: string;
  status: string;
  stage: string;
  error?: string | null;
  usageUnknown: boolean;
  jobId: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  content?: any;
  citations: Citation[];
  textAlternative?: string | null;
  sourcesChanged: boolean;
  createdAt: string;
};

export type ResourceRow = {
  id: string;
  revision: number;
  subjectId: string;
  kind: Kind;
  title: string;
  materialIds: string[];
  archived: boolean;
  versionCount: number;
  latestStatus?: string | null;
  currentVersionId?: string | null;
  latestVersionId?: string | null;
};

export type ResourceDetail = ResourceRow & { versions: ResourceVersion[] };
