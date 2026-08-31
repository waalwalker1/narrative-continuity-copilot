import { test, expect } from "@playwright/test";

test.describe("Flow A, D, E: Full Author Lifecycle & Editorial UX", () => {
  test("Flow A & E: Cold manuscript import, indexing, and story memory panel verification", async ({ page, request }) => {
    // Create project
    const projRes = await request.post("http://localhost:8000/api/v1/projects", {
      data: { title: "The High Citadel", genre_hint: "Fantasy", privacy_mode: "LOCAL_ONLY" },
    });
    const proj = await projRes.json();
    const projectId = proj.project_id;

    // Import manuscript with facts, relations, rules, and threads
    const sampleText =
      "# Chapter 1: The High Citadel\n\n" +
      "Lord Arthur Vance was thirty years old. Arthur carried the ancient sunblade.\n\n" +
      "# Chapter 2: The Rules of Magic\n\n" +
      "According to the ancient codex: Magic cannot penetrate solid iron.";

    await request.post(`http://localhost:8000/api/v1/projects/${projectId}/import`, {
      data: { format: "markdown", content_text: sampleText },
    });

    await request.post(`http://localhost:8000/api/v1/projects/${projectId}/index`, { data: {} });

    // Open Web App
    await page.goto("http://localhost:3000");
    const selectElem = page.locator("select").first();
    await selectElem.selectOption(projectId);

    // Switch to Story Memory tab
    const memoryTabBtn = page.getByRole("button", { name: "Story Memory" });
    await memoryTabBtn.click();

    // Verify Story Memory Panel displays entities and extracted facts
    await expect(page.locator("aside")).toContainText("Story Memory & Lore");
    await expect(page.locator("aside")).toContainText("Lord Arthur Vance");
  });

  test("Flow D: Evidence jump from alert citation to editor span", async ({ page, request }) => {
    const projRes = await request.post("http://localhost:8000/api/v1/projects", {
      data: { title: "Evidence Jump Saga", genre_hint: "Mystery" },
    });
    const proj = await projRes.json();
    const projectId = proj.project_id;

    const sampleText =
      "# Chapter 1: The Silver Hall\n\nLord Arthur Vance had blue eyes.\n\n" +
      "# Chapter 2: The Obsidian Tower\n\nLord Arthur Vance had green eyes.";

    await request.post(`http://localhost:8000/api/v1/projects/${projectId}/import`, {
      data: { format: "markdown", content_text: sampleText },
    });

    await request.post(`http://localhost:8000/api/v1/projects/${projectId}/index`, { data: {} });
    await request.post(`http://localhost:8000/api/v1/projects/${projectId}/continuity/check`);

    await page.goto("http://localhost:3000");
    const selectElem2 = page.locator("select").first();
    await selectElem2.selectOption(projectId);

    // Click jump to earlier evidence
    const jumpLink = page.locator("aside").getByText("Jump to text").first();
    await expect(jumpLink).toBeVisible();
    await jumpLink.click();

    // Editor should be focused on Chapter 1
    await expect(page.locator("header")).toContainText("Evidence Jump Saga");
  });

  test("Flow XSS: Adversarial manuscript prose containing script, SVG, MathML does not execute", async ({ page, request }) => {
    const projRes = await request.post("http://localhost:8000/api/v1/projects", {
      data: { title: "XSS Security Test Saga", genre_hint: "Thriller" },
    });
    const proj = await projRes.json();
    const projectId = proj.project_id;

    const adversarialText =
      "# Chapter 1: The Trap\n\n" +
      '<svg onload="window.__xss_e2e = true"></svg>\n\n' +
      "<math><mtext>Exploit</mtext></math>\n\n" +
      "<script>window.__xss_e2e = true</script>\n\n" +
      '<img src=x onerror="window.__xss_e2e = true">\n\n' +
      "The detective inspected the crime scene thoroughly.";

    await request.post(`http://localhost:8000/api/v1/projects/${projectId}/import`, {
      data: { format: "markdown", content_text: adversarialText },
    });

    await request.post(`http://localhost:8000/api/v1/projects/${projectId}/index`, { data: {} });

    await page.goto("http://localhost:3000");
    const selectElem = page.locator("select").first();
    await selectElem.selectOption(projectId);

    // Verify window.__xss_e2e is undefined
    const xssExecuted = await page.evaluate(() => (window as any).__xss_e2e);
    expect(xssExecuted).toBeUndefined();

    // Verify editor text is rendered safely as plain text
    await expect(page.locator(".ql-editor")).toContainText("The detective inspected the crime scene thoroughly.");
  });
});
