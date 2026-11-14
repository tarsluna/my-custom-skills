import type { PublicAudit } from '@/lib/types';
import { businessVars } from '@/lib/palette';
import { Hero } from './Hero';
import { Business } from './Business';
import { Competitors } from './Competitors';
import { Creatives } from './Creatives';
import { Projects } from './Projects';
import { Assistant } from './Assistant';
import { Closing } from './Closing';
import { Motion } from './Motion';

export function AuditPage({ audit }: { audit: PublicAudit }) {
  const hasProjects = audit.projects.length > 0;
  const { sections } = audit.copy;
  const sheets = [
    { id: 'business', label: sections.business },
    { id: 'concurrents', label: sections.competitors },
    { id: 'creatives', label: sections.creatives },
    ...(hasProjects ? [{ id: 'projets', label: sections.projects }] : []),
    { id: 'assistant', label: sections.assistant },
    { id: 'suite', label: sections.next },
  ];
  const t = audit.theme;
  const theme = { ['--bg' as string]: t.background, ['--bg-alt' as string]: t.backgroundAlt, ['--bg-light' as string]: t.backgroundLight, ['--fg' as string]: t.foreground, ['--fg-soft' as string]: t.foregroundSoft, ['--fg-muted' as string]: t.muted, ['--accent' as string]: t.accent };
  const total = sheets.length;
  const at = (id: string) => sheets.findIndex((s) => s.id === id) + 1;
  const isFixture = (audit as PublicAudit & { _fixture?: string })._fixture;

  return (
    <div className="audit" style={{ ...theme, ...businessVars(audit.business.palette), ...(isFixture ? { ['--flag' as string]: '26px' } : {}) }}>
      {isFixture ? <p className="fixture-flag">Entreprise fictive · données de démonstration</p> : null}
      <nav className="topindex" aria-label="Index de la page">
        <a className="topindex__main" href="#creatives">
          {audit.copy.indexCta}
        </a>
        <div className="topindex__rest">
          {sheets
            .filter((s) => s.id !== 'creatives')
            .map((s) => (
              <a key={s.id} href={`#${s.id}`}>
                {s.label}
              </a>
            ))}
        </div>
      </nav>
      <main>
        <Hero audit={audit} sheets={sheets} />
        <Business audit={audit} n={at('business')} total={total} />
        <Competitors audit={audit} n={at('concurrents')} total={total} />
        <Creatives audit={audit} n={at('creatives')} total={total} />
        {hasProjects ? <Projects audit={audit} n={at('projets')} total={total} /> : null}
        <Assistant audit={audit} n={at('assistant')} total={total} />
        <Closing audit={audit} n={at('suite')} total={total} />
      </main>
      <Motion />
    </div>
  );
}
