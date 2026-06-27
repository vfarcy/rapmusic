# RapMusic Karaoke CLI

Projet Python pour:

- générer un beat MIDI boom-bap flow-ready
- afficher des paroles en karaoké dans le terminal (mot à mot)
- synchroniser la durée du texte avec la musique MIDI

État: documentation mise à jour pour les scripts actuels.

## Fonctionnalités

- Génération d un beat principal via mc_beat.py
- Karaoke CLI avec:
  - mode scroll (sans scintillement)
  - mode frame (fenêtre glissante)
  - surbrillance mot à mot
- Synchronisation texte/midi:
  - fin exacte (exact)
  - fin instrumentale conservée (tail-silence)
- Support UTF-8 Windows pour afficher les accents français (é, è, à, ç, œ)
- Outil de grille de flow V2 (1-e-&-a) via build_flow_v2.py
- Vocalisation automatique des paroles (voix guide) via vocalize_song.py

## Prérequis

- Python 3.10+
- Windows, macOS ou Linux
- Un lecteur associé aux fichiers .mid

Dépendances Python (requirements.txt):

- mido==1.3.3
- music21==10.5.0
- pyttsx3==2.99

## Installation

### Option recommandée (venv)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Scripts principaux

- mc_beat.py
  - Génère le beat principal Rhodes: mc_solaar_flow_ready.mid
  - Génère aussi une variante EP2: mc_solaar_flow_ready_ep2.mid
  - Si le fichier est verrouillé, écrit un fallback: mc_solaar_flow_ready_v2.mid

- karaoke_cli.py
  - Lance le karaoké depuis un fichier de paroles
  - Peut lancer et recaler un MIDI en parallèle

- build_flow_v2.py
  - Construit une version analysée du flow (grille 1-e-&-a)
  - Sortie: paroles_bilan_thermique_flow_v2_1e_and_a.txt

- vocalize_song.py
  - Génère une voix guide TTS depuis les paroles (français)
  - Sortie par défaut: vocal_guide.wav

## Fichiers de paroles utiles

- paroles_bilan_thermique_flow_accentue.txt
  - Version opérationnelle pour karaoké (accents de flow)

- paroles_bilan_thermique_flow_accentue_fr.txt
  - Variante accentuée en français UTF-8

- paroles_bilan_thermique_flow_v2_1e_and_a.txt
  - Version grille de subdivision (générée)

## Quick Start

### 1) Générer le beat

```powershell
python mc_beat.py
```

### 2) Lancer le karaoké complet (recommandé)

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --play-midi --midi mc_solaar_flow_ready.mid --bpm 88 --midi-lead 0.8 --end-sync-mode exact --render-mode scroll
```

## Comment la synchro MIDI / surbrillance fonctionne

La synchronisation n est pas pilotée par des événements temps réel envoyés par le lecteur MIDI. Le script calcule lui-même une timeline, lance le fichier `.mid`, attend `--midi-lead`, puis fait avancer la surbrillance du texte avec sa propre horloge interne.

### 1) Construction du timing de base du texte

Quand `--sync-midi` est activé, `karaoke_cli.py` n utilise plus un délai fixe par ligne. Il construit un profil de durée pour chaque ligne à partir de:

- du `--bpm`
- du nombre de mots dans la ligne
- de la ponctuation (virgules, points, etc.)
- d une petite pause de respiration en fin de ligne
- d un traitement spécial pour les titres / sections (`[Couplet]`, `## Intro`, etc.)

Concrètement:

- une ligne de section reçoit une durée plus longue et stable
- une ligne de rap reçoit une durée estimée selon un débit parlé
- plus une ligne contient de mots, plus elle dure longtemps
- la ponctuation ajoute quelques fractions de seconde

Ce timing de base sert de "forme" du flow: il définit quelles lignes doivent aller plus vite ou plus lentement les unes par rapport aux autres.

### 2) Lecture de la durée réelle du MIDI

Quand le karaoké est en mode auto avec `--sync-midi` et `--play-midi`, le script lit directement le fichier MIDI pour en déduire la durée totale.

Il ne demande pas au lecteur externe sa position courante. À la place, il:

- lit les chunks MIDI (`MThd`, `MTrk`)
- récupère le nombre de ticks par noire
- récupère les changements de tempo (`meta event 0x51`)
- récupère la fin des pistes (`meta event 0x2F`)
- convertit tous les ticks en secondes

Résultat: le script connaît la durée théorique totale du morceau en secondes, même si le lecteur MIDI utilisé est externe à Python.

### 3) Recalage global texte -> durée du morceau

Une fois la durée du texte estimée et la durée du MIDI connues, le script applique un coefficient d échelle à toutes les lignes.

Principe:

- il additionne toutes les durées estimées du texte
- il calcule le temps réellement disponible pour le texte
- il multiplie chaque durée de ligne par le même ratio

Le temps disponible dépend de trois paramètres:

- durée totale du MIDI
- `--midi-lead`: attente avant d afficher le premier mot après le lancement du MIDI
- `--end-sync-mode`

En mode `exact`:

- le texte est étiré ou compressé pour que la dernière surbrillance finisse en même temps que le morceau

En mode `tail-silence`:

- le script réserve une queue instrumentale finale
- la valeur réservée est `--tail-silence`
- la dernière ligne se termine donc avant la fin réelle du MIDI

La formule appliquée est essentiellement:

```text
temps_texte_disponible = durée_midi - midi_lead - queue_finale
ratio = temps_texte_disponible / somme_des_durées_estimées
durée_finale_ligne = durée_estimée_ligne * ratio
```

Important: comme un seul ratio global est appliqué, le script conserve les proportions entre les lignes. Si un vers était estimé comme deux fois plus long qu un autre, il reste deux fois plus long après recalage.

### 4) Point de départ réel de la synchronisation

À l exécution, l ordre est le suivant:

1. le script construit la timeline
2. il démarre sa propre horloge interne
3. il ouvre le fichier MIDI via l application associée au système
4. il attend `--midi-lead`
5. il commence la surbrillance

Cela signifie que `--midi-lead` compense:

- le léger délai d ouverture du lecteur MIDI
- l éventuelle intro instrumentale avant l entrée du texte
- le ressenti humain de calage que vous voulez obtenir

Si le texte démarre trop tôt, augmentez `--midi-lead`. S il démarre trop tard, diminuez cette valeur.

### 5) Comment la surbrillance mot à mot est produite

La surbrillance visible n est pas stockée dans le fichier de paroles. Elle est calculée au moment de l affichage.

Pour une ligne normale:

- la ligne est découpée en mots et espaces
- la durée finale de la ligne est divisée par le nombre de mots affichés
- chaque mot devient actif à son tour
- les mots déjà passés deviennent "dim"
- le mot courant devient "active"
- les mots suivants restent en style normal

Autrement dit, la synchro MIDI agit d abord au niveau de la ligne, puis cette durée est répartie uniformément mot par mot.

Exemple simplifié:

```text
Ligne: "J'isole le vide sous le béton"
Durée finale de ligne: 2.4 s
6 mots -> environ 0.4 s par mot
```

Le curseur de surbrillance avance donc par pas réguliers à l intérieur de la ligne.

### 6) Différence entre sync de ligne et sync de mot

Le point important est le suivant:

- le MIDI recale la durée totale et la durée de chaque ligne
- la surbrillance mot à mot à l intérieur d une ligne reste uniforme

Il n y a donc pas encore de placement syllabique ou mot par mot issu du MIDI lui-même. Le script ne lit pas les notes pour associer chaque mot à un événement musical précis. Il utilise un modèle simple mais robuste:

- estimation musicale globale
- recalage sur la durée réelle du morceau
- découpage régulier à l intérieur de chaque ligne

### 7) Cas où le MIDI ne recale pas vraiment le texte

Le recalage exact sur la durée du MIDI n a lieu que si ces conditions sont réunies:

- `--auto`
- `--sync-midi`
- `--play-midi`
- un fichier `--midi` lisible

Si `--sync-midi` est utilisé sans `--play-midi`, le script construit bien un flow basé sur le BPM, mais il ne recale pas les durées sur la longueur réelle d un fichier MIDI.

### 8) Limites actuelles du système

- Le lecteur MIDI est externe, donc Python ne reçoit pas sa position réelle en lecture.
- Si le lecteur met du temps à s ouvrir, il faut compenser avec `--midi-lead`.
- La surbrillance intra-ligne est uniforme par mot, pas alignée sur chaque note.
- Si le MIDI contient une structure très libre ou des tempos inhabituels, la durée globale sera correcte, mais l accent local peut demander un ajustement manuel des paroles ou du `--midi-lead`.

### 9) Réglage pratique recommandé

Pour caler proprement le texte:

1. Garder `--sync-midi` activé.
2. Utiliser le vrai fichier `--midi` qui sera joué.
3. Ajuster d abord `--midi-lead`.
4. Choisir `exact` si vous voulez que le dernier mot tombe avec la fin du morceau.
5. Choisir `tail-silence` si vous voulez laisser respirer l instrumental à la fin.

Commande de référence:

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --play-midi --midi mc_solaar_flow_ready.mid --bpm 88 --midi-lead 0.8 --end-sync-mode exact --render-mode scroll
```

## Commandes utiles

### Karaoké avec fin instrumentale (queue)

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --play-midi --midi mc_solaar_flow_ready.mid --bpm 88 --midi-lead 0.8 --end-sync-mode tail-silence --tail-silence 1.5 --render-mode scroll
```

### Karaoké sans musique (texte seul)

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --bpm 88 --render-mode scroll
```

### Mode frame (alternative)

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --play-midi --midi mc_solaar_flow_ready.mid --bpm 88 --midi-lead 0.8 --end-sync-mode exact --render-mode frame
```

### Générer la grille de flow V2

```powershell
python build_flow_v2.py
```

### Vocaliser les paroles (voix guide)

```powershell
python vocalize_song.py --input paroles_bilan_thermique_flow_accentue_fr.txt --output vocal_guide.wav --rate 160
```

### Lancer le karaoké avec la version EP2

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --play-midi --midi mc_solaar_flow_ready_ep2.mid --bpm 88 --midi-lead 0.8 --end-sync-mode exact --render-mode scroll
```

## Options de karaoke_cli.py

- lyrics_file
  - chemin du fichier de paroles (optionnel)
- --auto
  - défilement automatique
- --delay `float`
  - délai fixe entre lignes (si --sync-midi absent)
- --title `texte`
  - titre affiché
- --color / --no-color
  - active/désactive ANSI
- --sync-midi
  - construit un profil de timing rap/slam
- --bpm `float`
  - BPM de référence du profil de timing
- --midi `chemin`
  - fichier MIDI cible
- --play-midi
  - ouvre le MIDI en arrière-plan
- --midi-lead `float`
  - délai avant début texte après lancement MIDI
- --end-sync-mode exact|tail-silence
  - mode de calage de fin
- --tail-silence `float`
  - durée conservée de queue instrumentale
- --render-mode scroll|frame
  - scroll (sans scintillement) ou frame (fenêtre)

## Format des paroles

- Lignes non vides: affichées
- Sections reconnues:
  - lignes commençant par ## ou ###
  - lignes entre crochets: [Intro], [Couplet], [Refrain]
- Marqueurs de respiration possibles dans le texte: //

## Dépannage

### Le script karaoké se termine avec code 1

Cela arrive souvent quand:

- le fichier de paroles passé en argument n existe pas
- le chemin MIDI est incorrect

Vérifiez d abord:

```powershell
Test-Path .\paroles_bilan_thermique_flow_accentue.txt
Test-Path .\mc_solaar_flow_ready.mid
```

### Le MIDI ne se lance pas

- Associer une application de lecture aux fichiers .mid
- Ouvrir manuellement le fichier .mid pour vérifier que l association fonctionne

### Le texte est mal calé

- Ajuster --midi-lead (ex: 0.6, 0.8, 1.0)
- Ajuster --bpm
- Choisir exact ou tail-silence selon le rendu voulu

### Le terminal affiche mal les accents

Le script force UTF-8 au démarrage, mais si besoin:

```powershell
chcp 65001
```

## Notes

- Certains fichiers historiques (ex: generate.py, anciens .mid) peuvent rester dans le repo.
- Le workflow recommandé et maintenu est basé sur:
  - mc_beat.py
  - karaoke_cli.py
  - build_flow_v2.py
  - vocalize_song.py
