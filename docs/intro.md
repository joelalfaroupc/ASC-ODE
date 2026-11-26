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
and compare their accuracy and stability.

The book's [publishing guide](publishing.md) describes how the documentation
is deployed to GitHub Pages.
