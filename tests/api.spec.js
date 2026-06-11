import { test, expect } from '@playwright/test';

test('GET / serves frontend', async ({ request }) => {
  const res = await request.get('/');
  expect(res.status()).toBe(200);
  const html = await res.text();
  expect(html).toContain('Weiqi Estimate Trainer');
});

test('GET /leaderboard serves frontend route', async ({ request }) => {
  const res = await request.get('/leaderboard');
  expect(res.status()).toBe(200);
  const html = await res.text();
  expect(html).toContain('Weiqi Estimate Trainer');
});

test('GET /api/leaderboard returns data', async ({ request }) => {
  const res = await request.get('/api/leaderboard');
  expect(res.status()).toBe(200);
  const data = await res.json();
  expect(Array.isArray(data)).toBe(true);
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
