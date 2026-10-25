import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  ArrowRight,
  Globe2,
  RotateCcw,
  AlertCircle,
} from "lucide-react";
import type { Context, Run, Activity, Providers, MemoryState } from "./types";
import * as api from "./api";
import LearnerPanel from "./components/LearnerPanel";
import ExchangeGraph from "./components/ExchangeGraph";
import ProposalPanel from "./components/ProposalPanel";
import MemoryPanel from "./components/MemoryPanel";
import ActivityDrawer from "./components/ActivityDrawer";

const errorText: Record<string, string> = {
  provider_unavailable:
    "Gemini is unavailable or timed out. Your search is saved; try a new search when service recovers.",
  quota_limited:
    "Gemini quota is temporarily limited. Your search is saved. Try again after your quota resets.",
  provider_access_denied:
    "Gemini access was denied. Check the configured API key and model access.",
  execution_timeout:
    "This search reached its 90-second active limit. Start a fresh search to try again.",
  execution_error:
    "The search could not finish. Check the provider status and activity, then try again.",
  stopped: "This search reached its safety budget. Start a fresh search.",
  no_match:
    "No feasible reciprocal exchange for this request and availability. Try another skill or adjust your exclusions.",
  cancelled: "Proposal cancelled. Start a new search whenever you’re ready.",
};
export default function App() {
  const [member, setMember] = useState(
    localStorage.getItem("skillswap-member") || "maya",
  );
  const [context, setContext] = useState<Context | null>(null);
  const [request, setRequest] = useState(
    "I want to learn presentation design from a working-level teacher.",
  );
  const [exclusions, setExclusions] = useState<string[]>([]);
  const [runId, setRunId] = useState<string | null>(
    localStorage.getItem("skillswap-run"),
  );
  const [run, setRun] = useState<Run | null>(null);
  const [events, setEvents] = useState<Activity[]>([]);
  const [providers, setProviders] = useState<Providers>({});
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const seq = useRef(0);
  const updateMemoryProvider = useCallback(
    (provider: MemoryState["provider"]) => {
      setProviders((previous) => ({ ...previous, mem0: provider }));
    },
    [],
  );
  useEffect(() => {
    let current = true;
    api
      .getContext(member)
      .then((c) => {
        if (current) setContext(c);
      })
      .catch((e) => {
        if (current) setError(e.message);
      });
    localStorage.setItem("skillswap-member", member);
    return () => {
      current = false;
    };
  }, [member]);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    seq.current = 0;
    setEvents([]);
    async function poll() {
      try {
        const p = await api.getProviders();
        if (!active) return;
        setProviders(p);
        if (runId) {
          const [s, rows] = await Promise.all([
            api.getRun(runId),
            api.getEvents(runId, seq.current),
          ]);
          if (!active) return;
          setRun(s);
          if (rows.length) {
            seq.current = rows[rows.length - 1].sequence;
            setEvents((old) => [...old, ...rows]);
          }
          if (s.member_id !== member) setMember(s.member_id);
          if (s.status === "running") timer = setTimeout(poll, 1000);
        } else setRun(null);
      } catch (e) {
        if (active) setError((e as Error).message);
      }
    }
    poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [runId, pending]);
  const busy = pending || run?.status === "running";
  const locked =
    !!run &&
    ["awaiting_approval", "awaiting_clarification", "saved"].includes(
      run.status,
    );
  const act = async (fn: () => Promise<void>) => {
    setPending(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPending(false);
    }
  };
  const start = () =>
    act(async () => {
      const next = await api.startRun(member, request, exclusions, run?.run_id);
      setRun(null);
      setRunId(next.run_id);
      localStorage.setItem("skillswap-run", next.run_id);
    });
  const resume = (body: unknown) =>
    act(async () => {
      if (runId) setRun(await api.resumeRun(runId, body));
    });
  const reset = () =>
    act(async () => {
      if (
        runId &&
        ["awaiting_approval", "awaiting_clarification"].includes(
          run?.status || "",
        )
      )
        await api.resumeRun(runId, { decision: "cancel" });
      setRunId(null);
      setRun(null);
      setEvents([]);
      setExclusions([]);
      localStorage.removeItem("skillswap-run");
    });
  const current = context?.profiles.find((p) => p.id === member);
  return (
    <>
      <header className="topbar">
        <a className="brand" href="/" aria-label="SkillSwap home">
          <span className="brand-mark">
            <ArrowUpRight size={21} />
            <ArrowRight size={21} />
          </span>
          SkillSwap<span className="brand-period">.</span>
        </a>
        <nav aria-label="Main">
          <span className="nav-active">Exchange studio</span>
          <span className="nav-cohort">
            <Globe2 size={14} /> Global cohort
          </span>
        </nav>
        <div className="demo-badge">
          <i /> FICTIONAL COHORT DEMO
        </div>
      </header>
      <main>
        <div className="page-heading">
          <div>
            <div className="eyebrow green">
              GOOD THINGS HAPPEN WHEN KNOWLEDGE MOVES
            </div>
            <h1>What you know opens doors.</h1>
            <p>Trade a little of your expertise for a whole new perspective.</p>
          </div>
          <div className="cohort-stack">
            <div className="mini-faces">
              <span>M</span>
              <span>L</span>
              <span>N</span>
              <span>+12</span>
            </div>
            <span>Learning has no borders.</span>
          </div>
        </div>
        <div className="workspace-toolbar">
          <span>
            <i className="status-dot" />{" "}
            {run?.status === "saved"
              ? "Exchange saved"
              : busy
                ? "Specialists at work"
                : run?.status === "awaiting_approval"
                  ? "Ready for your review"
                  : "Your exchange workspace"}
          </span>
          <span>
            {run && (
              <button onClick={reset} disabled={busy}>
                <RotateCcw size={13} /> New search
              </button>
            )}
            <span className="week-label">OCT 26–30, 2026</span>
          </span>
        </div>
        {(error || (run && errorText[run.status])) && (
          <div className="error-banner" role="alert">
            <AlertCircle size={18} />
            <span>{error || errorText[run!.status]}</span>
          </div>
        )}
        <div className="workspace">
          <LearnerPanel
            context={context}
            member={member}
            setMember={(v) => {
              setMember(v);
              setExclusions([]);
            }}
            request={request}
            setRequest={setRequest}
            exclusions={exclusions}
            setExclusions={setExclusions}
            onStart={start}
            busy={!!busy}
            locked={locked}
          />
          <ExchangeGraph
            plan={run?.plan || null}
            profiles={context?.profiles || []}
            viewerZone={current?.timezone || "America/Chicago"}
            busy={!!busy}
          />
          <ProposalPanel
            run={run}
            profiles={context?.profiles || []}
            onRetry={() => resume({ decision: "retry" })}
            onApprove={() =>
              resume({
                decision: "approve",
                fingerprint: run?.plan?.fingerprint,
              })
            }
            onCancel={() => resume({ decision: "cancel" })}
            onAnswer={(answer) => resume({ answer })}
            pending={!!busy}
          />
        </div>
        <ActivityDrawer events={events} busy={!!busy} />
        <MemoryPanel
          key={member}
          member={member}
          name={current?.display_name || member}
          onProvider={updateMemoryProvider}
        />
        <div className="provider-strip">
          <span className="provider-caption">CONNECTED SERVICES</span>
          {["skillswap", "gemini", "mem0", "pinecone"].map((name) => (
            <span
              key={name}
              title={providers[name]?.detail}
              className={"provider " + (providers[name]?.mode || "disabled")}
            >
              <i />
              {name === "skillswap"
                ? "SkillSwap MCP"
                : name === "gemini"
                  ? providers.gemini?.model || "Gemini"
                  : name === "mem0"
                    ? "Mem0"
                    : "Pinecone"}
              <small>
                {providers[name]?.mode === "live"
                  ? "live"
                  : providers[name]?.mode === "test"
                    ? name === "gemini"
                      ? "test model"
                      : "test provider"
                    : providers[name]?.mode === "connecting"
                      ? "not verified"
                      : providers[name]?.mode || "offline"}
              </small>
            </span>
          ))}
        </div>
        <footer>
          <span>Made for shared curiosity.</span>
          <span>
            Remote sessions · Human approval · Nothing booked automatically
          </span>
        </footer>
      </main>
    </>
  );
}
