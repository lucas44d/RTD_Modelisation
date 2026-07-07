# RTD Modelisation

Python application for data processing, modelling and visualization.

## Requirements

Before starting, make sure the following software is installed:

* Python 3.14 or newer
* Git
* Visual Studio Code (recommended)

## Clone the repository

```bash
git clone <repository-url>
cd RTD_Modelisation
```

## Create a virtual environment

Windows:

```bash
py -m venv .venv
```

## Activate the virtual environment

**PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**Command Prompt (CMD)**

```cmd
.venv\Scripts\activate.bat
```

Once activated, the terminal should display:

```text
(.venv)
```

## Install the required dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the application

```bash
python src/main.py
```

## Project structure

TODO

## Updating dependencies

If a new library is added to the project, update the dependency list with:

```bash
pip freeze > requirements.txt
```

Commit the updated `requirements.txt` so that other users can install the same environment.

## Recommended Git workflow

1. Pull the latest changes from the `main` branch.
2. Create a new development branch for your feature or bug fix.

```bash
git checkout main
git pull
git checkout -b feature/my-feature
```

3. Activate the virtual environment.
4. Develop and test your changes.
5. Commit your work regularly with meaningful commit messages.

```bash
git add .
git commit -m "Implement feature X"
```

6. Push your branch to GitHub.

```bash
git push -u origin feature/my-feature
```

7. Open a Pull Request (Merge Request) from your development branch into `main`.
8. Review the changes, resolve any comments if necessary, and merge the Pull Request.
9. Delete the development branch once it has been merged.
