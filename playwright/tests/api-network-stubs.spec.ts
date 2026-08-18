import { expect, test, type Page } from '@playwright/test';

const mockOrigin = 'https://qualtan.mock';

async function openMockApplication(page: Page) {
  await page.route(`${mockOrigin}/`, async (route) => {
    await route.fulfill({
      contentType: 'text/html',
      body: '<!doctype html><html><body><main id="app">QUALTAN mock application</main></body></html>',
    });
  });
  await page.goto(`${mockOrigin}/`);
}

test.describe('deterministic API and GraphQL network stubs', () => {
  test('stubs the REST resource endpoint and validates request contract', async ({ page }) => {
    let routedRequestCount = 0;
    await page.route(`${mockOrigin}/api/v1/resource`, async (route) => {
      routedRequestCount += 1;
      const request = route.request();
      expect(request.method()).toBe('GET');
      expect(request.headers().authorization).toBe('Bearer test-token');
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'resource-1', name: 'Mocked quality resource', status: 'ready' }),
      });
    });

    await openMockApplication(page);
    const response = await page.evaluate(async () => {
      const result = await fetch('/api/v1/resource', {
        headers: { Authorization: 'Bearer test-token' },
      });
      return { status: result.status, body: await result.json() };
    });

    expect(response.status).toBe(200);
    expect(response.body).toEqual({ id: 'resource-1', name: 'Mocked quality resource', status: 'ready' });
    expect(routedRequestCount).toBe(1);
  });

  test('stubs a GraphQL query and validates operation name, variables, and response shape', async ({ page }) => {
    let routedRequestCount = 0;
    await page.route(`${mockOrigin}/graphql`, async (route) => {
      routedRequestCount += 1;
      const request = route.request();
      expect(request.method()).toBe('POST');
      expect(request.headers()['content-type']).toContain('application/json');

      const body = JSON.parse(request.postData() ?? '{}');
      expect(body.operationName).toBe('GetProducts');
      expect(body.variables).toEqual({ includeInactive: false });
      expect(body.query).toContain('query GetProducts');
      expect(body.query).toContain('products');

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            products: [
              { id: 'product-1', name: 'Mocked Test Plan', price: 19.99 },
              { id: 'product-2', name: 'Mocked Evidence Pack', price: 29.99 },
            ],
          },
        }),
      });
    });

    await openMockApplication(page);
    const response = await page.evaluate(async () => {
      const result = await fetch('/graphql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operationName: 'GetProducts',
          variables: { includeInactive: false },
          query: 'query GetProducts($includeInactive: Boolean!) { products(includeInactive: $includeInactive) { id name price } }',
        }),
      });
      return { status: result.status, body: await result.json() };
    });

    expect(response.status).toBe(200);
    expect(response.body.data.products).toHaveLength(2);
    expect(response.body.data.products[0]).toEqual({ id: 'product-1', name: 'Mocked Test Plan', price: 19.99 });
    expect(routedRequestCount).toBe(1);
  });

  test('stubs GraphQL error responses so failure handling is testable without a live service', async ({ page }) => {
    await page.route(`${mockOrigin}/graphql`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: null,
          errors: [{ message: 'Product catalog is unavailable', extensions: { code: 'CATALOG_UNAVAILABLE' } }],
        }),
      });
    });

    await openMockApplication(page);
    const response = await page.evaluate(async () => {
      const result = await fetch('/graphql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operationName: 'GetProducts', query: 'query GetProducts { products { id } }' }),
      });
      return { status: result.status, body: await result.json() };
    });

    expect(response.status).toBe(200);
    expect(response.body.data).toBeNull();
    expect(response.body.errors[0].extensions.code).toBe('CATALOG_UNAVAILABLE');
  });
});
