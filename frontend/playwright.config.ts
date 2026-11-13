import { defineConfig, devices } from "@playwright/test"

// e2e 走完整真实栈：uvicorn（含 prestart 迁移+种子）+ vite dev server。
// 后端连接本机 db（POSTGRES_SERVER=localhost，独立于 docker compose 的 db 服务名）。
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      // 浏览器会把 localhost 解析为 ::1（IPv6），而 uvicorn 默认只绑 127.0.0.1，
      // 因此 e2e 全链路统一用 127.0.0.1（不影响日常 dev 的 localhost 配置）
      command:
        "bash -c 'cd ../backend && POSTGRES_SERVER=localhost uv run bash scripts/prestart.sh && POSTGRES_SERVER=localhost uv run uvicorn app.main:app --host 127.0.0.1 --port 8000'",
      url: "http://127.0.0.1:8000/api/v1/utils/ready-check/",
      reuseExistingServer: !process.env.CI,
      stdout: "ignore",
      stderr: "pipe",
      timeout: 120_000,
    },
    {
      command: "npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: !process.env.CI,
      env: { VITE_API_URL: "http://127.0.0.1:8000" },
      stdout: "ignore",
      stderr: "pipe",
      timeout: 60_000,
    },
  ],
})
