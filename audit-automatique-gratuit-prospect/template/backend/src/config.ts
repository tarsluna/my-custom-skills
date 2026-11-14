import { z } from 'zod';

const bool = (d: boolean) =>
  z.preprocess((v) => (v === undefined || v === '' ? d : /^(1|true|yes|on)$/i.test(String(v))), z.boolean());
const int = (d: number, min = 0) => z.coerce.number().int().min(min).default(d);

const Env = z.object({
  NODE_ENV: z.string().default('development'),
  PORT: int(8080, 1),
  DATABASE_URL: z.string().min(1),
  DATA_DIR: z.string().default('/data'),
  PUBLIC_BASE_URL: z.string().url().default('http://localhost:8080'),
  FRONTEND_ORIGIN: z.string().url().default('http://localhost:4411'),
  BOOKING_URL: z.string().url().default('https://exemple.fr/rendez-vous'),

  ADMIN_API_KEY: z.string().min(16, 'ADMIN_API_KEY doit faire au moins 16 caractères'),
  OPENROUTER_API_KEY: z.string().min(1),
  APIFY_TOKEN: z.string().min(1).optional(),
  KIE_API_KEY: z.string().min(1).optional(),

  /** generic : votre outil appelle /webhooks/booking. iclosed : sonde de l'API iClosed, exemple fourni. */
  BOOKING_PROVIDER: z.enum(['generic', 'iclosed']).default('generic'),
  BOOKING_WEBHOOK_SECRET: z.string().min(8).optional(),
  BOOKING_EVENT_IDS: z.string().default(''),
  ICLOSED_API_KEY: z.string().min(1).optional(),

  /** Option désactivée sans ces deux valeurs : fourchette issue de VOS campagnes réelles, jamais inventée. */
  COST_ESTIMATE_MIN: z.coerce.number().positive().optional(),
  COST_ESTIMATE_MAX: z.coerce.number().positive().optional(),

  LLM_MODEL: z.string().default('google/gemini-3.8-flash'),
  LLM_FALLBACK: z.string().default('moonshotai/kimi-k3'),

  POLLER_ENABLED: bool(true),
  POLLER_INTERVAL_MS: int(120_000, 5_000),
  WORKER_ENABLED: bool(true),
  WORKER_CONCURRENCY: int(2, 1),

  MAX_AUDITS_PER_DAY: int(25, 1),
  REUSE_WINDOW_DAYS: int(30, 0),
  MAX_GENERATIONS_PER_AUDIT: int(14, 1),

  ADS_RESULTS_LIMIT: int(30, 1),
  ADS_MAX_QUERIES: int(6, 1),
  ADS_MIN_COMPETITORS: int(3, 1),
  ADS_MAX_COMPETITORS: int(8, 1),

  CRAWL_MAX_INTERNAL_PAGES: int(10, 0),
  PROJECTS_MAX: int(9, 1),

  CHAT_MAX_MESSAGES_PER_SESSION: int(40, 2),
  CHAT_MAX_MESSAGE_LENGTH: int(500, 1),
  CHAT_MAX_PER_AUDIT_PER_DAY: int(400, 1),
  CHAT_RATE_PER_MINUTE: int(15, 1),
});

export type Config = z.infer<typeof Env> & { bookingEventIds: Set<string> };

let cached: Config | null = null;

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  const parsed = Env.safeParse(env);
  if (!parsed.success) {
    const issues = parsed.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join(' ; ');
    throw new Error(`Configuration invalide : ${issues}`);
  }
  const d = parsed.data;
  return {
    ...d,
    bookingEventIds: new Set(d.BOOKING_EVENT_IDS.split(',').map((s) => s.trim()).filter(Boolean)),
  };
}

export function cfg(): Config {
  if (!cached) cached = loadConfig();
  return cached;
}

export function setConfigForTests(c: Config | null) {
  cached = c;
}
