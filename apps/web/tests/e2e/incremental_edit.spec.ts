import { test, expect } from "@playwright/test";

test.describe("Flow C: Incremental Scoped Edit & Anchor Persistence", () => {
  test("creates 3-chapter manuscript, edits chapter 2, and verifies preservation of chapters 1 & 3", async ({
    page,
    request,
  }) => {
    // 1. Seed deterministic test project
    const projRes = await request.post("http://localhost:8000/api/v1/projects", {
      data: { title: "Preservation Saga", genre_hint: "Fantasy", privacy_mode: "LOCAL_ONLY" },
    });
    expect(projRes.ok()).toBeTruthy();
    const proj = await projRes.json();
    const projectId = proj.project_id;
    const initialRevId = proj.active_revision_id;

    // 2. Import 3-chapter manuscript (AAA, BBB, CCC)
    const sampleText =
      "# Chapter 1: The First Realm\n\nAAA\n\n" +
      "# Chapter 2: The Middle Tower\n\nBBB\n\n" +
      "# Chapter 3: The Far Reach\n\nCCC";

    const impRes = await request.post(`http://localhost:8000/api/v1/projects/${projectId}/import`, {
      data: { format: "markdown", content_text: sampleText },
    });
    expect(impRes.ok()).toBeTruthy();

    const idxRes = await request.post(`http://localhost:8000/api/v1/projects/${projectId}/index`, {
      data: { incremental: false },
    });
    expect(idxRes.ok()).toBeTruthy();

    // 3. Open Browser
    await page.goto("http://localhost:3000");

    const selectElem = page.locator("select").first();
    await selectElem.selectOption(projectId);

    // Verify 3 chapters appear in navigation
    await expect(page.locator("nav")).toContainText("Chapter 1: The First Realm");
    await expect(page.locator("nav")).toContainText("Chapter 2: The Middle Tower");
    await expect(page.locator("nav")).toContainText("Chapter 3: The Far Reach");

    // Click Chapter 2 in sidebar
    await page.locator("nav").getByText("Chapter 2: The Middle Tower").click();

    // Verify Chapter 2 content is BBB
    const editor = page.locator(".ql-editor");
    await expect(editor).toContainText("BBB");

    // Edit Chapter 2: BBB -> BBB EDITED
    await editor.click();
    await page.keyboard.press("Meta+A");
    await page.keyboard.press("Backspace");
    await page.keyboard.type("BBB EDITED");

    // Wait for save & index response
    const savePromise = page.waitForResponse(
      (resp) => resp.url().includes("/revisions/from-edits") && resp.status() === 200
    );
    const indexPromise = page.waitForResponse(
      (resp) => resp.url().includes("/index") && resp.status() === 200
    );

    const saveBtn = page.getByRole("button", { name: "Save Revision" });
    await saveBtn.click();
    await savePromise;
    await indexPromise;

    // 4. Reload Browser to verify full state persistence
    await page.reload();
    await page.locator("select").selectOption(projectId);

    // Verify structure still has all three chapters
    await expect(page.locator("nav")).toContainText("Chapter 1: The First Realm");
    await expect(page.locator("nav")).toContainText("Chapter 2: The Middle Tower");
    await expect(page.locator("nav")).toContainText("Chapter 3: The Far Reach");

    // Verify Chapter 1 contains AAA
    await page.locator("nav").getByText("Chapter 1: The First Realm").click();
    await expect(page.locator(".ql-editor")).toContainText("AAA");

    // Verify Chapter 2 contains BBB EDITED
    await page.locator("nav").getByText("Chapter 2: The Middle Tower").click();
    await expect(page.locator(".ql-editor")).toContainText("BBB EDITED");

    // Verify Chapter 3 contains CCC
    await page.locator("nav").getByText("Chapter 3: The Far Reach").click();
    await expect(page.locator(".ql-editor")).toContainText("CCC");

    // Verify active revision changed via API
    const projectRes = await request.get(`http://localhost:8000/api/v1/projects/${projectId}`);
    const updatedProject = await projectRes.json();
    expect(updatedProject.active_revision_id).not.toBe(initialRevId);
  });
});
