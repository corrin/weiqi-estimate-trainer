import { test, expect } from '@playwright/test';

const TEST_TOKEN = process.env.TEST_TOKEN;

// --- Splash page ---

test('splash renders headline, sign-in, and stat cards', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('score sense');
  await expect(page.getByRole('button', { name: 'Sign in with Google' })).toBeVisible();
  await expect(page.getByText('Real games', { exact: true })).toBeVisible();
  await page.screenshot({ path: 'tests/screenshots/splash.png', fullPage: true });
});

test('splash privacy modal shows', async ({ page }) => {
  await page.goto('/');
  await page.getByText('Privacy').click();
  await expect(page.getByText('Weiqi Estimate Trainer uses Google')).toBeVisible();
});

test('splash renders on mobile', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toContainText('score sense');
  await page.screenshot({ path: 'tests/screenshots/splash-mobile.png', fullPage: true });
});

// --- Auth ---

test('/play redirects unauthenticated users to splash', async ({ page }) => {
  await page.goto('/play');
  await expect(page.locator('h1')).toContainText('score sense');
});

test('/api/position requires auth', async ({ request }) => {
  const res = await request.get('/api/position');
  expect(res.status()).toBe(401);
});

// --- Admin gating ---

test('/api/leaderboard denies non-admin', async ({ request }) => {
  const res = await request.get('/api/leaderboard');
  expect(res.status()).toBe(401);
});

test('leaderboard loads for admin', async ({ page }) => {
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

// --- Play page ---

test('play page renders board and score slider', async ({ page }) => {
  test.skip(!TEST_TOKEN, 'TEST_TOKEN env var not set');

  await page.goto('/');
  await page.evaluate((token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('email', 'test@test.com');
    localStorage.setItem('name', 'Test');
  }, TEST_TOKEN);

  await page.goto('/play');
  await page.waitForTimeout(2000);

  await expect(page.locator('h2')).toContainText('final score');
  await expect(page.locator('canvas')).toBeVisible();
  await page.screenshot({ path: 'tests/screenshots/play.png', fullPage: true });
});

test('play page on mobile', async ({ page }) => {
  test.skip(!TEST_TOKEN, 'TEST_TOKEN env var not set');

  await page.goto('/');
  await page.evaluate((token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('email', 'test@test.com');
    localStorage.setItem('name', 'Test');
  }, TEST_TOKEN);

  await page.goto('/play');
  await page.waitForTimeout(2000);

  await page.screenshot({ path: 'tests/screenshots/play-mobile.png', fullPage: true });
});

test('guess submission works end-to-end', async ({ request }) => {
  test.skip(!TEST_TOKEN, 'TEST_TOKEN env var not set');

  const posRes = await request.get('/api/position', {
    headers: { Authorization: `Bearer ${TEST_TOKEN}` },
  });
  expect(posRes.status()).toBe(200);
  const position = await posRes.json();
  expect(position.game_id).toBeTruthy();
  expect(position.stones).toBeTruthy();

  const guessRes = await request.post('/api/guess', {
    headers: { Authorization: `Bearer ${TEST_TOKEN}` },
    data: { game_id: position.game_id, guessed_score: 4 },
  });
  expect(guessRes.status()).toBe(200);
  const result = await guessRes.json();
  expect(result.rating).toBeTruthy();
  expect(result.deviation).toBeGreaterThanOrEqual(0);
});
