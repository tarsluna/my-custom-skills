import { notFound } from 'next/navigation';

/* Les pages d'audit vivent en /c/<jeton> : l'accueil n'expose rien. */
export default function Home() {
  notFound();
}
