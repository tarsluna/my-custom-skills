/** Erreur définitive au message lisible : l'audit passe en `failed`, sans nouvelle tentative. */
export class FatalAuditError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FatalAuditError';
  }
}
