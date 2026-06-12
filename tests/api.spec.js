import { test, expect } from '@playwright/test';

const ADMIN_TOKEN = process.env.TEST_TOKEN;

test('GET / serves frontend', async ({ request }) => {
  const res = await request.get('/');
  expect(res.status()).toBe(200);
  const html = await res.text();
  expect(html).toContain('Weiqi Estimate Trainer');
});

test('GET /leaderboard redirects non-admin', async ({ request }) => {
  const res = await request.get('/leaderboard');
  expect(res.status()).toBe(200);
  const html = await res.text();
  expect(html).toContain('Weiqi Estimate Trainer');
});

test('GET /api/leaderboard returns data for admin', async ({ request }) => {
  test.skip(!ADMIN_TOKEN, 'ADMIN_TOKEN env var not set');
  const res = await request.get('/api/leaderboard', {
    headers: { Authorization: `Bearer ${ADMIN_TOKEN}` },
  });
  expect(res.status()).toBe(200);
  const data = await res.json();
  expect(Array.isArray(data)).toBe(true);
});

test('GET /api/leaderboard denies non-admin', async ({ request }) => {
  const res = await request.get('/api/leaderboard');
  expect(res.status()).toBe(401);
});

test('GET /api/position requires auth', async ({ request }) => {
  const res = await request.get('/api/position');
  expect(res.status()).toBe(401);
});

test('POST /api/auth/google with invalid token', async ({ request }) => {
  const res = await request.post('/api/auth/google', {
    data: { credential: 'invalid-token' },
  });
  expect(res.status()).toBe(401);
});
