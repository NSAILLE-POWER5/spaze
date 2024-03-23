#!/usr/bin/env bash

# Exit on error
set -e

# Prepare directory
mkdir -p raylib
cd raylib

# Get modified raylib repo
if [ -d raylib ]; then
	echo "dépôt raylib a déjà été cloné"
else
	git clone -b farplane --single-branch --depth=1 https://github.com/NSAILLE-POWER5/raylib
fi

# Create install directory
mkdir -p out

# Build raylib
cd raylib

mkdir -p build
cd build

cmake -DCMAKE_BUILD_TYPE=Relase -DWITH_PIC=ON -DBUILD_EXAMPLES=OFF -DUSE_EXTERNAL_GLFW=OFF -DCMAKE_INSTALL_PREFIX=../../out ..
make -j6
make install

cd ../..

# Copy GLFW includes to install directory (not done by cmake automatically)
cp -r raylib/src/external/glfw/include/GLFW/ out/include/

# Install raylib python ffi

# Give the install directory to pkgconfig (which is used by raylib python in its build)

# --break-system-packages is necessary in arch derivatives
# use --no-cache-dir in case the raylib package was already downloaded (with prebuilt raylib binaries)
PKG_CONFIG_PATH=$(realpath out/lib/pkgconfig) pip3 install raylib --no-binary raylib --upgrade --force-reinstall --no-cache-dir --break-system-packages 
