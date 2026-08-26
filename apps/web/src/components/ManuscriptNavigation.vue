<template>
  <nav class="w-64 bg-stone-900 text-stone-200 flex flex-col h-full border-r border-stone-800 select-none">
    <div class="p-4 border-b border-stone-800 flex items-center justify-between">
      <div class="font-semibold text-sm tracking-wide uppercase text-stone-400">
        Manuscript
      </div>
      <span class="text-xs px-2 py-0.5 rounded bg-stone-800 text-stone-300 font-mono">
        v{{ store.currentProject?.active_revision_id ? '1' : '0' }}
      </span>
    </div>

    <div class="p-3">
      <div class="text-xs font-medium text-stone-400 mb-2 px-2">Projects</div>
      <select
        :value="store.currentProject?.project_id"
        @change="onSelectProject"
        class="w-full bg-stone-800 text-stone-200 text-sm rounded px-2.5 py-1.5 border border-stone-700 focus:outline-none focus:border-amber-500"
      >
        <option v-for="p in store.projects" :key="p.project_id" :value="p.project_id">
          {{ p.title }}
        </option>
      </select>
    </div>

    <div class="flex-1 overflow-y-auto p-2 space-y-1">
      <div class="text-xs font-medium text-stone-400 mb-1 px-2">Chapters</div>
      <div v-if="store.chapters.length === 0" class="text-xs text-stone-500 px-2 py-3">
        No chapters found. Import a manuscript to begin.
      </div>
      <button
        v-for="chap in store.chapters"
        :key="chap.unit_id"
        @click="store.setActiveChapter(chap.unit_id)"
        :class="[
          'w-full text-left px-3 py-2 rounded text-sm transition-colors flex items-center justify-between',
          store.activeChapterId === chap.unit_id
            ? 'bg-amber-600/20 text-amber-300 font-medium border-l-2 border-amber-500'
            : 'text-stone-300 hover:bg-stone-800 hover:text-stone-100'
        ]"
      >
        <span class="truncate">{{ chap.title || `Chapter ${chap.ordinal}` }}</span>
        <span class="text-xs text-stone-500 font-mono">{{ chap.word_count || '' }}</span>
      </button>
    </div>

    <div class="p-3 border-t border-stone-800">
      <button
        @click="store.triggerIndex"
        :disabled="store.isLoading"
        class="w-full bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-medium text-xs py-2 px-3 rounded transition-colors flex items-center justify-center space-x-2"
      >
        <span>{{ store.isLoading ? 'Indexing...' : 'Index & Verify' }}</span>
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useManuscriptStore } from "@/stores/manuscript";

const store = useManuscriptStore();

function onSelectProject(e: Event) {
  const target = e.target as HTMLSelectElement;
  if (target.value) {
    store.selectProject(target.value);
  }
}
</script>
