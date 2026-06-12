import { test, expect } from '@playwright/test';

const TEST_TOKEN = process.env.TEST_TOKEN;

test('splash page loads', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('score sense');
  await page.screenshot({ path: 'tests/screenshots/splash.png', fullPage: true });
});

test('splash shows Google sign-in', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Sign in with Google' })).toBeVisible();
});

test('splash shows stat cards', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Real games', { exact: true })).toBeVisible();
  await expect(page.getByText('Instant', { exact: true })).toBeVisible();
  await expect(page.getByText('Free', { exact: true })).toBeVisible();
});

test('leaderboard loads', async ({ page }) => {
  test.skip(!TEST_TOKEN, 'TEST_TOKEN env var not set');

  await page.goto('/');
  await page.evaluate((token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('is_admin', 'true');
    localStorage.setItem('email', 'test@test.com');
    localStorage.setItem('name', 'Test');
  }, TEST_TOKEN);

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
  await expect(page.locator('h1')).toContainText('score sense');
});

test('splash on mobile', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('score sense');
  await page.screenshot({ path: 'tests/screenshots/splash-mobile.png', fullPage: true });
});
