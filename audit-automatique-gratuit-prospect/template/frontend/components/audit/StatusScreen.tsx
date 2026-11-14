import '@/components/audit/audit.css';

type Props = {
  tag: string;
  title: string;
  body: string;
  progress?: boolean;
  action?: { href: string; label: string };
};

/* Attente, erreur, jeton inconnu : une page presque vide, une phrase. */
export function StatusScreen({ tag, title, body, progress, action }: Props) {
  return (
    <main className="status">
      <div className="status__body">
        <p className="mono-tag">{tag}</p>
        <h1 className="d1 status__title">{title}</h1>
        <p className="status__text">{body}</p>
        {action ? (
          <a className="btn" href={action.href} rel="noopener noreferrer">
            {action.label}
          </a>
        ) : null}
      </div>
      <div className={progress ? 'status__ground is-live' : 'status__ground'} aria-hidden="true">
        <i />
      </div>
    </main>
  );
}
