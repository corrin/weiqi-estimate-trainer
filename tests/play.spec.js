import { test, expect } from '@playwright/test';

const TEST_TOKEN = process.env.TEST_TOKEN;

test('play page shows Go board', async ({ page }) => {
  test.skip(!TEST_TOKEN, 'TEST_TOKEN env var not set');

  await page.goto('/');
  await page.evaluate((token) => {
    localStorage.setItem('token', token);
  }, TEST_TOKEN);

  await page.goto('/play');
  await page.waitForTimeout(2000);

  await expect(page.locator('h2')).toContainText("final score");
  await page.screenshot({ path: 'tests/screenshots/play.png', fullPage: true });
});

test('play page shows board on mobile', async ({ page }) => {
  test.skip(!TEST_TOKEN, 'TEST_TOKEN env var not set');

  await page.goto('/');
  await page.evaluate((token) => {
    localStorage.setItem('token', token);
  }, TEST_TOKEN);

  await page.goto('/play');
  await page.waitForTimeout(2000);

  await page.screenshot({ path: 'tests/screenshots/play-mobile.png', fullPage: true });
});

test('guess submission works', async ({ request }) => {
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
    data: { game_id: position.game_id, guessed_score: 5.5 },
  });
  expect(guessRes.status()).toBe(200);
  const result = await guessRes.json();
  expect(result.rating).toBeTruthy();
  expect(result.deviation).toBeGreaterThanOrEqual(0);
});
