import { test, expect, Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir } from "node:fs/promises";

const shots = process.env.RESOURCE_SHOTS;
async function shot(page: Page, name: string) {
  if (!shots) return;
  await mkdir(shots, { recursive: true });
  await page.screenshot({ path: `${shots}/${name}.png`, fullPage: true });
}
async function audit(page: Page, where: string) {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(
    result.violations.map(
      (v) =>
        `${where}: ${v.id} -> ${v.nodes.map((n) => n.target.join(" ") + " " + (n.any[0]?.message ?? "")).join(" | ")}`,
    ),
  ).toEqual([]);
}

for (const [label, size] of [
  ["escritorio", { width: 1280, height: 900 }],
  ["movil", { width: 390, height: 844 }],
] as const) {
  test(`accesibilidad de recursos, progreso y pasaporte (${label})`, async ({
    page,
  }) => {
    test.setTimeout(90000);
    await page.setViewportSize(size);
    await page.goto("http://127.0.0.1:5173");
    await page.getByRole("button", { name: "Es mi primera visita" }).click();
    await page
      .getByLabel("Correo electrónico")
      .fill(`a11y-${label}-${Date.now()}@pcpuma.acatlan.unam.mx`);
    await page
      .getByLabel("Contraseña", { exact: true })
      .fill("Local-study-2026!");
    await page
      .getByRole("button", { name: "Crear cuenta", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Crear mi primera materia" })
      .click();
    await page.getByLabel("Nombre", { exact: true }).fill("Accesible");
    await page.getByRole("button", { name: "Guardar", exact: true }).click();
    await page.getByRole("button", { name: /Accesible.*temas/ }).click();
    await expect(page.getByText("Tu progreso")).toBeVisible();
    await audit(page, "materia con recursos y progreso");
    await shot(page, `a11y-${label}-01-materia`);

    await page.getByRole("button", { name: "+ Crear un recurso" }).click();
    await expect(page.getByText("¿Qué quieres crear?")).toBeVisible();
    await audit(page, "formulario de recurso");
    await shot(page, `a11y-${label}-02-formulario`);

    await page.getByRole("button", { name: "Mi perfil" }).first().click();
    await expect(page.getByText("Mi pasaporte")).toBeVisible();
    await expect(page.locator(".stamp")).toHaveCount(8);
    await audit(page, "pasaporte");
    await shot(page, `a11y-${label}-03-pasaporte`);

    for (const [name, title] of [
      ["Inicio", "inicio"],
      ["Agenda", "agenda"],
      ["Horario", "horario"],
    ] as const) {
      await page.getByRole("button", { name }).first().click();
      await page.waitForTimeout(500);
      await audit(page, title);
      await shot(page, `a11y-${label}-04-${title}`);
    }
  });
}
