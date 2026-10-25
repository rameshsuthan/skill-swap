export type Goal = { skill_id: string; minimum_teacher_proficiency: number };
export type Profile = {
  id: string;
  display_name: string;
  city: string;
  country_code: string;
  timezone: string;
  offer: {
    skill_id: string;
    proficiency: number;
    description: string;
    styles: string[];
  };
  learning_goal: Goal;
};
export type LocalView = {
  member_id: string;
  timezone: string;
  start_local: string;
  end_local: string;
};
export type Session = {
  teacher_id: string;
  learner_id: string;
  skill_id: string;
  start_utc: string;
  end_utc: string;
  local_views: LocalView[];
};
export type Plan = {
  fingerprint: string;
  dataset_revision: number;
  goal: Goal;
  cycle: {
    member_ids: string[];
    edges: { teacher_id: string; learner_id: string; skill_id: string }[];
  };
  sessions: Session[];
  participant_timezones: Record<string, string>;
  evidence: string[];
  reviewer_summary: string;
};
export type Run = {
  run_id: string;
  member_id: string;
  parent_run_id: string | null;
  status: string;
  request: string;
  goal: Goal | null;
  plan: Plan | null;
  question: string | null;
  result: { id: string; status: string; plan: Plan } | null;
  message: string;
  error: string | null;
  model_calls: number;
  revisions: number;
  active_seconds: number;
};
export type Activity = {
  sequence: number;
  timestamp: string;
  agent: string;
  server: string;
  tool: string;
  status: string;
  duration_ms: number;
};
export type Providers = Record<
  string,
  { mode: string; model?: string; detail?: string }
>;
export type Context = {
  member: Profile;
  profiles: Profile[];
  catalog: Record<string, string>;
  dataset_revision: number;
};
