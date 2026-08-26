import { test, expect } from "@playwright/test";

test.describe("Flow B: Continuity Review & Author Decision", () => {
  test("loads project, inspects continuity alert, and applies author decision", async ({ page, request }) => {
    // 1. Seed deterministic test project via API
    const projRes = await request.post("http://localhost:8000/api/v1/projects", {
      data: { title: "E2E Test Novel", genre_hint: "Mystery", privacy_mode: "LOCAL_ONLY" },
    });
    expect(projRes.ok()).toBeTruthy();
    const proj = await projRes.json();
    const projectId = proj.project_id;

    // 2. Import manuscript with deliberate attribute contradiction
    const sampleText =
      "# Chapter 1: The Encounter\n\nArthur had piercing blue eyes.\n\n" +
      "# Chapter 2: The Truth\n\nArthur had green eyes.";

    const importRes = await request.post(`http://localhost:8000/api/v1/projects/${projectId}/import`, {
      data: { format: "markdown", content_text: sampleText },
    });
    expect(importRes.ok()).toBeTruthy();

    // 3. Trigger Indexing & Continuity Check
    const idxRes = await request.post(`http://localhost:8000/api/v1/projects/${projectId}/index`, {
      data: {},
    });
    expect(idxRes.ok()).toBeTruthy();

    const checkRes = await request.post(`http://localhost:8000/api/v1/projects/${projectId}/continuity/check`);
    expect(checkRes.ok()).toBeTruthy();

    // 4. Open web application in browser
    await page.goto("http://localhost:3000");

    // Verify workspace loaded
    await expect(page.locator("header")).toContainText("Narrative Copilot");

    // Select project if needed
    const selectElem = page.locator("select");
    await selectElem.selectOption(projectId);

    // Verify Chapter 1 is loaded
    await expect(page.locator("nav")).toContainText("Chapter 1");

    // Verify Continuity Alert is visible
    await expect(page.locator("aside")).toContainText("ATTRIBUTE CONTRADICTION");

    // Click 'Mark Intentional'
    const intentionalBtn = page.getByRole("button", { name: "Mark Intentional" }).first();
    await expect(intentionalBtn).toBeVisible();
    await intentionalBtn.click();

    // Verify alert is marked/resolved
    await page.waitForTimeout(500);
    await expect(page.locator("aside")).toContainText("No continuity issues detected in current manuscript revision.");
  });
});
