# Exercise 17.2.2 — mass–spring system

For mass m = 1, spring constant k = 1, and initial state (x, v) = (1, 0),
the system is x' = v and v' = −x. The exact solution is x(t) = cos(t),
v(t) = −sin(t), with constant energy E = (x² + v²)/2.

`ExplicitEuler` uses y_next = y + h f(y). The new `ImprovedEuler` class
implements precisely the **explicit midpoint method** stated in the exercise:

```text
y_mid  = y + (h/2) f(y)
y_next = y + h f(y_mid)
```

## Reproduce the experiment

The repository uses `nanoblas` as a submodule, and its CMake build requires
`pybind11`. From the `ASC-ODE` directory:

```sh
git submodule update --init
python3 -m venv build/venv
build/venv/bin/python -m pip install pybind11
cmake -S . -B build -DPython_EXECUTABLE="$PWD/build/venv/bin/python" -DNANOBLAS_BUILD_DEMOS=OFF
cmake --build build --target test_ode
cd build
./test_ode
venv/bin/python ../demos/plotmassspring.py
```

The C++ program prints final-state error and the ratio E(T)/E(0). It writes
six CSV datasets for nominal steps h = 0.4, 0.2, 0.1 and end times
T = 4π, 40π. Actual steps are slightly adjusted so each run lands exactly
on T. The plotting script uses only the Python standard library and writes
one time-evolution and one phase-portrait SVG per dataset. The five panels
in each plot have independent vertical scales so the exact and midpoint
curves remain visible even when explicit Euler diverges. The current demo also
includes implicit Euler and Crank–Nicolson; see
[the complete comparison](exercises_euler.md) for their results.

## Results

| End time | Nominal step | Explicit final error | Midpoint final error | Explicit energy ratio | Midpoint energy ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4π | 0.4 | 9.109 | 0.3360 | 98.43 | 1.209 |
| 4π | 0.2 | 2.436 | 0.08376 | 11.68 | 1.025 |
| 4π | 0.1 | 0.8674 | 0.02084 | 3.480 | 1.003 |
| 40π | 0.4 | 1.264e10 | 3.702 | 1.598e20 | 7.303 |
| 40π | 0.2 | 2.216e5 | 0.8647 | 4.912e10 | 1.285 |
| 40π | 0.1 | 517.2 | 0.2105 | 2.684e5 | 1.032 |

The time plots show explicit Euler's oscillation envelope expanding; its
phase trajectory spirals outward instead of remaining on the exact unit
circle. The midpoint method is much closer to that circle, and reducing
the step by about half reduces its final error by about four at fixed T,
consistent with second-order accuracy. It also slowly spirals outward
over long times: it is **not** exactly energy-conserving.

For this oscillator, one explicit Euler step multiplies squared amplitude
(and energy) by 1 + h²; one midpoint step multiplies it by 1 + h⁴/4.
Both therefore gain energy, but midpoint does so much more slowly.
