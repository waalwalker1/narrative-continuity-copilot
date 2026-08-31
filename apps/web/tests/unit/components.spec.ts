import { describe, it, expect, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { mount } from "@vue/test-utils";
import { useManuscriptStore } from "@/stores/manuscript";
import ContinuityReviewQueue from "@/components/ContinuityReviewQueue.vue";
import StoryMemoryPanel from "@/components/StoryMemoryPanel.vue";

describe("Frontend Vue Components & Stores", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("initializes manuscript store with default empty state", () => {
    const store = useManuscriptStore();
    expect(store.projects).toEqual([]);
    expect(store.activeRightTab).toBe("continuity");
    expect(store.unresolvedAlerts).toEqual([]);
  });

  it("renders ContinuityReviewQueue and displays alert count", async () => {
    const store = useManuscriptStore();
    store.alerts = [
      {
        alert_id: "alt-1",
        project_id: "proj-1",
        revision_id: "rev-1",
        conflict_class: "ATTRIBUTE_CONTRADICTION",
        confidence: 0.95,
        confidence_category: "HIGH",
        explanation: "Earlier chapter described blue eyes, later green.",
        alternate_interpretations: [],
        evidence_a: {
          anchor_id: "anc-1",
          chapter_id: "chap-1",
          block_id: "blk-1",
          char_start: 0,
          char_end: 20,
          text_snippet: "He had piercing blue eyes.",
          revision_id: "rev-1",
        },
        evidence_b: {
          anchor_id: "anc-2",
          chapter_id: "chap-2",
          block_id: "blk-2",
          char_start: 0,
          char_end: 20,
          text_snippet: "His green eyes narrowed.",
          revision_id: "rev-1",
        },
        requires_author_review: true,
        canonical_status: "PROPOSED",
        suppressed: false,
      },
    ];

    const wrapper = mount(ContinuityReviewQueue);
    expect(wrapper.text()).toContain("Continuity Alerts (1)");
    expect(wrapper.text()).toContain("ATTRIBUTE CONTRADICTION");
    expect(wrapper.text()).toContain("He had piercing blue eyes.");
  });

  it("renders StoryMemoryPanel with entities and facts", async () => {
    const store = useManuscriptStore();
    store.storyMemory = {
      project_id: "proj-1",
      revision_id: "rev-1",
      entities: [
        {
          entity_id: "ent-1",
          project_id: "proj-1",
          canonical_name: "Elizabeth Bennet",
          entity_type: "character",
          aliases: ["Lizzy", "Eliza"],
          canonical_status: "PROPOSED",
          evidence_anchor_ids: ["anc-1"],
        },
      ],
      facts: [
        {
          fact_id: "f-1",
          project_id: "proj-1",
          revision_id: "rev-1",
          subject_entity_id: "ent-1",
          predicate: "eye_color",
          value: "dark",
          narrative_scope: "GLOBAL_CANON",
          epistemic_status: "OBSERVED",
          canonical_status: "PROPOSED",
          confidence: 1.0,
          evidence_anchor_ids: ["anc-1"],
        },
      ],
      relations: [],
      timeline_events: [],
      world_rules: [],
      story_threads: [],
    };

    const wrapper = mount(StoryMemoryPanel);
    expect(wrapper.text()).toContain("Elizabeth Bennet");
    expect(wrapper.text()).toContain("Aliases: Lizzy, Eliza");
    expect(wrapper.text()).toContain("eye_color");
    expect(wrapper.text()).toContain("dark");
  });

  it("safely handles XSS payloads in editor content without execution (SVG, MathML, script)", async () => {
    (window as any).__xss = undefined;
    const store = useManuscriptStore();
    const maliciousPayload =
      '<svg onload="window.__xss = true"></svg>\n' +
      "<math><mtext></mtext></math>\n" +
      "<script>window.__xss = true</script>\n" +
      '<img src=x onerror="window.__xss = true">\n' +
      "Lord Arthur Vance examined the ancient manuscript.";

    store.editorContent = maliciousPayload;
    const { default: QuillEditor } = await import("@/components/QuillEditor.vue");
    const wrapper = mount(QuillEditor, {
      attachTo: document.body,
    });

    // Verify window.__xss was NOT triggered
    expect((window as any).__xss).toBeUndefined();

    // Verify manuscript prose is preserved as plain text
    expect(wrapper.text()).toContain("Lord Arthur Vance examined the ancient manuscript.");
    wrapper.unmount();
  });
});
