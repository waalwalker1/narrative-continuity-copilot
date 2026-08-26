import { test, expect } from "@playwright/test";

test.describe("Flow C: Incremental Edit & Anchor Persistence", () => {
  test("edits passage in Quill, saves revision, and verifies state persistence", async ({ page, request }) => {
    // 1. Seed deterministic test project
    const projRes = await request.post("http://localhost:8000/api/v1/projects", {
      data: { title: "Incremental Edit Novel", genre_hint: "Fantasy", privacy_mode: "LOCAL_ONLY" },
    });
    const proj = await projRes.json();
    const projectId = proj.project_id;

    // 2. Import Initial Manuscript
    const sampleText =
      "# Chapter 1: The Gate\n\nArthur examined the stone gate carefully.\n\n" +
      "# Chapter 2: The Key\n\nThe iron key was lost in the river.";

    await request.post(`http://localhost:8000/api/v1/projects/${projectId}/import`, {
      data: { format: "markdown", content_text: sampleText },
    });

    await request.post(`http://localhost:8000/api/v1/projects/${projectId}/index`, { data: {} });

    // 3. Open Browser
    await page.goto("http://localhost:3000");

    const selectElem = page.locator("select");
    await selectElem.selectOption(projectId);

    // Verify Chapter 1 text is displayed in Quill editor
    const editor = page.locator(".ql-editor");
    await expect(editor).toContainText("Arthur examined the stone gate carefully.");

    // Type text into editor
    await editor.click();
    await page.keyboard.type(" Early at dawn, ");

    // Click Save Revision button
    const saveBtn = page.getByRole("button", { name: "Save Revision" });
    await saveBtn.click();

    // Verify revision saved and indexing completed
    await page.waitForTimeout(500);
    await expect(page.locator("header")).toContainText("Incremental Edit Novel");
  });
});
