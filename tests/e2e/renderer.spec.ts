import { test, expect } from "@playwright/test";

test("DeepSeek-generated Ohm explorer runs inside the same capability sandbox", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:5173/h0.html");
  await page
    .getByRole("button", { name: "Recurso creado por DeepSeek" })
    .click();
  const frame = page.frameLocator("iframe");
  await expect(frame.locator("#voltaje")).toHaveText("Voltaje: 10 V");
  await expect(frame.locator("#status")).toHaveText("Listo para explorar.");
  await frame.locator("#resistencia").fill("4");
  await expect(frame.locator("#voltaje")).toHaveText("Voltaje: 8 V");
});

test("three resource families compute and react in the isolated frame", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:5173/h0.html");
  const frame = page.frameLocator("iframe");
  await expect(frame.locator("#status")).toHaveText("Listo para explorar.");
  await expect(frame.locator("#result")).toHaveText("f(2) = 4");
  await frame.locator("#a").fill("2");
  await expect(frame.locator("#result")).toHaveText("f(2) = 8");
  await page
    .getByRole("button", { name: "Movimiento sin aceleración" })
    .click();
  await expect(frame.locator("#result")).toHaveText("A los 5 s: 15 m");
  await page.getByRole("button", { name: "Ordena paso a paso" }).click();
  for (let i = 0; i < 10; i++)
    await frame.getByRole("button", { name: "Siguiente comparación" }).click();
  await expect(frame.locator("#array")).toHaveText("1 · 2 · 3 · 4 · 5");
  await expect(frame.locator("#result")).toHaveText("Lista ordenada.");
  await page.screenshot({
    path: ".superpowers/sdd/2026-11-02-plataforma-estudio/laboratorio.png",
    fullPage: true,
  });
});

test("generated code cannot access network or native DOM and infinite loop is recoverable", async ({
  page,
}) => {
  const external: string[] = [];
  page.on("request", (r) => {
    if (
      !r.url().startsWith("http://127.0.0.1:") &&
      !r.url().startsWith("blob:") &&
      !r.url().startsWith("data:")
    )
      external.push(r.url());
  });
  await page.goto("http://127.0.0.1:5173/h0.html");
  await page.setContent(
    '<iframe title="Test runtime" sandbox="allow-scripts allow-same-origin" src="http://127.0.0.1:5174"></iframe>',
  );
  const frame = page.frameLocator("iframe");
  await expect(frame.locator("#title")).toHaveText("Un espacio para explorar.");
  async function load(
    javascript: string,
    sequence: number,
    html = '<p id="result"></p>',
  ) {
    await page.evaluate(
      ({ javascript, sequence, html }) => {
        document
          .querySelector("iframe")!
          .contentWindow!.postMessage(
            {
              protocolVersion: 1,
              channelId: "test-channel-123456789",
              sequence,
              type: "load",
              payload: {
                package: {
                  schemaVersion: 1,
                  title: "Seguridad",
                  learningObjective: "Prueba",
                  instructions: "Prueba",
                  html,
                  css: "",
                  javascript,
                  initialState: {},
                  textAlternative: "Alternativa",
                  sourceRefs: [],
                  requestedCapabilities: ["controls"],
                },
              },
            },
            "http://127.0.0.1:5174",
          );
      },
      { javascript, sequence, html },
    );
  }
  await load(
    `ui.patch('result',{text:[typeof window,typeof document,typeof fetch,typeof WebSocket,typeof localStorage].join(',')});`,
    1,
    '<p id="result"></p><img src="https://example.com/steal" onerror="alert(1)"><script>fetch("https://example.com/steal")</script>',
  );
  await expect(frame.locator("#result")).toHaveText(
    "undefined,undefined,undefined,undefined,undefined",
  );
  await expect(frame.locator("#resource img")).toHaveCount(0);
  await expect(frame.locator("#resource script")).toHaveCount(0);
  await load("while(true){}", 2);
  await expect(frame.locator("#status")).toContainText("se detuvo");
  await load(`ui.patch('result',{text:'Recuperado'});`, 3);
  await expect(frame.locator("#result")).toHaveText("Recuperado");
  expect(external).toEqual([]);
});
