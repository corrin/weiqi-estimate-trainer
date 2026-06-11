import { test, expect } from '@playwright/test';

test('splash page loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('estimate');
  await page.screenshot({ path: 'tests/screenshots/splash.png', fullPage: true });
});

test('splash shows Google sign-in', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Sign in with Google' })).toBeVisible();
});

test('splash shows stat cards', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('34k+')).toBeVisible();
  await expect(page.getByText('KataGo', { exact: true })).toBeVisible();
  await expect(page.getByText('Free', { exact: true })).toBeVisible();
});

test('leaderboard loads', async ({ page }) => {
  await page.goto('/leaderboard');
  await expect(page.locator('h2')).toContainText('Leaderboard');
  await page.screenshot({ path: 'tests/screenshots/leaderboard.png', fullPage: true });
});

test('splash privacy modal', async ({ page }) => {
  await page.goto('/');
  await page.getByText('Privacy').click();
  await expect(page.getByText('Weiqi Estimate Trainer uses Google')).toBeVisible();
  await page.screenshot({ path: 'tests/screenshots/privacy.png', fullPage: true });
});

test('redirect to splash when unauthenticated', async ({ page }) => {
  await page.goto('/play');
  await expect(page.locator('h1')).toContainText('estimate');
});

test('splash on mobile', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('estimate');
  await page.screenshot({ path: 'tests/screenshots/splash-mobile.png', fullPage: true });
});
