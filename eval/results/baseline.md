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
## Génération (qwen2.5:7b via Ollama, top-5 chunks, température 0)

| Métrique | Score |
|---|---|
| Contenu correct | 8/14 |
| Citation correcte | 10/14 |
| Refus corrects | 2/2 |

Échecs : q002, q005, q009, q013, q014, q015 (causes à préciser par le diagnostic).
Attention : l'évaluation par mots-clés est approximative.
## Génération (qwen2.5:7b via Ollama, top-5 chunks, température 0)

| Métrique | Score |
|---|---|
| Contenu correct | 10/14 (8/14 avant correction de deux mots-clés trop stricts : q002, q013) |
| Citation correcte | 10/14 |
| Refus corrects | 2/2 |

| Échec | Cause |
|---|---|
| q005 | Retrieval : l'information « dernière version » n'est dans aucun chunk (outil nécessaire) |
| q009 | Génération : réponse incomplète alors que l'information était présente |
| q014 | Refus à tort malgré l'information dans les chunks |
| q015 | Retrieval : chunk Deprecations de la v1.19.0 non retrouvé |
## Effet du filtre repo/tag (14 questions, une exécution, température 0)

| Mesure | Sans filtre | Avec filtre |
|---|---|---|
| Release retrouvée @1 | 12/14 | 13/14 |
| Mots-clés de la réponse dans le top 5 | 12/14 | 12/14 |
| Génération : contenu correct | 10/14 | 11/14 |
| Génération : citation correcte | 10/14 | 12/14 |

Corrigée par le filtre : q014. Non corrigées : q005 (nécessite un outil), q009 (échec du modèle),
q015 (chunk Deprecations non retrouvé, cause en cours d'analyse).
Limite : la plupart des questions citent une version, ce qui avantage le filtre.
## Effet du filtre repo/tag et de K (14 questions, une exécution, température 0)

| Configuration | Mots-clés dans les chunks | Contenu correct | Citation correcte |
|---|---|---|---|
| Sans filtre, K = 5 | 12/14 | 10/14 | 10/14 |
| Filtre, K = 5 | 12/14 | 11/14 | 12/14 |
| Filtre, K adaptatif (5 sans filtre, 8 avec filtre) | 13/14 | 12/14 | 12/14 |

Corrigées : q014 (filtre), q015 (K adaptatif). Régression : q011 (citation) avec K = 8.
Non corrigées : q005 (nécessite un outil), q009 (réponse incomplète du modèle).
Limites : K = 8 choisi après analyse d'un échec du jeu d'évaluation ; la plupart des questions
citent une version, ce qui avantage le filtre ; une seule exécution.
q011 (question multi-releases) : contenu correct, mais citation incomplète (le fait de la v1.19.0 n'est pas
sourcé). Critère de citation étendu aux deux releases attendues.