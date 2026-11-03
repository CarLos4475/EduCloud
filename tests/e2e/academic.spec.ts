import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("V01 V02 V03: register, create freely, edit illustration, persist and complete agenda", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page
    .getByLabel("Correo electrónico")
    .fill(`student-${Date.now()}@pcpuma.acatlan.unam.mx`);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /TU SIGUIENTE/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("dialog", { name: "Tutor", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Crear mi primera materia" }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Métodos numéricos II");
  await page.getByRole("radio", { name: "Órbitas" }).check();
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.reload();
  await page
    .getByRole("button", { name: /Métodos numéricos II.*temas/ })
    .click();
  await page
    .getByRole("button", { name: "Editar materia", exact: true })
    .click();
  await page
    .getByLabel("Nombre", { exact: true })
    .fill("Análisis numérico propio");
  await page.getByRole("radio", { name: "Circuitos" }).check();
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Análisis numérico propio",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "+ Agregar tema" }).click();
  await page.getByLabel("Título", { exact: true }).fill("Interpolación");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Interpolación", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "+ Agregar", exact: true }).click();
  await page.getByLabel("Título", { exact: true }).fill("Preparar examen");
  await page.getByLabel("Día completo", { exact: true }).fill("2026-12-10");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await page.getByRole("button", { name: "Agenda", exact: true }).click();
  await Promise.all([
    page.waitForResponse(
      (response) =>
        response.request().method() === "PATCH" &&
        response.url().includes("/agenda/") &&
        response.status() === 200,
    ),
    page.getByRole("checkbox", { name: "Completar Preparar examen" }).check(),
  ]);
  await page.reload();
  await page.getByRole("button", { name: "Agenda", exact: true }).click();
  await expect(
    page.getByRole("checkbox", { name: "Completar Preparar examen" }),
  ).toBeChecked();
  await page.getByRole("button", { name: "Mi perfil", exact: true }).click();
  await page.getByLabel("Cómo te llamamos").fill("Estudiante de prueba");
  await page.getByLabel("Carrera (opcional)").fill("Ingeniería");
  await page
    .getByRole("button", { name: "Guardar perfil", exact: true })
    .click();
  await expect(
    page.getByRole("status").filter({ hasText: "Perfil actualizado." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "+ Nuevo", exact: true }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Semestre 2026-II");
  await page.getByLabel("Inicio", { exact: true }).fill("2026-08-01");
  await page.getByLabel("Fin", { exact: true }).fill("2026-12-20");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("button", { name: "Horario", exact: true }).click();
  await page
    .getByRole("button", { name: "+ Agregar clase", exact: true })
    .click();
  await page
    .getByRole("combobox", { name: "Materia", exact: true })
    .selectOption({ label: "Análisis numérico propio" });
  await page.getByLabel("Días sin clase (opcional)").fill("2026-12-25");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(
    page.getByRole("heading", {
      name: "Análisis numérico propio",
      exact: true,
    }),
  ).toBeVisible();
  await page.reload();
  await page.getByRole("button", { name: "Horario", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Análisis numérico propio",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Inicio", exact: true }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({
    path: ".superpowers/sdd/2026-11-02-plataforma-estudio/desktop-home.png",
    fullPage: true,
  });
  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
});

test("mobile layout and account isolation across sign out", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page
    .getByLabel("Correo electrónico")
    .fill(`mobile-${Date.now()}@pcpuma.acatlan.unam.mx`);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /TU SIGUIENTE/ }),
  ).toBeVisible();
  await expect(page.locator(".subject-card")).toHaveCount(0);
  const fits = await page.evaluate(
    () => document.documentElement.scrollWidth <= window.innerWidth,
  );
  expect(fits).toBe(true);
  await page.screenshot({
    path: ".superpowers/sdd/2026-11-02-plataforma-estudio/mobile-home.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Crear mi primera materia" }).click();
  await page
    .getByLabel("Nombre", { exact: true })
    .fill("Materia privada móvil");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("button", { name: "Salir", exact: true }).click();
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page
    .getByLabel("Correo electrónico")
    .fill(`other-${Date.now()}@pcpuma.acatlan.unam.mx`);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /TU SIGUIENTE/ }),
  ).toBeVisible();
  await expect(page.locator(".subject-card")).toHaveCount(0);
  await expect(
    page.getByText("Materia privada móvil", { exact: true }),
  ).toHaveCount(0);
});

test("institutional domain is required before account creation", async ({
  page,
}) => {
  const signupRequests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("accounts:signUp"))
      signupRequests.push(request.url());
  });
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page.getByLabel("Correo electrónico").fill("outside@example.test");
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText(
    "@pcpuma.acatlan.unam.mx",
  );
  expect(signupRequests).toEqual([]);
});
