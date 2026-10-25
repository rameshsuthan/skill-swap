import {
  ShieldCheck,
  Clock3,
  ArrowRight,
  Download,
  Check,
  CalendarDays,
} from "lucide-react";
import type { Run, Profile } from "../types";
import { skill } from "./LearnerPanel";
import { localInterval, wall, dayBadge } from "../time";
import { downloadProposal } from "../api";
export default function ProposalPanel({
  run,
  profiles,
  onApprove,
  onRetry,
  onCancel,
  onAnswer,
  pending,
}: {
  run: Run | null;
  profiles: Profile[];
  onApprove: () => void;
  onRetry: () => void;
  onCancel: () => void;
  onAnswer: (answer: string) => void;
  pending: boolean;
}) {
  const plan = run?.plan;
  const name = (id: string) =>
    profiles.find((p) => p.id === id)?.display_name || id;
  return (
    <aside className="proposal-panel">
      <div className="eyebrow">
        <span className="step-dot">3</span> YOUR PROPOSAL
      </div>
      <div className="proposal-heading">
        <h2>
          {run?.status === "saved"
            ? "Proposal saved"
            : plan
              ? "A plan worth sharing."
              : "Make it a plan."}
        </h2>
        <ShieldCheck size={22} />
      </div>
      {run?.status === "awaiting_clarification" && (
        <div className="clarify">
          <strong>One quick question</strong>
          <p>{run.question}</p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const data = new FormData(e.currentTarget);
              onAnswer(String(data.get("answer")));
            }}
          >
            <label className="sr-only" htmlFor="answer">
              Your answer
            </label>
            <input
              id="answer"
              name="answer"
              required
              placeholder="Tell us a little more…"
            />
            <button className="primary full" disabled={pending}>
              Continue
              <ArrowRight size={15} />
            </button>
          </form>
          <button className="text-button" onClick={onCancel}>
            Cancel search
          </button>
        </div>
      )}
      {plan ? (
        <>
          <div
            className={
              "review-banner " + (run?.status === "saved" ? "saved" : "")
            }
          >
            <ShieldCheck size={18} />
            <div>
              <strong>
                {run?.status === "saved"
                  ? "Awaiting participant confirmation"
                  : "Checked & ready for your review"}
              </strong>
              <span>
                {run?.status === "saved"
                  ? "Saved safely. Nobody has been booked or contacted."
                  : `${plan.sessions.length} sessions · ${plan.sessions.length * 30} minutes of shared learning`}
              </span>
            </div>
          </div>
          {run && run.revisions > 0 && run.status === "awaiting_approval" && (
            <div className="notice">
              Availability changed. Please review again.
            </div>
          )}
          {run?.status === "save_error" && (
            <div className="notice">
              The save outcome is uncertain. Recover the existing proposal
              before starting another.
              <button className="primary" disabled={pending} onClick={onRetry}>
                Recover save
              </button>
            </div>
          )}
          <div className="session-list">
            {plan.sessions.map((s, i) => (
              <article
                className="session-card"
                key={i}
                tabIndex={0}
                aria-label={`${name(s.teacher_id)} teaches ${name(s.learner_id)} ${skill(s.skill_id)}`}
              >
                <div className="session-top">
                  <span className="session-index">SESSION 0{i + 1}</span>
                  <span>
                    <Clock3 size={12} /> 30 min
                  </span>
                </div>
                <h3>{skill(s.skill_id)}</h3>
                <p className="direction">
                  {name(s.teacher_id)} → {name(s.learner_id)}
                </p>
                <div className="local-times">
                  {s.local_views.map((v) => (
                    <div key={v.member_id}>
                      <div>
                        <b>{name(v.member_id)}</b>
                        {dayBadge(v, s.start_utc) && (
                          <em>{dayBadge(v, s.start_utc)}</em>
                        )}
                        {v.start_local.slice(0, 10) !==
                          v.end_local.slice(0, 10) && <em>Next day</em>}
                      </div>
                      <strong>{localInterval(v)}</strong>
                      <small>
                        {v.timezone} · {wall(v.start_local).offset}
                      </small>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
          <details className="evidence">
            <summary>
              <Check size={14} /> Why this works
            </summary>
            <p>{plan.reviewer_summary}</p>
            {plan.evidence.map((e, i) => (
              <p key={i}>{e}</p>
            ))}
            <small>
              Self-declared proficiency · dataset revision{" "}
              {plan.dataset_revision}
            </small>
          </details>
          {run?.status === "saved" && run.result ? (
            <a
              className="primary full download"
              href={downloadProposal(run.result.id, run.member_id)}
              download
            >
              <Download size={16} /> Download proposal
            </a>
          ) : (
            <>
              <button
                className="primary full"
                onClick={onApprove}
                disabled={pending || run?.status !== "awaiting_approval"}
              >
                <Check size={16} /> Approve & save proposal
              </button>
              <button
                className="text-button full"
                onClick={onCancel}
                disabled={pending || run?.status !== "awaiting_approval"}
              >
                Cancel proposal
              </button>
            </>
          )}
          <p className="approval-note">
            Your approval saves this exact proposal. Participants still need to
            confirm; these times are not reserved.
          </p>
        </>
      ) : (
        run?.status !== "awaiting_clarification" && (
          <div className="proposal-empty">
            <CalendarDays size={30} strokeWidth={1.3} />
            <h3>Your schedule will land here.</h3>
            <p>
              Review every session in both participants’ local time before you
              decide.
            </p>
            <div className="empty-checks">
              <span>
                <Check size={14} /> Skills that fit
              </span>
              <span>
                <Check size={14} /> Times that work
              </span>
              <span>
                <Check size={14} /> Your final say
              </span>
            </div>
          </div>
        )
      )}
    </aside>
  );
}
