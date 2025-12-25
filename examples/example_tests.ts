import { test, expect } from '@playwright/test';

// 1. Web Test Example
test('Web: User can login', async ({ page }) => {
  await page.goto('https://example.com/login');
  await page.fill('#username', 'testuser');
  await page.fill('#password', 'password123');
  await page.click('#login-button');
  await expect(page).toHaveURL(/dashboard/);
});

// 2. REST API Test Example
test('API: Get user details', async ({ request }) => {
  const response = await request.get('https://api.example.com/users/1');
  expect(response.ok()).toBeTruthy();
  const body = await response.json();
  expect(body.name).toBe('John Doe');
});

// 3. GraphQL API Test Example
test('GraphQL: Fetch products', async ({ request }) => {
  const query = `
    query GetProducts {
      products {
        id
        name
        price
      }
    }
  `;
  const response = await request.post('https://api.example.com/graphql', {
    data: { query }
  });
  expect(response.ok()).toBeTruthy();
  const body = await response.json();
  expect(body.data.products).toBeDefined();
});

// 4. Mobile Emulation Example
test.use({ viewport: { width: 375, height: 667 }, isMobile: true });
test('Mobile: Responsive menu', async ({ page }) => {
  await page.goto('https://example.com');
  await page.click('#mobile-menu-button');
  await expect(page.locator('#mobile-nav')).toBeVisible();
});
