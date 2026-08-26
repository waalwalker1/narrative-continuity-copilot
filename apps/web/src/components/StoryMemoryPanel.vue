<template>
  <div class="flex flex-col h-full overflow-y-auto p-4 space-y-4">
    <div class="text-sm font-semibold text-stone-800">
      Story Memory & Lore
    </div>

    <!-- Entities / Characters -->
    <div class="space-y-2">
      <div class="text-xs font-semibold text-stone-500 uppercase tracking-wider">
        Characters & Entities ({{ store.storyMemory?.entities.length || 0 }})
      </div>
      <div
        v-for="ent in store.storyMemory?.entities || []"
        :key="ent.entity_id"
        class="p-3 bg-white border border-stone-200 rounded-lg text-xs space-y-1"
      >
        <div class="flex items-center justify-between">
          <span class="font-bold text-stone-800">{{ ent.canonical_name }}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-stone-100 text-stone-600 uppercase font-mono">
            {{ ent.entity_type }}
          </span>
        </div>
        <div v-if="ent.aliases.length > 0" class="text-stone-500 text-[11px]">
          Aliases: {{ ent.aliases.join(", ") }}
        </div>
      </div>
    </div>

    <!-- Facts -->
    <div class="space-y-2 pt-2 border-t border-stone-200">
      <div class="text-xs font-semibold text-stone-500 uppercase tracking-wider">
        Extracted Facts ({{ store.storyMemory?.facts.length || 0 }})
      </div>
      <div
        v-for="fact in store.storyMemory?.facts || []"
        :key="fact.fact_id"
        class="p-2.5 bg-stone-50 border border-stone-100 rounded text-xs text-stone-700"
      >
        <div class="font-medium text-stone-900 mb-0.5">
          {{ fact.predicate }}: <span class="text-amber-700 font-semibold">{{ fact.value }}</span>
        </div>
        <div class="flex items-center space-x-2 text-[10px] text-stone-400">
          <span>Scope: {{ fact.narrative_scope }}</span>
          <span>&bull;</span>
          <span>Status: {{ fact.epistemic_status }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useManuscriptStore } from "@/stores/manuscript";

const store = useManuscriptStore();
</script>
