# Documentation complète

# main.py
C’est le fichier de la structure du projet, celui qui regroupe tous les autres et que l’on doit lancer pour avoir accès au jeu.

## Fonction `get_viewed_planet(player: Player, sys: System) -> Planet | None`
- Renvoie la planète que le joueur est actuellement entrain de regarder

## Fonction `main()`
- Fonction principale du programme. Initialise la fenêtre de jeu, charge les textures et les shaders, met à jour les états du système et du joueur, gère les entrées et le rendu graphique.
- ## Fonction `collision_check()`
	- Vérifie s'il y a une collision entre le joueur et une planète du système. Renvoie `True` s'il n'y a pas de collision, sinon `False`.

# icosphere.py
Gère la génération des sphères.

## Classe `SimpleMesh`
- Cette classe représente un maillage simple composé de points et de faces. Elle permet de créer un maillage raylib à partir des données fournies et est utilisée pour générer une icosaèdre et une icosphère, éléments essentiels dans la création d'un environnement spatial dans le jeu.
- ## Méthode `create_mesh(self) -> Mesh`
    - Transforme le maillage en objet raylib

## Fonction `gen_icosahedron()`
- Génère un maillage d'icosaèdre initial avec des points et des faces prédéfinis, qui servira de base pour la création de l'icosphère.
## Fonction `midpoint(a: Vector3, b: Vector3) -> Vector3`
- Calcule le point médian entre deux autres points, utilisé lors de la subdivision des triangles pour la création de l'icosphère.
## Fonction `subdivide(ico: SimpleMesh)`
- Subdivise chaque triangle de l'icosaèdre en 4 nouveaux triangles.
## Fonction `gen_icosphere(num: int) -> SimpleMesh`
- Crée une icosphère avec un nombre donné de subdivisions, permettant d'obtenir une sphère plus lisse pour représenter les planètes ou autres objets spatiaux dans le jeu.

# system.py
S’occupe de la génération des astres dans le jeu ainsi que de leur taille et leur organisation dans le système solaire. 

## Classe `Planet`
- Représente une entité planétaire dans le système solaire.
- ## Méthode `orbit(self, G, dt)`
    - Simule l'orbite de la planète autour de son centre orbital.
- ## Méthode `compute_transform(self)`
    - Calcule la matrice de transformation de la planète.
- ## Méthode `gen_layer(self)`
    - Génère les couches de couleur de la planète en fonction de ses caractéristiques.
  
## Classe `System`
- Modélise un système solaire composé de plusieurs planètes.
- ## Méthode `add(self, planet)`
    - Ajoute une nouvelle planète au système solaire.
- ## Méthode `planets(self)`
    - Renvoie un itérateur sur les planètes du système (sans inclure le soleil).
- ## Méthode `update(self, G, dt)`
    - Met à jour le système solaire à sa prochaine position.

## Classe `NewSystem`
- ## Méthode `new_sys(self, G: float) -> System`
    - Créé un nouveau système solaire aléatoire

# map.py
S'occupe de dessiner la carte du système solaire

## Fonction `copy_state(system: System, player: Player) -> tuple[System, Player]`
- Crée une copie de l'état du système et du joueur, avec toutes les informations de texture/graphiques partagées, pour permettre de les simuler à une vitesse différente de la simulation en temps réel.

## Classe `Map`
- ## Méthode `toggle(self)`
    - Active/Désactive la carte
- ## Méthode `update(self, G: float, player: Player, sys: System)`
    - Simule la trajectoire du joueur dans les prochaines étapes
    - Met à jour la caméra isometrique de la carte
- ## Méthode `draw(self, player: Player, sys: System, sphere_mesh: Mesh, wormhole_mat: WormholeMaterial)`
    - Dessine la carte

# sky.py
S'occope de dessiner les étoiles

## Classe `Sky`
- ## Fonction `draw(self)`
    - Dessine les étoiles

# player.py

## Classe `Player` :
- Représente le joueur dans le jeu, avec sa position, sa vitesse, sa caméra et ses rotations.
- ## Méthode `handle_mouse_input(self, dt: float)` :
    - Met à jour l'angle de vue du joueur en fonction des mouvements de la souris.
- ## Méthode `handle_keyboard_input(self)` :
    - Accélère le vaisseau du joueur en fonction des entrées clavier.
- ## Méthode `apply_gravity(self, G: float, dt: float, bodies: Iterable[Planet])` :
    - Applique la force gravitationnelle du champ de gravité des planètes sur le joueur.
- ## Méthode `integrate(self, dt: float)` :
    - Applique la vélocité à la position du joueur.
- ## Méthode `sync_camera(self)` :
    - Synchronise la caméra avec les transformations du joueur.

# cockpit.py

## Classe `Cockpit`:
- S'occupe de dessiner le cockpit du vaisseau
- ## Méthode `draw(self, player: Player, sys: System, selected: Planet | None)`
    - Dessine le cockpit et les informations de la planète selectionnée si elle a été scannée

## Fonction `rescale(cockpit_rec: Rectangle) -> Rectangle`
- Redimensionne un rectangle pris dans l'image originelle du cockpit à la taille de l'écran

## Fonction `draw_text_centered(text: str, rect: Rectangle, font_size: int, color: Color)`
- Dessine du texte au centre du rectangle donné

# noise.py
S'occupe de générer le bruit simplex utilisé par les planètes

## Classe `NoiseShader`
- Shader utilisé pour la génération du bruit simplex

## Fonction `generate_noise(size: tuple[int, int], scale: Vector3, pos: Vector2, octaves: int, frequency: float, amplitude: float, warp: float, ridge: bool, invert: bool) -> RenderTexture:`
- Génère une texture (= sur la carte graphique) de bruit simplex avec les paramètres donnés

# utils.py
Contient des fonctions et des classes utilitaires pour diverses opérations mathématiques et de manipulation de données.

- `Quat`: Cette classe représente un quaternion pour la rotation dans l'espace tridimensionnel.
- `vec3_zero`: Cette fonction crée un vecteur tridimensionnel initialisé à zéro.
- `print_vec3`: Cette fonction affiche un vecteur dans la console
- `get_projected_sphere_radius`: Cette fonction calcule le rayon projeté d'une sphère sur l'écran en fonction de sa position et de sa taille, afin de gérer la perspective dans le rendu graphique.
- `randf`: Cette fonction génère un nombre aléatoire à virgule flottante dans l'intervalle [0, 1].
- `randfr`: Cette fonction génère un nombre aléatoire à virgule flottante dans l'intervalle donné.
- `draw_rectangle_tex_coords`: Cette fonction dessine un rectangle aux coordonées données, en ajoutant aussi les coordonées de texture

# colors.py
Contient des définitions de couleurs (celles inclues dans raylib n'utilisent pas la classe couleur ce qui amène le LSP à déclarer des erreurs)

# shaders.py
Contient toutes les classes chargeant les shaders

## Classe `PlanetMaterial`
Le shader utilisé par les planètes

## Classe `SunMaterial`
Le shader utilisé par le soleil

## Classe `WormholeMaterial`
Le shader utilisé par le trou de ver

## Classe `SkyMaterial`
Le shader utilisé par les étoiles

## Classe `WormholeEffect`
Le shader utilisé lors du voyage dans le trou de vers

# assets/
Contient les images et musiques que nous avons intégré au jeu

# shaders/
Contient tous les shaders utilisés par le jeu
