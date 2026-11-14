import { mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import EmbeddedPostgres from 'embedded-postgres';

export const TEST_PORT = 54329;
export const TEST_DB = 'audit_test';

/** Vrai Postgres local (binaire embarqué, dossier temporaire) : SKIP LOCKED et verrous consultatifs inclus. */
export default async function setup() {
  const databaseDir = await mkdtemp(path.join(os.tmpdir(), 'audit-pg-'));
  const pg = new EmbeddedPostgres({ databaseDir, user: 'postgres', password: 'postgres', port: TEST_PORT, persistent: false, onLog: () => undefined, onError: () => undefined });
  await pg.initialise();
  await pg.start();
  await pg.createDatabase(TEST_DB);
  return async () => {
    await pg.stop();
    await rm(databaseDir, { recursive: true, force: true }).catch(() => undefined);
  };
}
