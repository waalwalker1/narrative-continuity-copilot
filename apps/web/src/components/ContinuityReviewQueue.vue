<template>
  <div class="flex flex-col h-full overflow-y-auto p-4 space-y-4">
    <div class="flex items-center justify-between">
      <div class="text-sm font-semibold text-stone-800">
        Continuity Alerts ({{ store.unresolvedAlerts.length }})
      </div>
      <span class="text-xs text-stone-500">
        Author Action Required
      </span>
    </div>

    <div v-if="store.unresolvedAlerts.length === 0" class="text-xs text-stone-500 py-6 text-center border border-dashed rounded-lg">
      No continuity issues detected in current manuscript revision.
    </div>

    <div
      v-for="alert in store.unresolvedAlerts"
      :key="alert.alert_id"
      :class="[
        'p-4 rounded-lg border text-sm transition-all',
        store.selectedAlert?.alert_id === alert.alert_id
          ? 'border-amber-500 bg-amber-50/40 shadow-sm'
          : 'border-stone-200 bg-white hover:border-stone-300'
      ]"
    >
      <!-- Alert Header -->
      <div class="flex items-start justify-between mb-2">
        <span class="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 tracking-wide">
          {{ alert.conflict_class.replace(/_/g, ' ') }}
        </span>
        <span class="text-xs font-mono text-stone-400">
          {{ Math.round(alert.confidence * 100) }}% confidence
        </span>
      </div>

      <!-- Explanation -->
      <p class="text-stone-700 mb-3 text-xs leading-relaxed font-sans">
        {{ alert.explanation }}
      </p>

      <!-- Evidence Comparison -->
      <div class="space-y-2 mb-3 bg-stone-50 p-2.5 rounded border border-stone-100 text-xs">
        <div class="cursor-pointer group" @click="store.jumpToEvidence(alert.evidence_a)">
          <div class="text-[11px] font-semibold text-amber-700 flex items-center justify-between">
            <span>Earlier Evidence ({{ alert.evidence_a.chapter_title || 'Chapter' }})</span>
            <span class="text-[10px] text-stone-400 group-hover:text-stone-600">Jump to text &rarr;</span>
          </div>
          <p class="text-stone-600 italic mt-0.5 group-hover:text-stone-900">
            "{{ alert.evidence_a.text_snippet }}"
          </p>
        </div>

        <div class="border-t border-stone-200 pt-2 cursor-pointer group" @click="store.jumpToEvidence(alert.evidence_b)">
          <div class="text-[11px] font-semibold text-red-700 flex items-center justify-between">
            <span>Later Conflict ({{ alert.evidence_b.chapter_title || 'Chapter' }})</span>
            <span class="text-[10px] text-stone-400 group-hover:text-stone-600">Jump to text &rarr;</span>
          </div>
          <p class="text-stone-600 italic mt-0.5 group-hover:text-stone-900">
            "{{ alert.evidence_b.text_snippet }}"
          </p>
        </div>
      </div>

      <!-- Author Action Buttons -->
      <div class="grid grid-cols-2 gap-1.5 pt-1 border-t border-stone-100 text-xs">
        <button
          @click="store.submitAuthorDecision(alert.alert_id, 'MARK_INTENTIONAL')"
          class="px-2 py-1.5 rounded bg-amber-100 hover:bg-amber-200 text-amber-900 font-medium transition-colors text-center"
        >
          Mark Intentional
        </button>
        <button
          @click="store.submitAuthorDecision(alert.alert_id, 'RESOLVE_WITH_CURRENT_FACT')"
          class="px-2 py-1.5 rounded bg-emerald-100 hover:bg-emerald-200 text-emerald-900 font-medium transition-colors text-center"
        >
          Resolve / Keep Current
        </button>
        <button
          @click="store.submitAuthorDecision(alert.alert_id, 'MARK_POV_BELIEF')"
          class="px-2 py-1.5 rounded bg-stone-100 hover:bg-stone-200 text-stone-700 transition-colors text-center"
        >
          Mark POV Belief
        </button>
        <button
          @click="store.submitAuthorDecision(alert.alert_id, 'IGNORE_ALERT')"
          class="px-2 py-1.5 rounded bg-stone-100 hover:bg-stone-200 text-stone-600 transition-colors text-center"
        >
          Ignore Alert
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useManuscriptStore } from "@/stores/manuscript";

const store = useManuscriptStore();
</script>
