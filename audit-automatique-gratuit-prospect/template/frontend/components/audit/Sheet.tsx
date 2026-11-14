export function SheetHead({
  n,
  total,
  business,
  title,
  lead,
}: {
  n: number;
  total: number;
  business: string;
  title: React.ReactNode;
  lead?: React.ReactNode;
}) {
  return (
    <header className="head">
      <div className="head__rule" data-m="draw" aria-hidden="true">
        <i />
      </div>
      <p className="head__tag">
        <span>
          Section {String(n).padStart(2, '0')}/{String(total).padStart(2, '0')}
        </span>
        <span className="head__biz">{business}</span>
      </p>
      <h2 className="d1 head__title" data-m="up">
        {title}
      </h2>
      {lead ? (
        <p className="head__lead" data-m="up">
          {lead}
        </p>
      ) : null}
    </header>
  );
}

export function Ground({ note }: { note?: string }) {
  return (
    <div className="ground" aria-hidden="true">
      <i />
      {note ? <em>{note}</em> : null}
    </div>
  );
}
