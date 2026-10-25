import type { LocalView } from "./types";
// Format the wall-clock portion of server-derived ISO values, never the browser's zone.
export function wall(iso: string) {
  const [date, time] = iso.split("T");
  const d = new Date(date + "T12:00:00Z");
  return {
    date: new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      timeZone: "UTC",
    }).format(d),
    time: time.slice(0, 5),
    offset: "UTC" + iso.slice(-6).replace("-", "−"),
  };
}
export function localInterval(view: LocalView) {
  const a = wall(view.start_local),
    b = wall(view.end_local);
  return (
    a.date +
    " · " +
    a.time +
    "–" +
    (a.date !== b.date ? b.date + " " : "") +
    b.time
  );
}
export function dayBadge(view: LocalView, utcStart: string) {
  const delta = Math.round(
    (Date.parse(view.start_local.slice(0, 10) + "T00:00Z") -
      Date.parse(utcStart.slice(0, 10) + "T00:00Z")) /
      86400000,
  );
  return delta > 0 ? "Next day" : delta < 0 ? "Previous day" : null;
}
export function viewerTime(utc: string, timezone: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: timezone,
  }).format(new Date(utc));
}
