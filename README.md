# RTD Modelisation

Application Python pour la simuler et modéliser des données sur la digestion dans un système digestif InVitro (IViDiS)  

## Prérequis

Avant de commencer, merci de vérifier que vous avez installé ces logiciels : 

* Python 3.14 ou plus récent
* Git
* Un IDE pour python (VScode/Spyder/etc.)

## Clonez le répertoire

1. Rendez-vous dans un répertoire qui sera dédié à votre projet sur votre PC.
2. Clique droit sur votre dossier et cliquez sur 'ouvrir dans le terminal'
3. Copier l'url du répertoire GitHub (sur GitHub appuyez sur Code puis copiez l'adresse https)
4. Clonez le répertoire sur votre espace personnel : 

```bash
git clone <repository-url>
cd RTD_Modelisation
```

## Ouvrir le projet 

### VS Code :

1. Cliquez sur file en haut à gauche de votre interface vscode
2. Choississez "Open Folder"
3. Récupérez le dossier du projet et appuyez sur "Select Folder"


### Spyder : 

1. Cliquez sur l'onglet "Projets" sur le menu de votre interface Spyder
2. Choississez "Ouvrir un projet"
3. Récupérez le dossier du projet et appuyez sur "Sélectionnez un dossier"

## Créez un environnement virtuel (VS code) 

Windows:

```bash
py -m venv .venv
```

## Activez l'environnement virtuel (VS code)

**PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**Command Prompt (CMD)**

```cmd
.venv\Scripts\activate.bat
```

Une fois activité le terminal devrait afficher :

```text
(.venv)
```

## Installer les dépendances requises

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## lancer l'application

* Depuis votre IDE :
    - Run Python application
 
* En commande bash :
```bash
python src/main.py
```

## Structure du projet 

TODO

## Mettre à jour les dépendances

Si une nouvelle librairie est installée pour le projet, mettre à jour la liste des prérequis :

```bash
pip freeze > requirements.txt
```
commit le fichier `requirements.txt` pour que les autres utilisateurs aient le même environnement.

## Workflow git recommandé 

1. Pull les derniers changement de la branche `main`.
2. Créez une nouvelle branche de développement pour les prochaines implémentation ou la résolution des bug

Si une branche dev n'est pas déjà créée :
```bash
git checkout main
git pull origin main
git checkout -b dev
```

Si la branche dev a déjà été créée plus tôt :
```bash
git checkout main
git pull origin main
git checkout dev
```

3. Développer et tester les fonctionnalités
4. Commit les changements régulièrement avec un message de commit cohérent

```bash
git add .
git commit -m "Implement feature X"
```

5. Push votre branche sur Github

```bash
git push -u origin dev
```
7. Ouvrir une Pull Request depuis votre branche de développement vers la branche `main` dans Github 
8. Vérifiez les changements et assurez-vous qu'il n'y a pas de conflits. Si nécessaire, ajoutez des commentaires.
9. Merger la Pull request 
10. Retournez à l'étape 1