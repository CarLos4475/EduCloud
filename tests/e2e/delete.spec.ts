import { test, expect } from "@playwright/test";

test("T24: eliminar una materia pide confirmación y la borra con sus datos", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page
    .getByLabel("Correo electrónico")
    .fill(`del-${Date.now()}@pcpuma.acatlan.unam.mx`);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await page.getByRole("button", { name: "Crear mi primera materia" }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Para borrar");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await page.getByRole("button", { name: /Para borrar.*temas/ }).click();
  await page.getByLabel("Título de la nota").fill("Apunte");
  await page.getByLabel("Contenido de la nota").fill("Contenido de prueba.");
  await page.getByRole("button", { name: "Guardar nota", exact: true }).click();
  await expect(
    page.getByText("Listo para estudiar", { exact: true }),
  ).toBeVisible({ timeout: 30000 });

  let message = "";
  page.once("dialog", (dialog) => {
    message = dialog.message();
    void dialog.dismiss();
  });
  await page.getByRole("button", { name: "Eliminar materia" }).click();
  await expect.poll(() => message).toContain("no se puede deshacer");
  await expect(
    page.getByRole("heading", { name: "Para borrar" }),
  ).toBeVisible();

  page.once("dialog", (dialog) => void dialog.accept());
  await page.getByRole("button", { name: "Eliminar materia" }).click();
  await expect(page.getByText("Materia eliminada.")).toBeVisible();
  await expect(page.getByRole("button", { name: /Para borrar/ })).toHaveCount(
    0,
  );
  await page.reload();
  await expect(page.getByText("Para borrar")).toHaveCount(0);
});

test("T24: borrar todo elimina los datos y cierra la cuenta", async ({
  page,
}) => {
  const email = `wipe-${Date.now()}@pcpuma.acatlan.unam.mx`;
  await page.goto("http://127.0.0.1:5173");
  await page.getByRole("button", { name: "Es mi primera visita" }).click();
  await page.getByLabel("Correo electrónico").fill(email);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Crear cuenta", exact: true }).click();
  await page.getByRole("button", { name: "Crear mi primera materia" }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Se va todo");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByRole("button", { name: /Se va todo/ })).toBeVisible();

  await page.getByRole("button", { name: "Mi perfil" }).first().click();
  await page.getByText("Borrar todo lo que he guardado").click();
  const erase = page.getByRole("button", { name: "Borrar todo", exact: true });
  await expect(erase).toBeDisabled();
  await page.getByLabel("Escribe ELIMINAR para confirmar").fill("eliminar");
  await expect(erase).toBeDisabled();
  await page.getByLabel("Escribe ELIMINAR para confirmar").fill("ELIMINAR");
  await erase.click();
  await expect(
    page.getByRole("button", { name: "Entrar a mi campus" }),
  ).toBeVisible({ timeout: 15000 });

  // La cuenta ya no existe: iniciar sesión con las mismas credenciales falla.
  await page.getByLabel("Correo electrónico").fill(email);
  await page
    .getByLabel("Contraseña", { exact: true })
    .fill("Local-study-2026!");
  await page.getByRole("button", { name: "Entrar a mi campus" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
});
