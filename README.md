# Objectif: Nouvelle Terre (nom à chercher)

## Instructions d'installation (Linux)

- Premièrement, assurez-vous de posséder les dépendances nécéssaires: `OpenGL`, `cmake`, `make` et `gcc` (ou `clang`).
- Ensuite, lancez `./build_linux.sh` pour compiler raylib et ses bindings python.
- Vous pouvez lancer le jeu avec `python3 source/main.py`!

## Instruction d'installation (Windows)

- Assurez-vous d'avoir un version de python superieur a 3.12, (version recommandée : [3.12.2](https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tar.xz))
- Lancer l'executable `setup.bat`
- Si `source/setup.bat` ne se lance pas executer les commandes suivantes dans votre terminal.
```powershell
pip install cffi
```
- puis:
```powershell
pip3 install source/raylib-5.0.0.1-cp312-cp312-win_amd64.whl --no-cache-dir --upgrade --force-reinstall
```
- Enfin, lancez le jeu avec `source/python main.py` et amusez vous bien.

## Pourquoi est-il nécessaire de compiler raylib?

La librarie que l'on utilise (pour faire le rendu, les sons, charger les modèles, etc...), [raylib](https://www.raylib.com),
ne permet pas de configurer la distance d'affichage pendant l'éxecution, seulement [au moment de la compilation](https://github.com/raysan5/raylib/blob/35252fceefdeb7b0920d9c1513efb4b5c05633dc/src/config.h#L112-L113).  
Or, pour créer une impression de distance, nouse avons besoin de voir plus loin que les 1000 mètres stipulés par défaut.

Ainsi, nous devons modifier la configuration dans raylib (chose faîte dans un [fork](https://github.com/NSAILLE-POWER5/raylib/tree/farplane)), compiler la librarie,
et reconstruire les [bindings python](https://github.com/electronstudio/raylib-python-cffi) nous permettant d'y accéder.  
C'est ce dont s'occupent les scripts `build_linux.sh` et `build_windows.ps`.
