import { useEffect, useRef, useState } from "react";
import { Bookmark, Pencil, RefreshCw, Trash2 } from "lucide-react";
import * as api from "../api";
import type { MemoryState, MemoryWrite } from "../types";

export default function MemoryPanel({
  member,
  name,
  onProvider,
}: {
  member: string;
  name: string;
  onProvider: (provider: MemoryState["provider"]) => void;
}) {
  const [data, setData] = useState<MemoryState | null>(null);
  const [text, setText] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const alive = useRef(true);
  const sequence = useRef(0);
  async function refresh() {
    const seq = ++sequence.current;
    const next = await api.getMemories(member);
    if (!alive.current || seq !== sequence.current) return;
    setData(next);
    onProvider(next.provider);
  }
  useEffect(() => {
    alive.current = true;
    refresh().catch(() => {
      if (alive.current)
        setError("Preferences could not be loaded. Try refreshing.");
    });
    return () => {
      alive.current = false;
    };
  }, [member]);
  async function act(action: () => Promise<MemoryWrite | void>) {
    setBusy(true);
    setError("");
    try {
      const result = await action();
      if (!alive.current) return;
      if (result?.status === "saved") {
        setText("");
        setEditing(null);
      }
      await refresh();
    } catch {
      if (alive.current)
        setError(
          "This change could not be confirmed. Refresh preferences before trying again.",
        );
    } finally {
      if (alive.current) setBusy(false);
    }
  }
  const pending =
    data?.operations.filter((op) => op.status === "pending") || [];
  const disabled =
    busy ||
    !data ||
    data.provider.mode === "disabled" ||
    pending.some((op) => !op.acknowledged);
  return (
    <section className="memory-panel" aria-labelledby="memory-title">
      <div className="memory-intro">
        <div className="eyebrow green">
          <Bookmark size={13} /> MADE PERSONAL
        </div>
        <h2 id="memory-title">Learning preferences</h2>
        <p>
          Remember how {name} likes to learn. Preferences guide future searches;
          availability and exclusions still decide what works.
        </p>
        <span className={"provider " + (data?.provider.mode || "connecting")}>
          <i /> Mem0 <small>{data?.provider.mode || "connecting"}</small>
        </span>
        <p className="memory-note">
          {data?.provider.detail || "Loading preferences…"}
        </p>
      </div>
      <div className="memory-controls">
        <div className="memory-list-heading">
          <span>REMEMBERED FOR {name.toUpperCase()}</span>
          <button
            aria-label="Refresh preferences"
            disabled={busy}
            onClick={() => act(refresh)}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
        {!!error && (
          <p role="alert" className="memory-error">
            {error}
          </p>
        )}
        {data?.memories.map((fact) => (
          <div className="memory-fact" key={fact.id}>
            <span>{fact.text}</span>
            <button
              aria-label={"Edit preference: " + fact.text}
              disabled={disabled}
              onClick={() => {
                setEditing(fact.id);
                setText(fact.text);
              }}
            >
              <Pencil size={14} />
            </button>
            <button
              aria-label={"Forget preference: " + fact.text}
              disabled={disabled}
              onClick={() => act(() => api.forgetMemory(member, fact.id))}
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
        {data &&
          ["live", "test"].includes(data.provider.mode) &&
          !data.memories.length && (
            <p className="memory-empty">No preferences remembered yet.</p>
          )}
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (!disabled && text.trim())
              act(() =>
                editing
                  ? api.editMemory(member, editing, text.trim())
                  : api.remember(member, text.trim()),
              );
          }}
        >
          <label htmlFor="memory-text">
            {editing
              ? "Edit learning preference"
              : "A preference for future searches"}
          </label>
          <textarea
            id="memory-text"
            rows={2}
            maxLength={1000}
            placeholder="For example, I prefer discussion-based teaching."
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={disabled}
          />
          <div className="memory-actions">
            <small>Saved only when you choose to remember.</small>
            {editing && (
              <button
                type="button"
                disabled={busy}
                onClick={() => {
                  setEditing(null);
                  setText("");
                }}
              >
                Cancel edit
              </button>
            )}
            <button className="memory-save" disabled={disabled || !text.trim()}>
              {busy ? "Checking…" : editing ? "Save preference" : "Remember"}
            </button>
          </div>
        </form>
        {pending.map((op) => (
          <div className="memory-pending" role="status" key={op.operation_id}>
            <span>
              {op.acknowledged ? "Unconfirmed" : "Pending"} · {op.detail}
            </span>
            <button
              disabled={busy}
              onClick={() =>
                act(() => api.checkMemory(member, op.operation_id))
              }
            >
              Check pending change
            </button>
            {!op.acknowledged && (
              <button
                disabled={busy}
                onClick={() =>
                  act(() => api.acknowledgeMemory(member, op.operation_id))
                }
              >
                Continue without confirmation
              </button>
            )}
          </div>
        ))}
        {!pending.length && data?.operations[0] && (
          <p
            className={"memory-result " + data.operations[0].status}
            role="status"
          >
            {data.operations[0].detail}
          </p>
        )}
      </div>
    </section>
  );
}
