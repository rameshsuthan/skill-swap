import { test, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
const root = process.cwd().replace(/\/frontend$/, "");
function scenario(name: string) {
  execFileSync(
    root + "/.venv/bin/python",
    [root + "/scripts/demo_scenario.py", name],
    {
      cwd: root,
      env: {
        ...process.env,
        SKILLSWAP_DOMAIN_DB: root + "/storage/browser-domain.sqlite",
      },
    },
  );
}
test.beforeEach(async ({ page }) => {
  execFileSync(root + "/.venv/bin/python", [root + "/scripts/seed_demo.py"], {
    cwd: root,
    env: {
      ...process.env,
      SKILLSWAP_DOMAIN_DB: root + "/storage/browser-domain.sqlite",
    },
  });
  await page.goto("/");
});
async function propose(page: any) {
  await page
    .getByRole("button", { name: "Find my exchange", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Approve & save proposal" }),
  ).toBeVisible();
}
test("propose_review_save_reload", async ({ page }) => {
  await propose(page);
  await expect(page.getByText("Maya → Leo", { exact: true })).toBeVisible();
  await expect(page.getByText("Leo → Nina", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Approve & save proposal" }).click();
  await expect(
    page.getByRole("heading", { name: "Proposal saved" }),
  ).toBeVisible();
  await expect(
    page.getByText("Awaiting participant confirmation", { exact: true }),
  ).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download proposal" }).click();
  expect((await download).suggestedFilename()).toContain("skillswap-");
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Proposal saved" }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/workspace-desktop.png",
    fullPage: true,
  });
});
test("stale_plan_requires_second_approval", async ({ page }) => {
  await propose(page);
  scenario("remove-nina-window");
  await page.getByRole("button", { name: "Approve & save proposal" }).click();
  await expect(
    page.getByText("Availability changed. Please review again.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Approve & save proposal" }),
  ).toBeEnabled();
  await expect(
    page.getByRole("heading", { name: "Proposal saved" }),
  ).not.toBeVisible();
  await expect(page.getByText(/Oct 28/).first()).toBeVisible();
});
test("participant_times_ignore_browser_zone", async ({ page }) => {
  await propose(page);
  await expect(
    page.getByText("America/Chicago · UTC−05:00").first(),
  ).toBeVisible();
  await expect(
    page.getByText("Asia/Kolkata · UTC+05:30").first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "New search", exact: true }).click();
  await page.getByLabel("Learner").selectOption("amelia");
  await page
    .getByLabel("What would you like to learn?")
    .fill("Excel automation");
  await propose(page);
  await expect(
    page.getByText("Next day", { exact: true }).first(),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "test-results/workspace-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});

test("quota_failure_is_visible_and_never_fabricates_a_plan", async ({
  page,
}) => {
  await page.getByLabel("What would you like to learn?").fill("simulate quota");
  await page
    .getByRole("button", { name: "Find my exchange", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("quota");
  await expect(
    page.getByRole("button", { name: "Approve & save proposal" }),
  ).not.toBeVisible();
  await page.getByText("Behind the exchange", { exact: true }).click();
  await expect(
    page.getByText("quota_limited", { exact: true }).first(),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/provider-degraded.png",
    fullPage: true,
  });
});

test("reviewer_failure_does_not_claim_a_reviewed_proposal", async ({
  page,
}) => {
  await page
    .getByLabel("What would you like to learn?")
    .fill("Presentation design, simulate reviewer outage");
  await page
    .getByRole("button", { name: "Find my exchange", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("Gemini");
  await expect(
    page.getByText("Awaiting independent review", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Checked & ready for your review", { exact: true }),
  ).not.toBeVisible();
  await expect(
    page.getByRole("button", { name: "Approve & save proposal" }),
  ).toBeDisabled();
});

test("clock_change_displays_both_endpoint_offsets", async ({ page }) => {
  const fixture = `
from skillswap.settings import Settings
from skillswap.repository import Repository
from skillswap.scheduling import normalize_window
from skillswap.models import LocalAvailabilityInput
r=Repository(Settings().domain_db)
def window(a,b,z,**folds):
 return normalize_window(LocalAvailabilityInput(start_local=a,end_local=b,timezone=z,**folds)).model_dump()
r.update_profile('amelia',timezone='America/Chicago',city='Chicago',country_code='US',availability=[window('2026-11-01T01:45','2026-11-01T01:45','America/Chicago',start_fold=0,end_fold=1)])
r.update_profile('bruno',availability=[window('2026-11-01T03:45','2026-11-01T04:45','America/Sao_Paulo')])
`;
  execFileSync(root + "/.venv/bin/python", ["-c", fixture], {
    cwd: root,
    env: {
      ...process.env,
      SKILLSWAP_DOMAIN_DB: root + "/storage/browser-domain.sqlite",
    },
  });
  await page.reload();
  await page.getByLabel("Learner").selectOption("amelia");
  await page
    .getByLabel("What would you like to learn?")
    .fill("Excel automation");
  await propose(page);
  await expect(
    page.getByText("America/Chicago · UTC−05:00 → UTC−06:00", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Clock change during this session", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/clock-change.png",
    fullPage: true,
  });
});

test("memory_explicit_remember_edit_forget_and_member_scope", async ({
  page,
}) => {
  await page
    .getByLabel("A preference for future searches")
    .fill("I prefer guided projects.");
  await page.getByRole("button", { name: "Remember", exact: true }).click();
  await expect(
    page.getByText("Preference saved for future searches."),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByText("I prefer guided projects.", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Learner").selectOption("leo");
  await expect(
    page.getByText("I prefer guided projects.", { exact: true }),
  ).not.toBeVisible();
  await page.getByLabel("Learner").selectOption("maya");
  await page
    .getByRole("button", { name: "Edit preference: I prefer guided projects." })
    .click();
  await page
    .getByLabel("Edit learning preference")
    .fill("I prefer discussion.");
  await page
    .getByRole("button", { name: "Save preference", exact: true })
    .click();
  await expect(
    page.getByText("I prefer discussion.", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/memory-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "test-results/memory-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page
    .getByRole("button", { name: "Forget preference: I prefer discussion." })
    .click();
  await expect(page.getByText("Preference forgotten.")).toBeVisible();
  await expect(
    page.getByText("I prefer discussion.", { exact: true }),
  ).not.toBeVisible();
});

test("memory_pending_and_degraded_states_are_honest", async ({ page }) => {
  let checked = false;
  const operation = {
    operation_id: "controlled-event",
    status: "pending",
    event_id: "vendor-event",
    memory_id: null,
    detail: "Waiting for Mem0 confirmation.",
  };
  await page.route("**/api/memories?*", (route) =>
    route.fulfill({
      json: {
        memories: [],
        operations: [
          {
            ...operation,
            status: checked ? "failed" : "pending",
            detail: checked
              ? "Mem0 did not save this change."
              : operation.detail,
          },
        ],
        provider: {
          mode: "degraded",
          detail:
            "Mem0 unavailable. Matching continues without remembered preferences.",
        },
      },
    }),
  );
  await page.route(
    "**/api/memory-operations/controlled-event/check",
    (route) => {
      checked = true;
      return route.fulfill({
        json: {
          ...operation,
          status: "failed",
          detail: "Mem0 did not save this change.",
        },
      });
    },
  );
  await page.reload();
  await expect(page.getByText(/Pending ·/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Remember", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Check pending change" }).click();
  await expect(page.getByText("Mem0 did not save this change.")).toBeVisible();
  await expect(
    page.getByText("Preference saved for future searches."),
  ).not.toBeVisible();
  await propose(page);
});

test("unknown_memory_outcome_can_be_acknowledged_without_retry", async ({
  page,
}) => {
  let acknowledged = false;
  const operation = {
    operation_id: "lost-response",
    status: "pending",
    event_id: null,
    memory_id: null,
    detail: "Outcome unconfirmed.",
  };
  await page.route("**/api/memories?*", (route) =>
    route.fulfill({
      json: {
        memories: [],
        operations: [
          {
            ...operation,
            acknowledged,
            detail: acknowledged
              ? "Outcome still unconfirmed; the change may appear later."
              : operation.detail,
          },
        ],
        provider: { mode: "test", detail: "Controlled memory boundary" },
      },
    }),
  );
  await page.route(
    "**/api/memory-operations/lost-response/acknowledge",
    (route) => {
      acknowledged = true;
      return route.fulfill({ json: { ...operation, acknowledged } });
    },
  );
  await page.reload();
  await expect(
    page.getByLabel("A preference for future searches"),
  ).toBeDisabled();
  await page
    .getByRole("button", { name: "Continue without confirmation" })
    .click();
  await expect(
    page.getByLabel("A preference for future searches"),
  ).toBeEnabled();
  await expect(page.getByText(/Unconfirmed ·/)).toBeVisible();
  await expect(
    page.getByText("Preference saved for future searches."),
  ).not.toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});
