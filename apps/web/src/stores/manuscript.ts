import { defineStore } from "pinia";
import {
  type ContinuityAlert,
  type ManuscriptProject,
  type StoryMemory,
  type StructuralUnit,
  applyAuthorDecision,
  fetchAlerts,
  fetchProjects,
  fetchStoryMemory,
  fetchStructure,
  indexProject,
  runContinuityCheck,
} from "@/services/api";

export const useManuscriptStore = defineStore("manuscript", {
  state: () => ({
    projects: [] as ManuscriptProject[],
    currentProject: null as ManuscriptProject | null,
    structure: [] as StructuralUnit[],
    activeChapterId: null as string | null,
    alerts: [] as ContinuityAlert[],
    selectedAlert: null as ContinuityAlert | null,
    storyMemory: null as StoryMemory | null,
    editorContent: "" as string,
    activeRightTab: "continuity" as "continuity" | "memory" | "timeline" | "search",
    isLoading: false,
    highlightAnchorId: null as string | null,
  }),

  getters: {
    chapters: (state) => state.structure.filter((u) => u.unit_type === "chapter"),
    currentChapterBlocks: (state) => {
      if (!state.activeChapterId) return [];
      const sceneIds = new Set(
        state.structure
          .filter((u) => u.unit_type === "scene" && u.parent_id === state.activeChapterId)
          .map((u) => u.unit_id)
      );
      return state.structure.filter(
        (u) =>
          u.unit_type === "block" &&
          (u.parent_id === state.activeChapterId || (u.parent_id && sceneIds.has(u.parent_id)))
      );
    },
    unresolvedAlerts: (state) => state.alerts.filter((a) => !a.suppressed),
  },

  actions: {
    async loadProjects() {
      this.isLoading = true;
      try {
        this.projects = await fetchProjects();
        if (this.projects.length > 0 && !this.currentProject) {
          await this.selectProject(this.projects[0].project_id);
        }
      } finally {
        this.isLoading = false;
      }
    },

    async selectProject(projectId: string) {
      this.isLoading = true;
      try {
        this.currentProject = this.projects.find((p) => p.project_id === projectId) || null;
        if (!this.currentProject) return;

        this.structure = await fetchStructure(projectId);
        const firstChap = this.chapters[0];
        if (firstChap) {
          this.activeChapterId = firstChap.unit_id;
          this.syncEditorContentForActiveChapter();
        }

        this.alerts = await fetchAlerts(projectId);
        this.storyMemory = await fetchStoryMemory(projectId);
      } finally {
        this.isLoading = false;
      }
    },

    syncEditorContentForActiveChapter() {
      const blocks = this.currentChapterBlocks;
      if (blocks.length > 0) {
        this.editorContent = blocks.map((b) => b.text).join("\n\n");
      } else {
        this.editorContent = "No content in this chapter yet.";
      }
    },

    setActiveChapter(chapterId: string) {
      this.activeChapterId = chapterId;
      this.syncEditorContentForActiveChapter();
    },

    selectAlert(alert: ContinuityAlert) {
      this.selectedAlert = alert;
      this.activeRightTab = "continuity";
    },

    jumpToEvidence(snippet: { anchor_id: string; chapter_id: string; block_id: string }) {
      if (snippet.chapter_id && snippet.chapter_id !== this.activeChapterId) {
        this.setActiveChapter(snippet.chapter_id);
      }
      this.highlightAnchorId = snippet.anchor_id;
    },

    async submitAuthorDecision(alertId: string, actionType: string, notes?: string) {
      if (!this.currentProject) return;
      await applyAuthorDecision(this.currentProject.project_id, alertId, actionType, notes);
      // Reload alerts
      this.alerts = await fetchAlerts(this.currentProject.project_id);
      if (this.selectedAlert && this.selectedAlert.alert_id === alertId) {
        this.selectedAlert = null;
      }
    },

    async triggerIndex(incremental = false) {
      if (!this.currentProject) return;
      this.isLoading = true;
      try {
        await indexProject(this.currentProject.project_id, incremental);
        this.storyMemory = await fetchStoryMemory(this.currentProject.project_id);
        this.alerts = await runContinuityCheck(this.currentProject.project_id);
      } finally {
        this.isLoading = false;
      }
    },
  },
});
