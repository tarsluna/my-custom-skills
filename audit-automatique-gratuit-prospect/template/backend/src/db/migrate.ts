import { readdir, readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { getPool } from './pool.js';
import { log } from '../log.js';

const MIGRATIONS_DIR = fileURLToPath(new URL('../../migrations/', import.meta.url));
const LOCK_KEY = 482910331;

/** Applique les migrations manquantes, une transaction par fichier, sous verrou : deux démarrages simultanés ne se gênent pas. */
export async function migrate(dir: string = MIGRATIONS_DIR): Promise<string[]> {
  const client = await getPool().connect();
  const applied: string[] = [];
  try {
    await client.query('SELECT pg_advisory_lock($1)', [LOCK_KEY]);
    await client.query('CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())');
    const done = new Set((await client.query<{ name: string }>('SELECT name FROM schema_migrations')).rows.map((r) => r.name));
    const files = (await readdir(dir)).filter((f) => f.endsWith('.sql')).sort();
    for (const file of files) {
      if (done.has(file)) continue;
      const sql = await readFile(path.join(dir, file), 'utf8');
      await client.query('BEGIN');
      try {
        await client.query(sql);
        await client.query('INSERT INTO schema_migrations (name) VALUES ($1)', [file]);
        await client.query('COMMIT');
        applied.push(file);
        log.info('migration appliquée', { file });
      } catch (e) {
        await client.query('ROLLBACK');
        throw e;
      }
    }
  } finally {
    await client.query('SELECT pg_advisory_unlock($1)', [LOCK_KEY]).catch(() => undefined);
    client.release();
  }
  return applied;
}
