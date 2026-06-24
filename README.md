# RapMusic Karaoke CLI

Application Python pour generer une instru MIDI rap/slam et afficher des paroles en mode karaoke dans le terminal.

## Quick Start

1) Generer le MIDI :

```powershell
python3.13.exe generate.py
```

2) Lancer le karaoke avec fin exacte (texte et musique ensemble) :

```powershell
python3.13.exe karaoke_cli.py --auto --sync-midi --play-midi --midi instru_piano_rap.mid --midi-lead 0.8 --end-sync-mode exact
```

3) Lancer le karaoke avec 1.5s de queue instrumentale :

```powershell
python3.13.exe karaoke_cli.py --auto --sync-midi --play-midi --midi instru_piano_rap.mid --midi-lead 0.8 --end-sync-mode tail-silence --tail-silence 1.5
```

Le projet contient deux scripts principaux :
- generate.py : genere l accompagnement MIDI
- karaoke_cli.py : affiche les paroles avec un defilement manuel ou automatique

## 1) Prerequis

- Windows (ou autre OS compatible Python)
- Python 3.13 (ou version recente)
- Un lecteur/app associee aux fichiers .mid

Option recommandee (si presente dans le projet) :
- environnement virtuel local .venv

## 2) Structure utile

- paroles_le_revers_du_fond_de_court.txt : paroles par defaut
- instru_piano_rap.mid : MIDI principal genere
- temp/instru_piano_rap_fort.mid : fallback si le fichier principal est verrouille
- generate.py : generation de l instru
- karaoke_cli.py : lecteur karaoke terminal

## 3) Generer le MIDI

Commande simple :

```powershell
python3.13.exe generate.py
```

Resultat attendu :
- generation de instru_piano_rap.mid
- si verrouillage du fichier cible, generation d une copie dans temp/instru_piano_rap_fort.mid

## 4) Lancer le karaoke

Exemple complet (auto + synchro MIDI + lecture MIDI) :

```powershell
python3.13.exe karaoke_cli.py --auto --sync-midi --play-midi --midi instru_piano_rap.mid --midi-lead 0.8
```

Exemple sans lecture MIDI (texte seul) :

```powershell
python3.13.exe karaoke_cli.py --auto --sync-midi
```

Exemple en mode manuel (Entree pour avancer) :

```powershell
python3.13.exe karaoke_cli.py
```

## 5) Synchronisation texte/musique

Le script peut maintenant caler la fin du texte sur la fin du MIDI.

Deux modes :
- exact : texte et musique finissent en meme temps
- tail-silence : la musique continue un peu apres la derniere ligne

Options :
- --end-sync-mode exact|tail-silence
- --tail-silence <secondes> (defaut 1.5)

Exemples :

1. Fin exacte :

```powershell
python3.13.exe karaoke_cli.py --auto --sync-midi --play-midi --midi instru_piano_rap.mid --midi-lead 0.8 --end-sync-mode exact
```

2. Garder 1.5s de queue instrumentale :

```powershell
python3.13.exe karaoke_cli.py --auto --sync-midi --play-midi --midi instru_piano_rap.mid --midi-lead 0.8 --end-sync-mode tail-silence --tail-silence 1.5
```

## 6) Toutes les options CLI de karaoke_cli.py

- lyrics_file
  - chemin du fichier de paroles (optionnel)

- --auto
  - defilement automatique

- --delay <float>
  - delai entre lignes en mode auto sans synchro MIDI

- --title <texte>
  - titre affiche en haut

- --color / --no-color
  - active/desactive les couleurs ANSI

- --sync-midi
  - construit un profil temporel rap/slam pour les lignes

- --bpm <float>
  - BPM de reference pour le profil de timing

- --midi <chemin>
  - fichier MIDI a ouvrir en fond

- --play-midi
  - lance le MIDI pendant le karaoke

- --midi-lead <float>
  - attente apres lancement du MIDI avant debut texte

- --end-sync-mode exact|tail-silence
  - mode de calage de fin

- --tail-silence <float>
  - duree de queue instrumentale souhaitee en mode tail-silence

## 7) Format recommande pour les paroles

- Les lignes non vides sont affichees
- Les sections commencent par ## ou ###
- Les marqueurs comme [Intro], [Couplet], [Refrain] sont supportes
- Le marqueur / dans les lignes peut servir de repere de flow

## 8) Comment le MIDI est resolu

Quand un fichier MIDI est demande, le script peut choisir entre :
- le fichier passe via --midi
- le fallback temp/instru_piano_rap_fort.mid

S il trouve plusieurs candidats existants, il prend le plus recent.

## 9) Depannage

1. Rien ne se joue cote musique
- verifier qu un lecteur MIDI est associe aux fichiers .mid
- tester l ouverture manuelle du fichier MIDI

2. Le texte va trop vite ou trop lentement
- utiliser --sync-midi avec --play-midi
- ajuster --midi-lead
- choisir le mode de fin adapte avec --end-sync-mode

3. Le MIDI principal est verrouille
- relancer generate.py
- utiliser le fichier de fallback dans temp/

4. Les couleurs ne s affichent pas correctement
- utiliser --no-color

## 10) Workflow conseille

1. Regenerer la prod

```powershell
python3.13.exe generate.py
```

2. Lancer le karaoke cale sur la musique

```powershell
python3.13.exe karaoke_cli.py --auto --sync-midi --play-midi --midi instru_piano_rap.mid --midi-lead 0.8 --end-sync-mode exact
```

3. Variante avec fin instrumentale

```powershell
python3.13.exe karaoke_cli.py --auto --sync-midi --play-midi --midi instru_piano_rap.mid --midi-lead 0.8 --end-sync-mode tail-silence --tail-silence 1.5
```
