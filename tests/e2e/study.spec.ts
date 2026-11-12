import { test, expect } from "@playwright/test";
import { mkdir, writeFile, unlink } from "node:fs/promises";
import { resolve } from "node:path";
import AxeBuilder from "@axe-core/playwright";

test("private local objects are not served by either frontend origin", async ({
  request,
}) => {
  const directory = resolve(".data");
  await mkdir(directory, { recursive: true });
  const file = resolve(directory, `private-probe-${Date.now()}.txt`);
  await writeFile(file, "SYNTHETIC PRIVATE PROBE");
  try {
    for (const port of [5173, 5174]) {
      const response = await request.get(
        `http://127.0.0.1:${port}/@fs/${file.replaceAll("\\", "/")}`,
      );
      expect([403, 404]).toContain(response.status());
    }
  } finally {
    await unlink(file);
  }
});

test("H2: upload a note, ask with sources, open a citation and recover conversation", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page
    .getByLabel("Correo electrónico")
    .fill(`h2-${Date.now()}@pcpuma.acatlan.unam.mx`);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await page.getByRole("button", { name: "Crear mi primera materia" }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Circuitos H2");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await page.getByRole("button", { name: /Circuitos H2.*temas/ }).click();
  await page.getByLabel("Título de la nota").fill("Ley de Ohm");
  await page
    .getByLabel("Contenido de la nota")
    .fill(
      "Ley de Ohm: V = I R. La resistencia limita la corriente y se mide en ohmios.",
    );
  await page.getByRole("button", { name: "Guardar nota", exact: true }).click();
  await expect(
    page.getByText("Listo para estudiar", { exact: true }),
  ).toBeVisible({ timeout: 30000 });
  await page.getByRole("button", { name: "✦ Abrir tutor" }).click();
  const tutor = page.getByRole("dialog", { name: "Tutor", exact: true });
  await tutor.getByLabel("Fuente: Ley de Ohm").check();
  await tutor
    .getByLabel("Tu pregunta")
    .fill("¿Qué es la resistencia en la ley de Ohm?");
  await tutor.getByRole("button", { name: "Enviar pregunta" }).click();
  await expect(
    tutor.getByRole("button", { name: /Abrir cita S1/ }),
  ).toBeVisible({ timeout: 60000 });
  await tutor.getByRole("button", { name: /Abrir cita S1/ }).click();
  await expect(
    page.getByRole("dialog", { name: "Fuente citada" }),
  ).toContainText(/Ohm|V = I R|resistencia/i);
  await page.getByRole("button", { name: "Cerrar fuente" }).click();
  await page.reload();
  await page.getByRole("button", { name: "✦ Abrir tutor" }).click();
  await page
    .getByLabel("Materia del tutor")
    .selectOption({ label: "Circuitos H2" });
  await page
    .getByRole("combobox", { name: /^Conversación/ })
    .selectOption({ index: 1 });
  await expect(
    page
      .getByRole("dialog", { name: "Tutor", exact: true })
      .getByRole("button", { name: /Abrir cita S1/ }),
  ).toBeVisible();
  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({
    path: ".superpowers/sdd/2026-11-02-plataforma-estudio/h2-tutor.png",
    fullPage: true,
  });
});

test("H2: an image requires review before it can become a source", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page
    .getByLabel("Correo electrónico")
    .fill(`image-${Date.now()}@pcpuma.acatlan.unam.mx`);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await page.getByRole("button", { name: "Crear mi primera materia" }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Física visual");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await page.getByRole("button", { name: /Física visual.*temas/ }).click();
  await page
    .getByLabel("Subir material", { exact: true })
    .setInputFiles(resolve("tests/fixtures/materials/ohm.png"));
  await expect(
    page.getByText("Revisa la transcripción", { exact: true }),
  ).toBeVisible({ timeout: 30000 });
  await page
    .getByRole("button", { name: "Abrir material", exact: true })
    .click();
  await page
    .getByLabel("Texto de la transcripción")
    .fill("Ley de Ohm: V = I R. R = 5 ohmios, I = 2 A, V = 10 V.");
  await page
    .getByRole("button", { name: "Confirmar página y guardar versión" })
    .click();
  await expect(
    page.getByText("Listo para estudiar", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("status").filter({ hasText: "Nueva versión guardada" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: ".superpowers/sdd/2026-11-02-plataforma-estudio/h2-material-mobile.png",
    fullPage: true,
  });
});
