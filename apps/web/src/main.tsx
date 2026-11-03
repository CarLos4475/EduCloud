import { createRoot } from "react-dom/client";
import { App } from "./App";
import "@fontsource/alfa-slab-one/latin-400.css";
import "@fontsource/archivo-narrow/latin-400.css";
import "@fontsource/archivo-narrow/latin-700.css";
import "@fontsource/dm-mono/latin-400.css";
import "@fontsource/caveat-brush/latin-400.css";
import "./styles/main.css";

createRoot(document.getElementById("root")!).render(<App />);
