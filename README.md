# ASC-ODE

ASC-ODE is a C++20 library for solving ordinary differential equations.
Read the [documentation](https://tuwien-asc.github.io/ASC-ODE/) for the
available methods, build instructions, and numerical experiments.

## Preview the documentation

Create a local Python environment and install Jupyter Book 2. On PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U "jupyter-book>=2"
cd docs
..\.venv\Scripts\jupyter-book.exe start
```

On macOS or Linux:

```sh
python -m venv .venv
.venv/bin/python -m pip install -U "jupyter-book>=2"
cd docs
../.venv/bin/jupyter-book start
```

The `.venv/` directory is ignored by Git. The GitHub Actions workflow builds
and publishes the documentation to GitHub Pages on pushes to `main`. Enable
GitHub Actions and select **GitHub Actions** as the Pages build source in the
repository settings.
