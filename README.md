# VidIO

Application de capture et visualisation vidéo/audio en temps réel utilisant GTK3 et GStreamer.

## Description

VidIO est une application Linux qui permet de capturer et afficher des flux vidéo et audio depuis des périphériques USB (comme des caméras de capture). Elle propose une interface de sélection des périphériques avec prévisualisation en temps réel avant d'ouvrir la fenêtre principale de visualisation.

### Fonctionnalités

- 🎥 Sélection interactive des sources vidéo (périphériques V4L2)
- 🔊 Sélection interactive des sources audio (périphériques PulseAudio)
- 👀 Prévisualisation vidéo et audio avant validation
- 🎨 Ajustement du contraste vidéo
- 🔉 Contrôle du volume audio (50% par défaut)
- 📺 Fenêtre de visualisation adaptative à la résolution source

## Installation sur Arch Linux

### Prérequis système

Installez les dépendances nécessaires via pacman :

```bash
sudo pacman -S python-gobject gtk3 gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad v4l-utils
```

### Détail des paquets

- `python-gobject` : Bindings Python pour GObject/GTK
- `gtk3` : Bibliothèque d'interface graphique GTK 3
- `gstreamer` : Framework multimédia
- `gst-plugins-base` : Plugins GStreamer de base
- `gst-plugins-good` : Plugins GStreamer de qualité
- `gst-plugins-bad` : Plugins GStreamer expérimentaux (nécessaire pour certains codecs)
- `v4l-utils` : Utilitaires Video4Linux pour la détection des périphériques

### Installation de l'application

1. Clonez ou téléchargez le projet :
```bash
git clone https://github.com/Legambey/VidIO.git
cd VidIO
```

2. Assurez-vous que le script est exécutable :
```bash
chmod +x vidio.py
```

## Utilisation

### Lancement

Exécutez simplement le script Python :

```bash
python vidio.py
```

ou, si vous l'avez rendu exécutable :

```bash
./vidio.py
```

### Workflow

1. **Sélection des périphériques** : Une boîte de dialogue s'ouvre au démarrage
   - Sélectionnez votre source vidéo (ex: `/dev/video0`)
   - Sélectionnez votre source audio
   - La prévisualisation s'affiche automatiquement

2. **Validation** : Cliquez sur "Valider" pour ouvrir la fenêtre principale

3. **Visualisation** : La fenêtre principale affiche le flux vidéo avec l'audio en temps réel

### Configuration par défaut

Le périphérique audio par défaut est configuré dans le code :
```python
DEFAULT_AUDIO_DEVICE = "alsa_input.usb-ARKMICRO_USB2.0_PC_CAMERA-02.mono-fallback"
```

Vous pouvez modifier cette valeur selon votre configuration.

## Dépannage

### Problème : Aucun périphérique vidéo détecté

Vérifiez vos périphériques V4L2 :
```bash
v4l2-ctl --list-devices
```

### Problème : Aucun son

Listez vos sources audio PulseAudio :
```bash
pactl list sources short
```

## Utilisation typique

Cette application est idéale pour :
- Capturer des signaux vidéo depuis des consoles de jeu rétro (GameCube, etc.)
- Visualiser des flux de caméras USB
- Faire de la capture vidéo en temps réel avec prévisualisation

## Licence

### à remplir

## Auteur

- Legambey