# RapMusic Karaoke CLI

Projet Python pour:
- generer un beat MIDI boom-bap flow-ready
- afficher des paroles en karaoke terminal (mot a mot)
- synchroniser la duree du texte avec la musique MIDI

Etat: documentation mise a jour pour les scripts actuels.

## Fonctionnalites

- Generation d un beat principal via mc_beat.py
- Karaoke CLI avec:
  - mode scroll (sans scintillement)
  - mode frame (fenetre glissante)
  - surbrillance mot a mot
- Synchronisation texte/midi:
  - fin exacte (exact)
  - fin instrumentale conservee (tail-silence)
- Support UTF-8 Windows pour afficher accents francais (e, e, a, c, oe)
- Outil de grille de flow V2 (1-e-&-a) via build_flow_v2.py

## Prerequis

- Python 3.10+
- Windows, macOS ou Linux
- Un lecteur associe aux fichiers .mid

Dependances Python (requirements.txt):
- mido==1.3.3
- music21==10.5.0

## Installation

### Option recommande (venv)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Scripts principaux

- mc_beat.py
  - Genere le beat principal: mc_solaar_flow_ready.mid
  - Si le fichier est verrouille, ecrit un fallback: mc_solaar_flow_ready_v2.mid

- karaoke_cli.py
  - Lance le karaoke depuis un fichier de paroles
  - Peut ouvrir et caler un MIDI en parallele

- build_flow_v2.py
  - Construit une version analysee du flow (grille 1-e-&-a)
  - Sortie: paroles_bilan_thermique_flow_v2_1e_and_a.txt

## Fichiers de paroles utiles

- paroles_bilan_thermique_flow_accentue.txt
  - Version operationnelle pour karaoke (accents de flow)

- paroles_bilan_thermique_flow_accentue_fr.txt
  - Variante accentuee en francais UTF-8

- paroles_bilan_thermique_flow_v2_1e_and_a.txt
  - Version grille de subdivision (generee)

## Quick Start

### 1) Generer le beat

```powershell
python mc_beat.py
```

### 2) Lancer le karaoke complet (recommande)

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --play-midi --midi mc_solaar_flow_ready.mid --bpm 88 --midi-lead 0.8 --end-sync-mode exact --render-mode scroll
```

## Commandes utiles

### Karaoke avec fin instrumentale (queue)

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --play-midi --midi mc_solaar_flow_ready.mid --bpm 88 --midi-lead 0.8 --end-sync-mode tail-silence --tail-silence 1.5 --render-mode scroll
```

### Karaoke sans musique (texte seul)

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --bpm 88 --render-mode scroll
```

### Mode frame (alternative)

```powershell
python karaoke_cli.py paroles_bilan_thermique_flow_accentue.txt --auto --sync-midi --play-midi --midi mc_solaar_flow_ready.mid --bpm 88 --midi-lead 0.8 --end-sync-mode exact --render-mode frame
```

### Generer la grille de flow V2

```powershell
python build_flow_v2.py
```

## Options karaoke_cli.py

- lyrics_file
  - chemin du fichier de paroles (optionnel)
- --auto
  - defilement automatique
- --delay <float>
  - delai fixe entre lignes (si --sync-midi absent)
- --title <texte>
  - titre affiche
- --color / --no-color
  - active/desactive ANSI
- --sync-midi
  - construit un profil de timing rap/slam
- --bpm <float>
  - BPM de reference du profil de timing
- --midi <chemin>
  - fichier MIDI cible
- --play-midi
  - ouvre le MIDI en arriere-plan
- --midi-lead <float>
  - delai avant debut texte apres lancement MIDI
- --end-sync-mode exact|tail-silence
  - mode de calage de fin
- --tail-silence <float>
  - duree conservee de queue instrumentale
- --render-mode scroll|frame
  - scroll (sans scintillement) ou frame (fenetre)

## Format des paroles

- Lignes non vides: affichees
- Sections reconnues:
  - lignes commencant par ## ou ###
  - lignes entre crochets: [Intro], [Couplet], [Refrain]
- Marqueurs de respiration possibles dans le texte: //

## Depannage

### Le script karaoke se termine avec code 1

Ca arrive souvent quand:
- le fichier de paroles passe en argument n existe pas
- le chemin MIDI est incorrect

Verifier d abord:

```powershell
Test-Path .\paroles_bilan_thermique_flow_accentue.txt
Test-Path .\mc_solaar_flow_ready.mid
```

### Le MIDI ne se lance pas

- Associer une application de lecture aux fichiers .mid
- Ouvrir manuellement le fichier .mid pour verifier

### Le texte est mal cale

- Ajuster --midi-lead (ex: 0.6, 0.8, 1.0)
- Ajuster --bpm
- Choisir exact ou tail-silence selon le rendu voulu

### Le terminal affiche mal les accents

Le script force UTF-8 au demarrage, mais si besoin:

```powershell
chcp 65001
```

## Notes

- Certains fichiers historiques (ex: generate.py, anciens .mid) peuvent rester dans le repo.
- Le workflow recommande et maintenu est base sur:
  - mc_beat.py
  - karaoke_cli.py
  - build_flow_v2.py
