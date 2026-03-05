import { test, expect } from '@playwright/test'

test.describe('Full Book Path (Pro Tier)', () => {
  test('home loads and shows dashboard', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('Noctua')
    await expect(page.getByRole('button', { name: /Create Your Book Cover/i })).toBeVisible()
  })
})
