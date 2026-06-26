# RapMusic Karaoke CLI

Projet Python pour:
- générer un beat MIDI boom-bap flow-ready
- afficher des paroles en karaoké terminal (mot à mot)
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
  - Peut ouvrir et caler un MIDI en parallèle

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
- --delay <float>
  - délai fixe entre lignes (si --sync-midi absent)
- --title <texte>
  - titre affiché
- --color / --no-color
  - active/désactive ANSI
- --sync-midi
  - construit un profil de timing rap/slam
- --bpm <float>
  - BPM de référence du profil de timing
- --midi <chemin>
  - fichier MIDI cible
- --play-midi
  - ouvre le MIDI en arrière-plan
- --midi-lead <float>
  - délai avant début texte après lancement MIDI
- --end-sync-mode exact|tail-silence
  - mode de calage de fin
- --tail-silence <float>
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

Ça arrive souvent quand:
- le fichier de paroles passé en argument n existe pas
- le chemin MIDI est incorrect

Vérifier d abord:

```powershell
Test-Path .\paroles_bilan_thermique_flow_accentue.txt
Test-Path .\mc_solaar_flow_ready.mid
```

### Le MIDI ne se lance pas

- Associer une application de lecture aux fichiers .mid
- Ouvrir manuellement le fichier .mid pour vérifier

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
