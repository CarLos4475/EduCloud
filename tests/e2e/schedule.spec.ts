import { test, expect } from "@playwright/test";

test("el aviso de primera materia desaparece y una clase puede ir en varios días", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page
    .getByLabel("Correo electrónico")
    .fill(`hor-${Date.now()}@pcpuma.acatlan.unam.mx`);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();

  // Sin materias, Inicio invita a crear la primera.
  await expect(
    page.getByRole("button", { name: "Crear mi primera materia" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Crear mi primera materia" }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Cálculo");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);

  // Con una materia, el aviso ya no aparece.
  await page.getByRole("button", { name: "Inicio", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Mis materias" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Crear mi primera materia" }),
  ).toHaveCount(0);
  await expect(page.getByText("PRIMERA PARADA")).toHaveCount(0);

  // Una clase en varios días: lunes, miércoles y viernes.
  await page.getByRole("button", { name: "Horario", exact: true }).click();
  await page
    .getByRole("button", { name: "+ Agregar clase", exact: true })
    .click();
  await page
    .getByRole("combobox", { name: "Materia", exact: true })
    .selectOption({ label: "Cálculo" });
  await page.getByRole("button", { name: "Lun, mié y vie" }).click();
  await page.getByLabel("Desde").fill("08:00");
  await page.getByLabel("Hasta").fill("09:30");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Cálculo" })).toHaveCount(3);

  // Hay que elegir al menos un día.
  await page
    .getByRole("button", { name: "+ Agregar clase", exact: true })
    .click();
  await page
    .getByRole("combobox", { name: "Materia", exact: true })
    .selectOption({ label: "Cálculo" });
  await page.getByLabel("Lun", { exact: true }).uncheck();
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByText("Elige al menos un día.")).toBeVisible();
  await page.getByLabel("Mar", { exact: true }).check();
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Cálculo" })).toHaveCount(4);

  // Al editar, cada bloque sigue siendo de un solo día.
  await page
    .getByRole("button", { name: /^Editar clase/ })
    .first()
    .click();
  await expect(page.getByRole("combobox", { name: /^Día/ })).toBeVisible();
  await expect(page.getByText("Días de la semana")).toHaveCount(0);
});
