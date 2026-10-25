import type { Context, Run, Activity, Providers } from "./types";
async function request<T>(path: string, body?: unknown): Promise<T> {
  const result = await fetch("/api" + path, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!result.ok) {
    const data = await result
      .json()
      .catch(() => ({ detail: "Connection failed" }));
    throw new Error(data.detail || "Request failed");
  }
  return result.json();
}
export const getContext = (member: string) =>
  request<Context>("/context?member_id=" + encodeURIComponent(member));
export const startRun = (
  member_id: string,
  requestText: string,
  excluded_member_ids: string[],
  parent_run_id?: string,
) =>
  request<{ run_id: string }>("/runs", {
    member_id,
    request: requestText,
    excluded_member_ids,
    parent_run_id,
  });
export const getRun = (id: string) => request<Run>("/runs/" + id);
export const getEvents = (id: string, after = 0) =>
  request<Activity[]>("/runs/" + id + "/events?after=" + after);
export const resumeRun = (id: string, body: unknown) =>
  request<Run>("/runs/" + id + "/resume", body);
export const getProviders = () => request<Providers>("/providers");
export const downloadProposal = (id: string, member: string) =>
  "/api/proposals/" + id + "/export?member_id=" + encodeURIComponent(member);

export const getMemories = (member: string) =>
  request<import("./types").MemoryState>(
    "/memories?member_id=" + encodeURIComponent(member),
  );
export const remember = (member_id: string, text: string) =>
  request<import("./types").MemoryWrite>("/memories", { member_id, text });
export const editMemory = (member_id: string, id: string, text: string) =>
  request<import("./types").MemoryWrite>(
    "/memories/" + encodeURIComponent(id) + "/update",
    { member_id, text },
  );
export const forgetMemory = (member_id: string, id: string) =>
  request<import("./types").MemoryWrite>(
    "/memories/" + encodeURIComponent(id) + "/forget",
    { member_id },
  );
export const checkMemory = (member_id: string, id: string) =>
  request<import("./types").MemoryWrite>(
    "/memory-operations/" + encodeURIComponent(id) + "/check",
    { member_id },
  );

export const acknowledgeMemory = (member_id: string, id: string) =>
  request<import("./types").MemoryWrite>(
    "/memory-operations/" + encodeURIComponent(id) + "/acknowledge",
    { member_id },
  );
