# Baseline retrieval

**Configuration** : embeddings `intfloat/multilingual-e5-large`, chunks de 1500 caractères maximum (découpage par sections), base Qdrant locale, 1529 chunks, top-k = 5.

**Jeu d'évaluation** : 14 questions avec réponse dans le corpus (Qdrant et Dagster).

| Métrique | Score |
|---|---|
| Recall@1 | 12/14 = 86 % |
| Recall@3 | 13/14 = 93 % |
| Recall@5 | 13/14 = 93 % |

La métrique vérifie que la bonne release est retrouvée, pas le bon chunk.

## Échecs

- **q005** (version la plus récente de Dagster) : non retrouvée. La similarité de texte ne sait pas comparer des dates ; il faudra un outil qui trie par `published_at`.
- **q015** (paramètre déprécié en v1.19.0) : retrouvée au rang 2. Le modèle pèse peu le numéro de version ; piste : filtre sur les métadonnées `tag`.

## Limites

- Jeu de questions petit, centré sur deux dépôts : un point d'écart correspond à une seule question.
- Les questions sans réponse dans le corpus (q006, q016) ne sont pas encore évaluées.