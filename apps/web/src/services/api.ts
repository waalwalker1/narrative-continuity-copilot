export interface ManuscriptProject {
  project_id: string;
  title: string;
  created_at: string;
  active_revision_id?: string;
  language: string;
  genre_hint?: string;
  privacy_mode: "LOCAL_ONLY" | "MINIMAL_CLOUD_CONTEXT";
}

export interface StructuralUnit {
  unit_id: string;
  project_id: string;
  revision_id: string;
  unit_type: "book" | "part" | "chapter" | "scene" | "block";
  parent_id?: string;
  ordinal: number;
  title?: string;
  text: string;
  word_count: number;
}

export interface EvidenceSnippet {
  anchor_id: string;
  chapter_id: string;
  chapter_title?: string;
  scene_id?: string;
  block_id: string;
  char_start: number;
  char_end: number;
  text_snippet: string;
  revision_id: string;
}

export interface ContinuityAlert {
  alert_id: string;
  project_id: string;
  revision_id: string;
  conflict_class: string;
  confidence: number;
  confidence_category: "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL";
  explanation: string;
  alternate_interpretations: string[];
  evidence_a: EvidenceSnippet;
  evidence_b: EvidenceSnippet;
  chapter_location?: string;
  requires_author_review: boolean;
  canonical_status: string;
  suppressed: boolean;
}

export interface Entity {
  entity_id: string;
  project_id: string;
  canonical_name: string;
  entity_type: string;
  aliases: string[];
  description?: string;
  canonical_status: string;
  evidence_anchor_ids: string[];
}

export interface FactAssertion {
  fact_id: string;
  project_id: string;
  revision_id: string;
  subject_entity_id: string;
  predicate: string;
  value?: string;
  narrative_scope: string;
  epistemic_status: string;
  canonical_status: string;
  confidence: number;
  evidence_anchor_ids: string[];
}

export interface StoryMemory {
  project_id: string;
  revision_id: string;
  entities: Entity[];
  facts: FactAssertion[];
  relations: any[];
  timeline_events: any[];
  world_rules: any[];
  story_threads: any[];
}

const API_BASE = "";

export async function fetchProjects(): Promise<ManuscriptProject[]> {
  const res = await fetch(`${API_BASE}/api/v1/projects`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function createProject(title: string): Promise<ManuscriptProject> {
  const res = await fetch(`${API_BASE}/api/v1/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, language: "en", privacy_mode: "LOCAL_ONLY" }),
  });
  if (!res.ok) throw new Error("Failed to create project");
  return res.json();
}

export async function importManuscript(projectId: string, contentText: string, format = "markdown"): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format, content_text: contentText }),
  });
  if (!res.ok) throw new Error("Failed to import manuscript");
  return res.json();
}

export async function fetchStructure(projectId: string): Promise<StructuralUnit[]> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/structure`);
  if (!res.ok) throw new Error("Failed to fetch structure");
  return res.json();
}

export async function indexProject(projectId: string, incremental = false): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ incremental }),
  });
  if (!res.ok) throw new Error("Failed to index project");
  return res.json();
}

export async function fetchStoryMemory(projectId: string): Promise<StoryMemory> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/memory`);
  if (!res.ok) throw new Error("Failed to fetch story memory");
  return res.json();
}

export async function runContinuityCheck(projectId: string): Promise<ContinuityAlert[]> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/continuity/check`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to run continuity check");
  return res.json();
}

export async function fetchAlerts(projectId: string): Promise<ContinuityAlert[]> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/continuity/alerts`);
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

export async function applyAuthorDecision(
  projectId: string,
  alertId: string,
  actionType: string,
  notes?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/continuity/alerts/${alertId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action_type: actionType, author_notes: notes }),
  });
  if (!res.ok) throw new Error("Failed to apply author decision");
  return res.json();
}

export async function createRevision(projectId: string, markdown: string): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/revisions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content_markdown: markdown }),
  });
  if (!res.ok) throw new Error("Failed to create revision");
  return res.json();
}

export async function createRevisionFromScopedEdits(
  projectId: string,
  chapterId: string,
  chapterContentMarkdown: string,
  baseRevisionId?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/v1/projects/${projectId}/revisions/from-edits`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chapter_id: chapterId,
      chapter_content_markdown: chapterContentMarkdown,
      base_revision_id: baseRevisionId,
    }),
  });
  if (!res.ok) throw new Error("Failed to create scoped revision from edits");
  return res.json();
}
