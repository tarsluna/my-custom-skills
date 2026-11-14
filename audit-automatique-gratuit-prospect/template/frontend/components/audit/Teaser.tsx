/* Rien n'est masqué ici : le DOM ne contient que des formes. Le contenu réel n'existe pas sur cette page. */

function GhostPlan() {
  const rows = [
    [0, 20],
    [10, 26],
    [22, 18],
    [30, 34],
    [46, 22],
    [58, 30],
    [70, 26],
  ];
  return (
    <svg viewBox="0 0 100 74" preserveAspectRatio="none" aria-hidden="true">
      {[0, 25, 50, 75].map((x) => (
        <rect key={x} x={x} y="0" width=".25" height="74" fill="currentColor" opacity=".35" />
      ))}
      {rows.map(([x, w], i) => (
        <rect key={i} x={x} y={4 + i * 10} width={w} height="5" rx="1.6" fill="currentColor" opacity={0.92 - i * 0.07} />
      ))}
    </svg>
  );
}

function GhostEstimate() {
  const bars = [18, 26, 22, 34, 30, 42, 38, 52, 48, 60];
  return (
    <svg viewBox="0 0 100 74" preserveAspectRatio="none" aria-hidden="true">
      <rect x="0" y="2" width="46" height="13" rx="3" fill="currentColor" opacity=".9" />
      <rect x="50" y="6" width="22" height="7" rx="2" fill="currentColor" opacity=".5" />
      {bars.map((h, i) => (
        <rect key={i} x={i * 10 + 1} y={74 - h} width="7" height={h} rx="1.4" fill="currentColor" opacity={0.5 + i * 0.05} />
      ))}
    </svg>
  );
}

function GhostSearch() {
  const rows = [78, 64, 88, 52, 70, 44, 60];
  return (
    <svg viewBox="0 0 100 74" preserveAspectRatio="none" aria-hidden="true">
      {rows.map((w, i) => (
        <g key={i}>
          <rect x="0" y={3 + i * 10} width={w} height="4.4" rx="1.4" fill="currentColor" opacity={0.86 - i * 0.06} />
          <rect x="90" y={3 + i * 10} width="10" height="4.4" rx="1.4" fill="currentColor" opacity=".5" />
        </g>
      ))}
    </svg>
  );
}

const GHOSTS = [GhostPlan, GhostEstimate, GhostSearch];

export function Teaser({ items, sentence }: { items: { title: string; sub: string }[]; sentence: string }) {
  return (
    <div className="teaser">
      <ul className="teaser__sheets">
        {items.map(({ title, sub }, i) => {
          const Ghost = GHOSTS[i % GHOSTS.length];
          return (
          <li key={title} className="tsheet" data-m="up">
            <h3 className="d4">{title}</h3>
            <p className="tsheet__sub">{sub}</p>
            <div className="tsheet__draw">
              <div className="tsheet__sharp">
                <Ghost />
              </div>
              <div className="tsheet__soft">
                <Ghost />
              </div>
            </div>
          </li>
          );
        })}
      </ul>
      <div className="teaser__veil">
        <p className="d2 teaser__line">{sentence}</p>
      </div>
    </div>
  );
}
