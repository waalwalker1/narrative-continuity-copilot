<template>
  <div class="flex-1 flex flex-col h-full bg-white relative">
    <!-- Editor Header -->
    <div class="h-12 border-b border-stone-200 px-6 flex items-center justify-between bg-stone-50">
      <div class="text-sm font-medium text-stone-700">
        {{ currentChapterTitle }}
      </div>
      <div class="flex items-center space-x-3 text-xs text-stone-500">
        <span>Word Count: {{ wordCount }}</span>
        <button
          @click="saveRevision"
          class="px-2.5 py-1 bg-stone-800 text-stone-100 hover:bg-stone-700 rounded transition-colors"
        >
          Save Revision
        </button>
      </div>
    </div>

    <!-- Quill Editor Container -->
    <div class="flex-1 overflow-y-auto p-8 max-w-4xl mx-auto w-full">
      <div ref="editorRef" class="min-h-[600px]"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from "vue";
import Quill from "quill";
import { useManuscriptStore } from "@/stores/manuscript";
import { createRevision, createRevisionFromScopedEdits } from "@/services/api";

const store = useManuscriptStore();
const editorRef = ref<HTMLElement | null>(null);
let quillInstance: Quill | null = null;

const currentChapterTitle = computed(() => {
  const chap = store.chapters.find((c) => c.unit_id === store.activeChapterId);
  return chap?.title || "Chapter Editor";
});

const wordCount = ref(0);

onMounted(() => {
  if (editorRef.value) {
    quillInstance = new Quill(editorRef.value, {
      theme: "snow",
      modules: {
        toolbar: [
          [{ header: [1, 2, 3, false] }],
          ["bold", "italic", "underline", "strike"],
          ["blockquote"],
          [{ list: "ordered" }, { list: "bullet" }],
          ["clean"],
        ],
      },
    });

    quillInstance.root.innerHTML = store.editorContent;

    quillInstance.on("text-change", () => {
      const text = quillInstance?.getText() || "";
      const words = text.trim().split(/\s+/).filter(Boolean);
      wordCount.value = words.length;
    });
  }
});

watch(
  () => store.editorContent,
  (newContent) => {
    if (quillInstance && quillInstance.root.innerHTML !== newContent) {
      quillInstance.root.innerHTML = newContent;
      const text = quillInstance.getText() || "";
      wordCount.value = text.trim().split(/\s+/).filter(Boolean).length;
    }
  }
);

async function saveRevision() {
  if (!store.currentProject || !quillInstance) return;
  const content = quillInstance.getText();
  if (store.activeChapterId) {
    await createRevisionFromScopedEdits(
      store.currentProject.project_id,
      store.activeChapterId,
      content,
      store.currentProject.active_revision_id
    );
  } else {
    await createRevision(store.currentProject.project_id, content);
  }
  await store.triggerIndex();
}
</script>
