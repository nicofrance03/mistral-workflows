# mistral-workflows — Briefing bourse quotidien

Workflow Mistral qui génère chaque matin un briefing des informations importantes sur :

- **Vallourec** (VK)
- **Coface** (COFA)
- **Bolloré**
- **Safran** (SAF)

## Fonctionnement

1. Le workflow `veille-bourse-briefing` récupère les dernières actualités de chaque société (Google News RSS, édition France).
2. Un modèle Mistral synthétise un briefing structuré en français (faits marquants, résultats, cours, événements à venir).
3. Le briefing est retourné comme résultat d'exécution, consultable dans [Mistral Studio](https://console.mistral.ai/build/workflows).

## Planification

Une exécution quotidienne est déclenchée à 7h00 (Europe/Paris), tous les jours.

## Déploiement

Le déploiement managé est construit depuis ce dépôt (branche `main`). Aucune clé API n'est stockée dans le dépôt : le worker managé s'authentifie avec un jeton de service injecté par la plateforme.
