import { StatusScreen } from '@/components/audit/StatusScreen';

export default function NotFound() {
  return (
    <StatusScreen
      tag="404"
      title="Cette page n’existe pas."
      body="Le lien que vous avez suivi ne mène à aucun audit."
    />
  );
}
