# ASC-ODE

ASC-ODE is a C++20 library for solving ordinary differential equations of the
form `y' = f(y)`. It provides explicit and implicit time-stepping methods and
example models for a mass–spring oscillator and an RC circuit.

## Time-stepping methods

The library provides four methods:

- **Explicit Euler**, a first-order explicit method.
- **Improved Euler**, implemented as the explicit midpoint Runge–Kutta method
  and therefore second order.
- **Implicit Euler**, a first-order method whose nonlinear step is solved with
  Newton's method.
- **Crank–Nicolson**, implemented as the trapezoidal rule and second order.
  Its nonlinear step also uses Newton's method.

The [Euler and model experiments](exercises_euler.md) explain these formulas,
compare their accuracy and stability, and document the reproduction commands.

## Build and run

The build requires CMake 3.20 or newer, a C++20 compiler, Python, and the
`pybind11` Python package. The `nanoblas` dependency is a Git submodule.
From a clone of the repository, initialize the submodule and install
`pybind11` in the Python environment you will use for CMake:

```sh
git submodule update --init
python -m pip install pybind11
cmake -S . -B build -DPython_EXECUTABLE="$(python -c 'import sys; print(sys.executable)')" -DNANOBLAS_BUILD_DEMOS=OFF -DBUILD_TESTING=ON
cmake --build build
ctest --test-dir build --output-on-failure
```

On Windows PowerShell, use this CMake configuration command instead of the
Unix-style command above:

```powershell
$python = (python -c "import sys; print(sys.executable)")
cmake -S . -B build "-DPython_EXECUTABLE=$python" -DNANOBLAS_BUILD_DEMOS=OFF -DBUILD_TESTING=ON
```

The tests use Catch2 3. CMake uses an installed copy if available and otherwise
downloads the version pinned by the project. See the experiment page for
commands that run the mass–spring and RC simulations and generate their plots.

## Documentation

This book is built with Jupyter Book 2. Follow the README to create and install
the ignored `.venv` environment, activate it, then start the preview from
`docs/`:

```text
jupyter-book start
```

To build the HTML book locally, run `jupyter-book build --html --strict` from
`docs/`. The GitHub Actions workflow builds and publishes the book to GitHub
Pages after pushes to `main`.
