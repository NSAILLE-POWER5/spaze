@echo off
echo Installation de la version modifiée de raylib sur Windows...

pip3 uninstall raylib

git clone --recurse-submodules --shallow-submodules https://github.com/electronstudio/raylib-python-cffi

rd /s /q raylib-c
git clone https://github.com/NSAILLE-POWER5/raylib raylib-c

copy raylib-python-cffi\version.py raylib-python-cffi\raylib\
copy raylib-c\src\raylib.h raylib-python-cffi\raylib\


pip3 install cffi
pip3 install wheel
python setup.py bdist_wheel

if %errorlevel% neq 0 (
    echo Erreurs pendant la construction. Télécharger les outils de construction pour Visual Studio et réessayer.
    pause
    exit /b %errorlevel%
)

pip3 install dist\raylib-<UN NOM CHELOU>.whl

echo Lancement de spaze...

echo Installation terminée.
pause