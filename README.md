# Objectif: Nouvelle Terre (nom à chercher)

## Instructions d'installation (Linux)

- Premièrement, assurez-vous de posséder les dépendances nécéssaires: `OpenGL`, `cmake`, `make` et `gcc` (ou `clang`).
- Ensuite, lancez `./build_linux.sh` pour compiler raylib et ses bindings python.
- Vous pouvez lancer le jeu avec `python3 main.py`!

## Instruction d'installation (Windows)

TODO

## Pourquoi est-il nécessaire de compiler raylib?

La librarie que l'on utilise (pour faire le rendu, les sons, charger les modèles, etc...), [raylib](https://www.raylib.com),
ne permet pas de configurer la distance d'affichage pendant l'éxecution, seulement [au moment de la compilation](https://github.com/raysan5/raylib/blob/35252fceefdeb7b0920d9c1513efb4b5c05633dc/src/config.h#L112-L113).  
Or, pour créer une impression de distance, nouse avons besoin de voir plus loin que les 1000 mètres stipulés par défaut.

Ainsi, nous devons modifier la configuration dans raylib (chose faîte dans un [fork](https://github.com/NSAILLE-POWER5/raylib/tree/farplane)), compiler la librarie,
et reconstruire les [bindings python](https://github.com/electronstudio/raylib-python-cffi) nous permettant d'y accéder.  
C'est ce dont s'occupent les scripts `build_linux.sh` et `build_windows.ps`.
