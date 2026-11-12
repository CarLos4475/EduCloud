import { test, expect, Page } from "@playwright/test";
import { mkdir } from "node:fs/promises";

// Recorrido H3: apuntes -> recurso (cada tipo) -> versión nueva -> volver a abrirlo.
// Usa el tutor real si hay clave configurada; con proveedor de prueba también pasa.
const shots = process.env.RESOURCE_SHOTS;

async function shot(page: Page, name: string) {
  if (!shots) return;
  await mkdir(shots, { recursive: true });
  await page.screenshot({ path: `${shots}/${name}.png`, fullPage: true });
}

async function prepare(page: Page) {
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page
    .getByLabel("Correo electrónico")
    .fill(`h3-${Date.now()}@pcpuma.acatlan.unam.mx`);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await page.getByRole("button", { name: "Crear mi primera materia" }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Circuitos H3");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await page.getByRole("button", { name: /Circuitos H3.*temas/ }).click();
  await page.getByLabel("Título de la nota").fill("Ley de Ohm");
  await page
    .getByLabel("Contenido de la nota")
    .fill(
      "Ley de Ohm: V = I R. La resistencia limita la corriente y se mide en ohmios. " +
        "Si la resistencia aumenta y el voltaje es fijo, la corriente disminuye. " +
        "La potencia disipada en una resistencia es P = V I = I^2 R.",
    );
  await page.getByRole("button", { name: "Guardar nota", exact: true }).click();
  await expect(
    page.getByText("Listo para estudiar", { exact: true }),
  ).toBeVisible({ timeout: 30000 });
}

async function create(page: Page, kind: string, instruction = "") {
  await page.getByRole("button", { name: "+ Crear un recurso" }).click();
  await page.getByText(kind, { exact: true }).first().click();
  if (instruction)
    await page.getByLabel(/algo en particular/i).fill(instruction);
  await page.getByLabel("Ley de Ohm", { exact: true }).check();
  await page.getByRole("button", { name: "Crear recurso" }).click();
}

test("H3: crea y revisa los cinco tipos de recurso", async ({ page }) => {
  test.setTimeout(420000);
  await prepare(page);
  await shot(page, "01-materia");

  // Esqueleto/espera visible mientras se prepara.
  await create(page, "Resumen", "Explica la relación entre V, I y R");
  await expect(
    page.getByText(/en la fila|preparando tu recurso/i),
  ).toBeVisible();
  await shot(page, "02-preparando");
  await expect(page.getByText("De dónde sale")).toBeVisible({
    timeout: 120000,
  });
  await shot(page, "03-resumen");
  await page.getByRole("button", { name: /Volver a mis recursos/ }).click();

  await create(page, "Tarjetas");
  await expect(page.getByText(/Tarjeta 1 de/)).toBeVisible({ timeout: 120000 });
  await page.getByRole("button", { name: "Ver la respuesta" }).click();
  await shot(page, "04-tarjetas");
  await page.getByRole("button", { name: /Volver a mis recursos/ }).click();

  await create(page, "Cuestionario");
  await expect(page.getByText(/^1\. /)).toBeVisible({ timeout: 120000 });
  await page.locator(".quiz-option").first().click();
  await expect(page.locator(".quiz-feedback")).toBeVisible();
  await shot(page, "05-cuestionario");
  await page.getByRole("button", { name: /Volver a mis recursos/ }).click();

  await create(page, "Conceptos clave");
  await expect(page.locator(".concept-card").first()).toBeVisible({
    timeout: 120000,
  });
  await shot(page, "06-conceptos");
  await page.getByRole("button", { name: /Volver a mis recursos/ }).click();

  await create(page, "Experimento interactivo", "Una gráfica de V contra R");
  await expect(page.locator(".interactive iframe")).toBeVisible({
    timeout: 180000,
  });
  const frame = page.frameLocator(".interactive iframe");
  await expect(frame.getByText("Listo para explorar.")).toBeVisible({
    timeout: 30000,
  });
  await shot(page, "07-interactivo");

  // Versión nueva sin perder la anterior.
  await page.getByLabel("¿Quieres cambiar algo?").fill("Hazlo más sencillo");
  await page.getByRole("button", { name: "Crear una versión nueva" }).click();
  await expect(page.getByRole("button", { name: /Versión 2/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /Versión 1/ })).toBeVisible();
  await expect(frame.getByText("Listo para explorar.")).toBeVisible({
    timeout: 180000,
  });
  await shot(page, "08-version-2");

  // La biblioteca conserva todo tras recargar.
  await page.reload();
  await page.getByRole("button", { name: /Circuitos H3.*temas/ }).click();
  await expect(page.locator(".resource-card")).toHaveCount(5);
  await shot(page, "09-biblioteca");
});
