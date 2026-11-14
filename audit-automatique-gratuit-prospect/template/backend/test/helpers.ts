import { mkdtemp } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { loadConfig, setConfigForTests } from '../src/config.js';
import { closePool, getPool, query } from '../src/db/pool.js';
import { migrate } from '../src/db/migrate.js';

export const TEST_DATABASE_URL = 'postgres://postgres:postgres@localhost:54329/audit_test';

export async function setupTestEnv(overrides: Record<string, string> = {}): Promise<{ dataDir: string }> {
  const dataDir = await mkdtemp(path.join(os.tmpdir(), 'audit-data-'));
  const env = {
    NODE_ENV: 'test',
    DATABASE_URL: TEST_DATABASE_URL,
    DATA_DIR: dataDir,
    ADMIN_API_KEY: 'admin-key-for-tests-0001',
    OPENROUTER_API_KEY: 'test',
    PUBLIC_BASE_URL: 'https://api.exemple.test',
    FRONTEND_ORIGIN: 'https://audit.exemple.fr',
    ...overrides,
  } as NodeJS.ProcessEnv;
  setConfigForTests(loadConfig(env));
  await migrate();
  return { dataDir };
}

export async function truncateAll(): Promise<void> {
  await query(`TRUNCATE settings, audits, bookings, jobs, creatives, competitors, projects, media, audit_steps, audit_costs, chat_sessions, chat_daily RESTART IDENTITY CASCADE`);
}

export async function teardownTestEnv(): Promise<void> {
  await closePool();
  setConfigForTests(null);
}

export { getPool };
