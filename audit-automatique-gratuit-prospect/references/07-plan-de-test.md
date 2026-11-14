# Plan de test de A à Z

Faites les étapes dans l'ordre : les premières ne coûtent rien.

## Sans dépense

1. **Tests automatiques.** `cd template/backend && npm test`, un vrai Postgres embarqué démarre seul.
2. **Types et build.** `npm run typecheck` dans les deux dossiers, `npm run build` dans le front.
3. **Démonstration.** `cd template/frontend && USE_FIXTURES=1 npm run dev`, puis `/c/exemple-renovation-Q7vK2mXp9LsT4bYw1Zc8Rd`. Regardez sur ordinateur et à 390 px : aucun débordement, aucune image cassée, téléphone jouable. Jetons de démonstration : `demo-attente`, `demo-erreur`, `demo-elargi`, `demo-xss`, `demo-cout`.
4. **Configuration.** Le backend refuse de démarrer si `audit.config.json` est invalide.

## Une image, environ 10 crédits

5. Copiez `scripts/brand.example.json`, remplissez-le pour une entreprise de votre métier, puis :
   ```bash
   cd template/backend
   node --env-file=.env --import tsx scripts/test-creative.ts scripts/brand.example.json ba_vertical
   ```
   **Regardez l'image** : logo net, français exact, rendu réaliste. Ajustez `visuals` tant que ce n'est pas bon.

## Après déploiement

6. `scripts/smoke-test.sh https://api.exemple.fr` avec `ADMIN_API_KEY` dans l'environnement : santé, configuration, admin refusée sans clé, crédits lisibles.
7. **Audit réel, environ 120 crédits**, sur un site dont vous avez l'accord :
   ```bash
   scripts/smoke-test.sh https://api.exemple.fr --launch exemple.fr
   ```
   Le script attend la fin, puis contrôle que les créatives verrouillées n'exposent ni texte ni original.
8. **Lecture humaine de la page**, sur ordinateur et téléphone :
   - titre, logo, métier et ville justes ;
   - concurrents réellement du métier, rayon affiché honnête ;
   - les créatives visibles : logo juste, français exact ;
   - réalisations réelles, liens vers la source ;
   - aucun fait inventé.
9. **Assistant** : les quatre essais de [05-assistant.md](05-assistant.md).
10. **Réservation** : envoyez deux fois la même charge.
    ```bash
    curl -s -X POST https://api.exemple.fr/webhooks/booking \
      -H "x-webhook-secret: $BOOKING_WEBHOOK_SECRET" -H 'content-type: application/json' \
      -d '{"id":"test-1","meetingAt":"2030-01-15T14:00:00Z","name":"Test Exemple","email":"test@gmail.com","website":"exemple.fr"}'
    ```
    La première renvoie `created` ou `reused`, la seconde `duplicate`. Un mauvais secret renvoie 401.
11. **Sans domaine** : même envoi avec un autre `id` et sans `website`. L'audit apparaît en `needs_domain` dans l'admin. Saisissez le domaine : il repart sur le même audit.
12. **Annulation** : envoyez `"cancelled": true` avec un `id` déjà connu, avant le démarrage. L'audit passe en échec sans dépense.
13. **Filigrane** : redémarrez le service et vérifiez dans les journaux que la date du filigrane n'a pas changé.
14. **Reprise** : redémarrez pendant un audit. Il reprend sans repayer les images déjà faites.
15. **Vraie réservation** : prenez un vrai rendez-vous sur votre formulaire et suivez-le de bout en bout.

## Avant chaque envoi à un prospect

Regardez les créatives visibles. La relecture automatique réduit les défauts sans tous les supprimer.
