<template>
  <div class="flex flex-col h-screen w-screen bg-stone-100 overflow-hidden">
    <!-- Top Navigation Header -->
    <header class="h-14 bg-stone-900 text-stone-100 px-6 flex items-center justify-between border-b border-stone-800 shrink-0">
      <div class="flex items-center space-x-3">
        <span class="text-amber-500 font-black text-lg tracking-tight">✦ Narrative Copilot</span>
        <span class="text-xs px-2 py-0.5 rounded bg-stone-800 text-stone-300 font-medium">
          {{ store.currentProject?.title || 'No Project' }}
        </span>
      </div>
      <div class="flex items-center space-x-4 text-xs">
        <span class="flex items-center space-x-1.5 text-stone-400">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          <span>Privacy: Local Only (0 Cloud Transmissions)</span>
        </span>
      </div>
    </header>

    <!-- Main Workspace -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left: Book & Chapter Structure Navigation -->
      <ManuscriptNavigation />

      <!-- Center: Quill Manuscript Editor -->
      <QuillEditor />

      <!-- Right: Review & Lore Panel -->
      <aside class="w-96 bg-stone-50 border-l border-stone-200 flex flex-col h-full shrink-0">
        <!-- Tab Navigation -->
        <div class="flex border-b border-stone-200 bg-stone-100 text-xs font-medium text-stone-600">
          <button
            @click="store.activeRightTab = 'continuity'"
            :class="[
              'flex-1 py-3 text-center transition-colors border-b-2',
              store.activeRightTab === 'continuity'
                ? 'border-amber-600 text-stone-900 bg-white font-semibold'
                : 'border-transparent hover:text-stone-900'
            ]"
          >
            Continuity ({{ store.unresolvedAlerts.length }})
          </button>
          <button
            @click="store.activeRightTab = 'memory'"
            :class="[
              'flex-1 py-3 text-center transition-colors border-b-2',
              store.activeRightTab === 'memory'
                ? 'border-amber-600 text-stone-900 bg-white font-semibold'
                : 'border-transparent hover:text-stone-900'
            ]"
          >
            Story Memory
          </button>
        </div>

        <!-- Tab Content -->
        <div class="flex-1 overflow-hidden">
          <ContinuityReviewQueue v-if="store.activeRightTab === 'continuity'" />
          <StoryMemoryPanel v-else-if="store.activeRightTab === 'memory'" />
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useManuscriptStore } from "@/stores/manuscript";
import ManuscriptNavigation from "@/components/ManuscriptNavigation.vue";
import QuillEditor from "@/components/QuillEditor.vue";
import ContinuityReviewQueue from "@/components/ContinuityReviewQueue.vue";
import StoryMemoryPanel from "@/components/StoryMemoryPanel.vue";

const store = useManuscriptStore();

onMounted(async () => {
  await store.loadProjects();
});
</script>
