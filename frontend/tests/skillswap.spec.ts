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
