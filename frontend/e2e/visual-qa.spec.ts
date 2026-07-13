import { expect, test } from "@playwright/test";

import {
  assertNoHorizontalOverflow,
  installVisualQaSession,
  setupVisualQaApiMocks,
  VISUAL_QA_ROUTES,
} from "./fixtures/visualQa";

test.describe("Phase 7 visual QA", () => {
  test.beforeEach(async ({ context, page }) => {
    await installVisualQaSession(context);
    await setupVisualQaApiMocks(context);
    await page.goto("/today");
    await expect(page.locator("h1.page-header-title")).toHaveText("Today", { timeout: 30_000 });
  });

  for (const route of VISUAL_QA_ROUTES) {
    test(`${route.path} renders without horizontal overflow`, async ({ page }, testInfo) => {
      await page.goto(route.path, { waitUntil: "networkidle" });
      await expect(page.locator("h1.page-header-title")).toHaveText(route.heading, { timeout: 30_000 });
      await assertNoHorizontalOverflow(page);

      const slug = route.path.replace(/\//g, "_").replace(/^_/, "") || "home";
      await page.screenshot({
        path: testInfo.outputPath(`${slug}-${testInfo.project.name}.png`),
        fullPage: true,
      });
    });
  }
});
