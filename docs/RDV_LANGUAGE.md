# Langage des rendez-vous dans Lumyn

## Objectif

Ce document liste les différentes façons naturelles d’écrire un rendez-vous.

Il servira de référence pour développer et tester l’analyseur de rendez-vous.

Lumyn doit progressivement s’adapter à la manière d’écrire de l’utilisateur.

---

## Informations à reconnaître

Lumyn cherchera séparément :

- le titre ;
- le jour de la semaine ;
- la date ;
- l’heure ;
- le lieu ;
- les informations manquantes ;
- les incohérences éventuelles.

---

## Exemples simples

- Dentiste mardi 14h30
- Orthophoniste vendredi 10h
- Garage lundi 8h
- Psychiatre jeudi 9h
- École Owen lundi 8h30

---

## Avec une date numérique

- Dentiste mardi 17/07 à 14h30
- Dentiste 17/07 14h30
- Médecin le 03/10 à 10h
- Psychologue 12/09 9h
- Contrôle technique le 3/10 à 10h

---

## Avec le mois écrit

- Dentiste mardi 17 juillet à 14h30
- Dentiste le 17 juillet à 14h30
- Contrôle technique le 3 octobre à 10h
- Psychiatre jeudi 12 septembre à 9h
- École Owen lundi 2 septembre 8h30

---

## Avec une date relative

- Dentiste demain à 14h30
- Médecin après-demain à 10h
- CAF dans 15 jours
- Psychiatre jeudi prochain à 9h
- Réunion la semaine prochaine mardi à 14h

---

## Ordre des mots différent

- Mardi 17 juillet dentiste à 14h30
- 17 juillet dentiste 14h30
- À 10h le 3 octobre contrôle technique
- Jeudi prochain psychiatre à Vannes 9h
- Owen école lundi 8h30

---

## Avec un lieu

- Psychiatre jeudi prochain à Vannes à 9h
- Dentiste mardi 14h30 à Lorient
- CAF vendredi 10h à Ploërmel
- Contrôle technique le 3 octobre à Pontivy à 10h

---

## Informations manquantes

Lumyn doit pouvoir détecter qu’une information importante manque.

Exemples :

- Dentiste mardi
- Psychiatre à 9h
- CAF dans 15 jours
- Contrôle technique le 3 octobre
- École Owen lundi

Réponse attendue :

- demander l’heure si elle manque ;
- demander la date si elle manque ;
- demander le titre si nécessaire ;
- ne pas créer automatiquement un rendez-vous incomplet.

---

## Incohérences

Exemple :

- mardi 17 juillet

Si le 17 juillet ne tombe pas un mardi, Lumyn doit signaler l’incohérence.

Réponse attendue :

- afficher le jour calculé ;
- demander confirmation ;
- ne pas choisir silencieusement à la place de l’utilisateur.

---

## Formats d’heure à reconnaître

- 14h
- 14h30
- 14 h 30
- 14:30
- 9h
- 09h00

---

## Formats de date à reconnaître

- 17/07
- 17/07/2026
- 17 juillet
- le 17 juillet
- mardi 17 juillet
- demain
- après-demain
- jeudi prochain
- dans 15 jours

---

## Règles de conception

1. L’ordre des mots ne doit pas être strict.
2. Lumyn doit afficher ce qu’elle a compris avant de créer le rendez-vous.
3. Une incohérence doit être signalée.
4. Une information manquante doit déclencher une question.
5. L’analyseur doit être amélioré à partir de phrases réellement utilisées.
6. L’application doit rester utilisable sans intelligence artificielle.

---

## Validation avant création

Lumyn ne doit jamais créer immédiatement un rendez-vous à partir du texte saisi.

Elle doit d’abord afficher ce qu’elle a compris :

- titre ;
- date ;
- jour ;
- heure ;
- lieu éventuel.

Puis demander une confirmation explicite.

Exemple :

```text
Lumyn a compris :

Titre : Dentiste
Date : 21 juillet 2026
Jour : mardi
Heure : 14h30

Confirmer la création ?
