import pg from 'pg';
import { cfg } from '../config.js';

// Les timestamptz restent des Date ; les numeric reviennent en nombre pour les coûts.
pg.types.setTypeParser(pg.types.builtins.NUMERIC, (v) => (v === null ? null : Number(v)));

let pool: pg.Pool | null = null;

export function getPool(): pg.Pool {
  if (!pool) {
    pool = new pg.Pool({ connectionString: cfg().DATABASE_URL, max: 10 });
    pool.on('error', (e) => console.error(JSON.stringify({ level: 'error', msg: 'pg pool', error: e.message })));
  }
  return pool;
}

export type Db = pg.Pool | pg.PoolClient;

export async function query<T extends pg.QueryResultRow = any>(text: string, params: unknown[] = [], db: Db = getPool()) {
  return db.query<T>(text, params as any[]);
}

export async function tx<T>(fn: (c: pg.PoolClient) => Promise<T>): Promise<T> {
  const client = await getPool().connect();
  try {
    await client.query('BEGIN');
    const out = await fn(client);
    await client.query('COMMIT');
    return out;
  } catch (e) {
    await client.query('ROLLBACK').catch(() => undefined);
    throw e;
  } finally {
    client.release();
  }
}

export async function closePool() {
  if (pool) {
    const p = pool;
    pool = null;
    await p.end();
  }
}
