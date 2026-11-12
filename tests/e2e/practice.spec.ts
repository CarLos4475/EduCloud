import { test, expect, Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";

// Recorrido H4: práctica guardada, progreso, tarjetas repasadas, avance del experimento y pasaporte.
const shots = process.env.RESOURCE_SHOTS;
async function shot(page: Page, name: string) {
  if (!shots) return;
  await mkdir(shots, { recursive: true });
  await page.screenshot({ path: `${shots}/${name}.png`, fullPage: true });
}

async function create(page: Page, kind: string) {
  await page.getByRole("button", { name: "+ Crear un recurso" }).click();
  await page.getByText(kind, { exact: true }).first().click();
  await page.getByLabel("Ley de Ohm", { exact: true }).check();
  await page.getByRole("button", { name: "Crear recurso" }).click();
}

test("H4: práctica, progreso, repaso y pasaporte", async ({ page }) => {
  test.setTimeout(420000);
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page
    .getByLabel("Correo electrónico")
    .fill(`h4-${Date.now()}@pcpuma.acatlan.unam.mx`);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await page.getByRole("button", { name: "Crear mi primera materia" }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Circuitos H4");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await page.getByRole("button", { name: /Circuitos H4.*temas/ }).click();
  await page.getByLabel("Título de la nota").fill("Ley de Ohm");
  await page
    .getByLabel("Contenido de la nota")
    .fill(
      "Ley de Ohm: V = I R. La resistencia limita la corriente y se mide en ohmios. " +
        "Si la resistencia aumenta y el voltaje es fijo, la corriente disminuye.",
    );
  await page.getByRole("button", { name: "Guardar nota", exact: true }).click();
  await expect(
    page.getByText("Listo para estudiar", { exact: true }),
  ).toBeVisible({ timeout: 30000 });

  // Antes de practicar, el progreso lo sugiere.
  await expect(page.getByText("Tu progreso")).toBeVisible();
  await expect(page.getByText(/Crea un resumen/)).toBeVisible();
  await shot(page, "h4-01-progreso-inicial");

  // Cuestionario: el servidor guarda y califica.
  await create(page, "Cuestionario");
  await expect(page.getByText(/^1\. /)).toBeVisible({ timeout: 120000 });
  const questions = page.locator(".quiz-question");
  const total = await questions.count();
  for (let i = 0; i < total; i++)
    await questions.nth(i).locator(".quiz-option").first().click();
  await expect(
    page.getByText(/Acertaste \d+ de \d+\. Quedó guardado/),
  ).toBeVisible();
  await shot(page, "h4-02-cuestionario-guardado");
  await page.getByRole("button", { name: /Volver a mis recursos/ }).click();
  await expect(page.getByText("Promedio en cuestionarios")).toBeVisible();
  await expect(
    page
      .locator(".progress-figures div", { hasText: "Promedio" })
      .locator("dd"),
  ).not.toHaveText("—");

  // Tarjetas: repaso guardado entre visitas.
  await create(page, "Tarjetas");
  await expect(page.getByText(/Tarjeta 1 de/)).toBeVisible({ timeout: 120000 });
  await page.getByRole("button", { name: "Ver la respuesta" }).click();
  await page.getByRole("button", { name: "La sabía" }).click();
  await expect(page.getByText(/Sabidas: 1/)).toBeVisible();
  await shot(page, "h4-03-tarjetas-repaso");
  await page.getByRole("button", { name: /Volver a mis recursos/ }).click();
  await page.locator(".resource-card", { hasText: "Tarjetas" }).click();
  await expect(page.getByText(/Sabidas: 1/)).toBeVisible();
  await page.getByRole("button", { name: /Volver a mis recursos/ }).click();

  // Experimento: el avance se conserva al volver a abrirlo.
  await create(page, "Experimento interactivo");
  const frame = page.frameLocator(".interactive iframe");
  await expect(frame.getByText("Listo para explorar.")).toBeVisible({
    timeout: 180000,
  });
  const slider = frame.locator('input[type="range"]').first();
  await slider.focus();
  await page.keyboard.press("End");
  await expect(page.getByText("Tu avance se guarda solo.")).toBeVisible({
    timeout: 10000,
  });
  const saved = await slider.inputValue();
  await page.getByRole("button", { name: /Volver a mis recursos/ }).click();
  await page.locator(".resource-card", { hasText: /interactivo/i }).click();
  await expect(frame.getByText("Listo para explorar.")).toBeVisible({
    timeout: 30000,
  });
  await expect(frame.locator('input[type="range"]').first()).toHaveValue(saved);

  // Pasaporte: estampillas ganadas por actividad real.
  await page.getByRole("button", { name: "Mi perfil" }).first().click();
  await expect(page.getByText("Mi pasaporte")).toBeVisible();
  await expect(
    page.locator(".stamp.earned", { hasText: "Primeros apuntes" }),
  ).toBeVisible();
  await expect(
    page.locator(".stamp.earned", { hasText: "Primer cuestionario" }),
  ).toBeVisible();
  await expect(
    page.locator(".stamp.earned", { hasText: "Explorador" }),
  ).toBeVisible();
  await expect(
    page.locator(".stamp.locked", { hasText: "Tres materias" }),
  ).toBeVisible();
  await shot(page, "h4-04-pasaporte");
});
