import { test, expect } from '@playwright/test'

test.describe('Cover-Only Path (Simple Tier)', () => {
  test('upload → analysis → moodboard → cover brief → generate', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: /Create Your Book Cover/i }).click()
    await page.locator('input[type=file]').setInputFiles('e2e/fixtures/short_story.txt')
    await page.getByPlaceholder(/Enter book title/i).fill('The Ember Crown')
    await page.getByPlaceholder(/Your name/i).fill('E2E Author')
    await page.locator('select').selectOption('Fantasy')
    await page.getByRole('radio', { name: /Book Cover/i }).check()
    await page.getByRole('button', { name: /Upload & Continue/i }).click()

    // Style step: run analysis
    await expect(page.getByRole('button', { name: /Analyze Book/i })).toBeVisible()
    await page.getByRole('button', { name: /Analyze Book/i }).click()

    // Wait for redirect to analysis-review (may take a while)
    await page.waitForURL(/\/books\/\d+\/analysis-review/, { timeout: 120000 })
    await expect(page.locator('[role=tab][aria-label="Characters"]')).toBeVisible()
    await expect(page.locator('[role=tab][aria-label="Locations"]')).not.toBeVisible()

    // Navigate to Mood Board
    await page.getByRole('button', { name: /Mood Board/i }).click()
    await expect(page.locator('[role=tab][aria-label="Style Reference"]')).toBeVisible()

    // Upload cover reference (optional for speed; then Continue to Cover Brief)
    await page.locator('[data-testid=cover-upload-input]').setInputFiles('e2e/fixtures/sample_cover.jpg')
    await expect(page.getByRole('button', { name: /Analyse style/i })).toBeVisible()

    // Navigate to Cover Brief (skip I2T for speed in E2E)
    await page.getByRole('button', { name: /Continue to Cover Brief/i }).click()
    await expect(page.locator('[data-testid=cover-type-selector]')).toBeVisible()
    await expect(page.locator('[data-testid=prompt-panel-b]')).not.toBeVisible()

    // Trigger generation: go to Cover Studio and start generation
    await page.getByRole('button', { name: /Generate Cover/i }).click()
    await page.waitForURL(/\/books\/\d+\/studio\/cover/)
    await page.getByRole('button', { name: /Regenerate/i }).click()
    await expect(page.locator('text=Generating')).toBeVisible()
    await expect(page.locator('[data-testid=concept-card]')).toBeVisible({ timeout: 90000 })
  })
})
