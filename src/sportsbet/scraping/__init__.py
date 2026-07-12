"""Couche de récupération d'informations sur le web — SANS clé API.

Tout passe par du HTTP public + parsing HTML. C'est volontairement modulaire
et « best-effort » : les sites changent, certains bloquent les robots, d'autres
chargent leurs données en JavaScript. Chaque source échoue proprement (retourne
une liste vide) plutôt que de casser le pipeline.

Sources documentées et éthiques recommandées (respecter robots.txt & CGU) :
  - Résultats/calendriers : sites officiels de ligues, Wikipédia, agrégateurs.
  - Cotes : comparateurs publics (à des fins d'analyse personnelle).
  - Avis d'experts : presse sportive, forums, réseaux sociaux (via recherche).
"""
