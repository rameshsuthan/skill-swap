import {
  ArrowUpRight,
  ArrowRight,
  Globe2,
  GraduationCap,
  Sparkles,
} from "lucide-react";
import type { Profile, Context } from "../types";
export const skill = (s: string) =>
  s === "sql"
    ? "SQL"
    : s.replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
export function Avatar({
  profile,
  large = false,
}: {
  profile: Profile;
  large?: boolean;
}) {
  return (
    <span
      className={
        "avatar avatar-" +
        (profile.id.charCodeAt(0) % 5) +
        (large ? " large" : "")
      }
    >
      {profile.display_name.slice(0, 1)}
    </span>
  );
}
export default function LearnerPanel({
  context,
  member,
  setMember,
  request,
  setRequest,
  onStart,
  busy,
  locked,
  exclusions,
  setExclusions,
}: {
  context: Context | null;
  member: string;
  setMember: (v: string) => void;
  request: string;
  setRequest: (v: string) => void;
  onStart: () => void;
  busy: boolean;
  locked: boolean;
  exclusions: string[];
  setExclusions: (v: string[]) => void;
}) {
  const p = context?.profiles.find((p) => p.id === member);
  return (
    <aside className="learner-panel">
      <div className="eyebrow">
        <span className="step-dot">1</span> YOUR STARTING POINT
      </div>
      <h2>
        A little give.
        <br />A lot to learn.
      </h2>
      <p className="muted intro">
        Bring a skill. Find your people.
        <br />
        Make room for something new.
      </p>
      <label className="label" htmlFor="learner">
        Learner <span>Fictional cohort</span>
      </label>
      <select
        id="learner"
        value={member}
        onChange={(e) => setMember(e.target.value)}
        disabled={busy || locked}
      >
        {context?.profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.display_name} · {p.city}
          </option>
        ))}
      </select>
      {p && (
        <div className="profile-card">
          <div className="profile-heading">
            <Avatar profile={p} large />
            <div>
              <strong>{p.display_name}</strong>
              <span>
                {p.city}, {p.country_code}
              </span>
            </div>
            <span className="you-badge">YOU</span>
          </div>
          <div className="timezone">
            <Globe2 size={13} />
            {p.timezone}
          </div>
          <div className="offer-row">
            <ArrowUpRight size={17} />
            <div>
              <span>I can share</span>
              <strong>{skill(p.offer.skill_id)}</strong>
            </div>
            <span className="level">
              {["", "Basic", "Working", "Advanced"][p.offer.proficiency]}
            </span>
          </div>
        </div>
      )}
      <label className="label" htmlFor="goal">
        What would you like to learn?
      </label>
      <textarea
        id="goal"
        value={request}
        onChange={(e) => setRequest(e.target.value)}
        rows={4}
        maxLength={2000}
        disabled={busy}
        placeholder="A skill, a project, or something you're curious about…"
      />
      <div className="suggestions">
        <button
          disabled={busy}
          onClick={() =>
            setRequest(
              "I want to learn presentation design from a working-level teacher.",
            )
          }
        >
          Presentation design
        </button>
        <button
          disabled={busy}
          onClick={() => setRequest("I want to learn SQL.")}
        >
          SQL
        </button>
      </div>
      <details className="preferences">
        <summary>
          People to exclude this time{" "}
          <span>{exclusions.length || "Optional"}</span>
        </summary>
        <div className="exclude-list">
          {context?.profiles
            .filter((p) => p.id !== member)
            .map((p) => (
              <label key={p.id}>
                <input
                  type="checkbox"
                  checked={exclusions.includes(p.id)}
                  disabled={busy}
                  onChange={(e) =>
                    setExclusions(
                      e.target.checked
                        ? [...exclusions, p.id]
                        : exclusions.filter((i) => i !== p.id),
                    )
                  }
                />
                {p.display_name}
              </label>
            ))}
        </div>
      </details>
      <button
        className="primary full"
        onClick={onStart}
        disabled={busy || !request.trim() || !context}
      >
        {busy ? (
          <>
            <span className="spinner" /> Exploring your exchange
          </>
        ) : (
          <>
            {locked ? "Revise my exchange" : "Find my exchange"}
            <ArrowRight size={17} />
          </>
        )}
      </button>
      <p className="micro">
        <Sparkles size={12} /> Three specialists. One thoughtful proposal.
      </p>
      <div className="cohort-note">
        <GraduationCap size={21} />
        <div>
          <strong>Better, together.</strong>
          <p>
            15 learners · 15 cities · one global community. Every exchange gives
            something back.
          </p>
        </div>
      </div>
    </aside>
  );
}
