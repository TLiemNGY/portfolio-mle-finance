# ADR-001 : Coupe-circuit budget automatique

## Statut
Accepté

## Contexte
Le projet doit rester dans un budget strict de 5 à 15€/mois maximum,
tout en utilisant des services GCP réellement utilisés en entreprise
(plutôt que des alternatives "bricolées" pour rester à 0€ à tout prix).
Un dépassement de budget non maîtrisé est le risque principal identifié
sur un compte GCP personnel.

## Décision
Mise en place d'une chaîne de protection automatique :
1. Budget GCP à 15€/mois avec alertes à 50%, 80%, 100%
2. Notification Pub/Sub (topic `billing-alerts`) déclenchée par le budget
3. Cloud Function gen2 (`stop-billing`) abonnée à ce topic, qui désactive
   automatiquement la facturation du projet si le seuil de 100% est dépassé

## Alternatives considérées
- **Alertes email seules** : rejeté — aucune garantie technique, dépend
  d'une action manuelle rapide de ma part.
- **Rester en 100% Always Free (0€)** : rejeté — impliquait de remplacer
  des services standards (Pub/Sub, Dataflow, Vertex AI Pipelines) par des
  alternatives non représentatives d'un usage entreprise, moins pertinent
  pour un objectif de reconversion MLE.
- **Quotas seuls (sans coupe-circuit)** : insuffisant seul — les quotas
  couverts (BigQuery notamment) ne couvrent pas tous les services, alors
  que le coupe-circuit protège au niveau du projet entier.

## Conséquences
- Protection automatique et garantie contre tout dépassement du budget.
- Effet de bord assumé : un déclenchement réel coupera aussi tous les
  services en cours d'exécution (acceptable pour un projet solo, pas
  pour un service en production avec des utilisateurs).
- Le compte de service `stop-billing-sa` doit rester strictement limité
  au rôle `roles/billing.projectManager` (principe du moindre privilège).
