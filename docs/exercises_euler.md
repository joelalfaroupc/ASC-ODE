# Euler methods and ODE experiments

This page documents the explicit and implicit Euler implementations based on
the course exercises, then compares them with Improved Euler and
Crank–Nicolson. Improved Euler in ASC-ODE is the **explicit midpoint method**,
not Heun's method.

## Methods

For an autonomous ODE `y' = f(y)`, `src/timestepper.hpp` implements:

- **Explicit Euler:** `y_next = y + h*f(y)`.
- **Improved Euler (explicit midpoint):**
  `y_mid = y + h/2*f(y)`, then `y_next = y + h*f(y_mid)`.
- **Implicit Euler:** Newton's method solves
  `y_next - y - h*f(y_next) = 0`.
- **Crank–Nicolson (trapezoidal rule):** Newton's method solves
  `y_next - y - h/2*(f(y) + f(y_next)) = 0`.

Crank–Nicolson here is the trapezoidal rule, not the implicit midpoint rule.
The formulas differ for nonlinear functions; the test suite checks this
distinction. The implicit methods reuse their composed nonlinear functions
and update their step parameters on each call. Newton starts from the previous
state.

## Build and reproduce

From the repository root, with CMake 3.20 or newer and a C++20 compiler:

```sh
git submodule update --init
python -m venv build/venv
build/venv/bin/python -m pip install pybind11
cmake -S . -B build -DPython_EXECUTABLE="$PWD/build/venv/bin/python" -DNANOBLAS_BUILD_DEMOS=OFF -DBUILD_TESTING=ON
cmake --build build -j 4
ctest --test-dir build --output-on-failure
cd build
./test_ode > massspring_summary.txt
./convergence > convergence_summary.txt
./test_rc > rc_summary.txt
venv/bin/python ../demos/plotmassspring.py
venv/bin/python ../demos/plotexperiments.py
```

On Windows PowerShell, use these equivalent commands from the repository
root:

```powershell
git submodule update --init
python -m venv build/venv
$python = (Resolve-Path build/venv/Scripts/python.exe).Path
& $python -m pip install pybind11
cmake -S . -B build "-DPython_EXECUTABLE=$python" -DNANOBLAS_BUILD_DEMOS=OFF -DBUILD_TESTING=ON
cmake --build build --parallel 4
ctest --test-dir build --output-on-failure
Set-Location build
.\test_ode.exe > massspring_summary.txt
.\convergence.exe > convergence_summary.txt
.\test_rc.exe > rc_summary.txt
.\venv\Scripts\python.exe ..\demos\plotmassspring.py
.\venv\Scripts\python.exe ..\demos\plotexperiments.py
```

CMake uses an installed Catch2 3 when available; otherwise it fetches version
3.8.1 at the commit pinned in `CMakeLists.txt`. The first configure therefore
needs GitHub access when Catch2 is not installed. Set `-DBUILD_TESTING=OFF`
to build the experiment programs without the Catch2 test target. The plotting
scripts use only Python's standard library. Generated data and plots are
written under `build/`.

## Mass–spring system

`src/ode_models.hpp` defines `MassSpring`. With mass `m = 1`, stiffness
`k = 1`, and initial state `(x, v) = (1, 0)`, the system is
`x' = v`, `v' = -x`. Its exact solution is `(cos(t), -sin(t))`, and its energy
is `E = (x² + v²)/2`.

The `test_ode` program compares all four methods at nominal step sizes
`0.4`, `0.2`, and `0.1`, and end times `4π` and `40π`. Each step is adjusted
to land exactly on the requested end time. It writes six CSV data sets,
twelve SVG plots (time evolution and phase portrait), and a summary of final
errors and energy ratios. The plots include the exact solution and use
independent panel scales so rapidly growing explicit Euler results do not
hide the bounded curves.

For `T = 4π` and `h ≈ 0.0997331`, the measured results are:

| Method | Final error | `E(T)/E(0)` |
| --- | ---: | ---: |
| Explicit Euler | 0.867377 | 3.48020 |
| Improved Euler | 0.0208441 | 1.00312 |
| Implicit Euler | 0.464949 | 0.287339 |
| Crank–Nicolson | 0.0104006 | 1.00000 |

Explicit Euler spirals outward and gains energy. Improved Euler also gains
energy, but more slowly. Implicit Euler spirals inward and damps this
undamped physical system. Crank–Nicolson preserves the energy of this linear
oscillator up to round-off and Newton tolerance, but still has phase error.
At `T = 40π` with the largest step, its final error is about `1.454` even
though its energy ratio remains 1: preserving amplitude does not guarantee
phase accuracy.

Newton's method uses an absolute residual tolerance of `1e-10`. In strongly
damped implicit runs, the state can reach the tolerance floor, so tiny final
energies should not be interpreted as arbitrarily precise damping
measurements.

## Convergence order and tests

The `convergence` program integrates to `T = 2π` with
`N = 2^4, ..., 2^12` steps. It computes
`e(h) = hypot(y_N(0) - 1, y_N(1))` and the observed order
`p = log2(e(h)/e(h/2))`. It writes `convergence.csv`; `plotexperiments.py`
plots the errors on logarithmic axes and marks each value of `N`.

Measured results for the last refinement (`N = 2048 → 4096`):

| Method | Error at `N = 4096` | `p` |
| --- | ---: | ---: |
| Explicit Euler | 0.0048307703 | 1.0034776 |
| Improved Euler | 2.4641574e-06 | 1.9999998 |
| Implicit Euler | 0.0048075462 | 0.9965251 |
| Crank–Nicolson | 1.2320783e-06 | 1.9999985 |

The expected orders are 1, 2, 1, and 2, respectively. The Catch2 suite checks
`|p - p_expected| <= 0.1` at every refinement whose coarser mesh has at least
512 steps. Coarse meshes are not required to meet this asymptotic-order
tolerance; the first explicit refinement, for example, gives `p ≈ 1.40`,
and the first implicit refinement gives `p ≈ 0.62`.

`tests/test_timestepper.cpp` also checks variable and zero step sizes, object
reuse, amplification formulas, nonlinear Crank–Nicolson behavior, the RC
Jacobian by finite differences, and RC accuracy including clock advancement.
When adding a method, add it to the typed test cases and declare its expected
order and an independently derived amplification formula.

## RC circuit and autonomous formulation

Ohm's law gives `U_R = R*I`, the capacitor relation gives `I = C*U_C'`, and
Kirchhoff's voltage law gives `U_0 = U_R + U_C`. Therefore,

```text
RC U_C' + U_C = cos(100π t),   U_C(0) = 0.
```

With state `y = (U_C, s)` and `s(0) = 0`, this becomes the autonomous system

```text
U_C' = (cos(ω s) - U_C)/(RC),   s' = 1,   ω = 100π.
Jacobian = [[-1/(RC), -ω sin(ω s)/(RC)], [0, 0]].
```

`RCCircuit` implements the system and its Jacobian. Its exact voltage is

```text
U_C(t) = [cos(ωt) + ωRC sin(ωt) - exp(-t/(RC))] / [1 + (ωRC)²].
```

`test_rc` compares all four methods for `(R, C) = (1, 1)` and
`(100, 10^-6)` through `T = 0.1` (five source periods), using steps
`0.005`, `0.001`, `0.0001`, and `0.00005`. It writes eight CSV files,
eight SVG plots, and a summary with final error, maximum error at the time
nodes, and maximum absolute voltage. The maximum error helps reveal a poorly
resolved transient that a small final error could hide. Plots include the
exact reference as a dashed gray curve and use independent scales.

For the stiff circuit with `h = 0.001`:

| Method | Maximum error on `[0,T]` | Final error |
| --- | ---: | ---: |
| Explicit Euler | 2.66663e95 | 2.66663e95 |
| Improved Euler | 1.90237e161 | 1.90237e161 |
| Implicit Euler | 0.0951751 | 0.00482466 |
| Crank–Nicolson | 0.666109 | 1.64321e-5 |

The two explicit methods are unstable with the two largest steps for this
circuit. Implicit Euler rapidly damps the transient. Crank–Nicolson remains
bounded but produces artificial alternating oscillations when the fast scale
is under-resolved. At `h = 0.00005`, its maximum error is `0.00787167`.
Reducing the step improves resolution of the transient.

## Stability functions

For `y' = λy`, a one-step method has the form `y_next = R(z)y`, where
`z = hλ`:

| Method | `R(z)` | Order |
| --- | --- | ---: |
| Explicit Euler | `1 + z` | 1 |
| Improved Euler | `1 + z + z²/2` | 2 |
| Implicit Euler | `1/(1 - z)` | 1 |
| Crank–Nicolson | `(1 + z/2)/(1 - z/2)` | 2 |

For the oscillator, `λ = ±i`:

```text
|R_exp(ih)|² = 1 + h²
|R_improved(ih)|² = 1 + h⁴/4
|R_implicit(ih)|² = 1/(1 + h²)
|R_CN(ih)|² = 1
```

These factors explain the energy changes above. For the RC circuit, the
homogeneous component has `λ = -1/(RC)`. Both explicit methods require
`0 <= h/(RC) <= 2` for absolute stability on this real mode, and strict
damping requires `< 2`. This stability condition does not guarantee
accuracy for the oscillating source. Both implicit methods are A-stable, but
only implicit Euler is L-stable: as `z → -∞`, its stability function tends
to 0, while Crank–Nicolson's tends to -1. This explains why Crank–Nicolson
can alternate in sign and damp very fast modes slowly.

- For `(R, C) = (1, 1)`, the time constant is `RC = 1 s`; there is no fast
  decay mode, and resolving the source period (`0.02 s`) sets the step size.
- For `(R, C) = (100, 10^-6)`, `RC = 10^-4 s`, much shorter than the source
  period. This is the stiff case. Explicit methods need `h < 2·10^-4 s` to
  damp the fast mode, even when only the later response is of interest.

The experiments illustrate that stability and accuracy are distinct:
a stable method can still be inaccurate if the step does not resolve the
source or transient.
