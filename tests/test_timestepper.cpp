#include <array>
#include <algorithm>
#include <cmath>
#include <memory>
#include <numbers>
#include <type_traits>

#include <catch2/catch_template_test_macros.hpp>
#include <catch2/catch_test_macros.hpp>

#include <ode_models.hpp>
#include <timestepper.hpp>

using namespace ASC_ode;

namespace
{
  // Deliberately incomplete: a later method must declare its expected order.
  template <typename Method> struct MethodOrder;
  template <> struct MethodOrder<ExplicitEuler> { static constexpr double value = 1.0; };
  template <> struct MethodOrder<ImprovedEuler> { static constexpr double value = 2.0; };
  template <> struct MethodOrder<ImplicitEuler> { static constexpr double value = 1.0; };
  template <> struct MethodOrder<CrankNicolson> { static constexpr double value = 2.0; };
  template <typename Method>
  constexpr double expectedOrder = MethodOrder<Method>::value;

  // Exact application of R(h A), A = [[0, 1], [-1, 0]], independent of doStep.
  template <typename Method>
  std::array<double, 2> oscillatorStep(double h, double x, double v)
  {
    double a = 1.0;
    double b = h;
    if constexpr (std::is_same_v<Method, ImprovedEuler>)
      a = 1.0 - h * h / 2.0;
    else if constexpr (std::is_same_v<Method, ImplicitEuler>)
    {
      a = 1.0 / (1.0 + h * h);
      b = h / (1.0 + h * h);
    }
    else if constexpr (std::is_same_v<Method, CrankNicolson>)
    {
      a = (1.0 - h * h / 4.0) / (1.0 + h * h / 4.0);
      b = h / (1.0 + h * h / 4.0);
    }
    return {a * x + b * v, a * v - b * x};
  }

  class ScalarLinear : public NonlinearFunction
  {
    double lambda;
  public:
    explicit ScalarLinear(double value) : lambda(value) {}
    size_t dimX() const override { return 1; }
    size_t dimF() const override { return 1; }
    void evaluate(VectorView<double> x, VectorView<double> f) const override
    {
      f(0) = lambda * x(0);
    }
    void evaluateDeriv(VectorView<double>, MatrixView<double> df) const override
    {
      df(0, 0) = lambda;
    }
  };

  class SquareFunction : public NonlinearFunction
  {
  public:
    size_t dimX() const override { return 1; }
    size_t dimF() const override { return 1; }
    void evaluate(VectorView<double> x, VectorView<double> f) const override
    {
      f(0) = x(0) * x(0);
    }
    void evaluateDeriv(VectorView<double> x, MatrixView<double> df) const override
    {
      df(0, 0) = 2.0 * x(0);
    }
  };
}

// Add each later method to these template lists and supply its expected order
// and independent amplification formula above to retain the same regression suite.
TEMPLATE_TEST_CASE("Mass-spring convergence has the expected order", "[convergence]",
                   ExplicitEuler, ImprovedEuler, ImplicitEuler, CrankNicolson)
{
  auto rhs = std::make_shared<MassSpring>(1.0, 1.0);
  const double end_time = 2.0 * std::numbers::pi;
  double previous_error = 0.0;
  for (int exponent = 4; exponent <= 12; ++exponent)
  {
    const int steps = 1 << exponent;
    const double h = end_time / steps;
    Vector<> y = {1.0, 0.0};
    TestType stepper(rhs);
    for (int i = 0; i < steps; ++i)
      stepper.doStep(h, y);
    // The exercise prescribes the exact endpoint (1, 0), not a numerical reference.
    const double error = std::hypot(y(0) - 1.0, y(1));
    CAPTURE(steps, h, error);
    REQUIRE(std::isfinite(error));
    REQUIRE(error > 0.0);
    if (previous_error > 0.0)
    {
      REQUIRE(error < previous_error);
      const double order = std::log2(previous_error / error);
      CAPTURE(order);
      // Coarse N=16 runs are outside the asymptotic regime for first-order Euler.
      // Test every successive halving whose coarse grid has N >= 512.
      if (steps >= 1024)
        REQUIRE(std::abs(order - expectedOrder<TestType>) <= 0.1);
    }
    previous_error = error;
  }
}

TEMPLATE_TEST_CASE("Oscillator updates match the stability function", "[step][state]",
                   ExplicitEuler, ImprovedEuler, ImplicitEuler, CrankNicolson)
{
  auto rhs = std::make_shared<MassSpring>(1.0, 1.0);
  TestType stepper(rhs);
  Vector<> y = {0.7, -0.4};
  std::array<double, 2> expected = {y(0), y(1)};
  for (double h : {0.1, 0.04, 0.0, 0.2})
  {
    expected = oscillatorStep<TestType>(h, expected[0], expected[1]);
    stepper.doStep(h, y);
    CAPTURE(h);
    REQUIRE(std::abs(y(0) - expected[0]) < 1e-11);
    REQUIRE(std::abs(y(1) - expected[1]) < 1e-11);
  }

  // Reusing the object with a different state must not reuse a previous y_old or f(y_old).
  y(0) = -0.3;
  y(1) = 0.8;
  expected = oscillatorStep<TestType>(0.07, y(0), y(1));
  stepper.doStep(0.07, y);
  REQUIRE(std::abs(y(0) - expected[0]) < 1e-11);
  REQUIRE(std::abs(y(1) - expected[1]) < 1e-11);
}

TEST_CASE("Crank-Nicolson uses trapezoidal endpoint slopes for a nonlinear RHS", "[nonlinear]")
{
  auto rhs = std::make_shared<SquareFunction>();
  CrankNicolson stepper(rhs);
  Vector<> y = {1.0};
  const double h = 0.1;
  stepper.doStep(h, y);
  // Solve y - 1 - (h/2)(1 + y^2) = 0, choosing the root near y_old.
  const double expected = (1.0 - std::sqrt(1.0 - 2.0 * h - h * h)) / h;
  REQUIRE(std::abs(y(0) - expected) < 1e-9);
  REQUIRE(std::abs(y(0) - 1.0 - h / 2.0 * (1.0 + y(0) * y(0))) < 1e-10);
  // Implicit midpoint has a different nonlinear residual; oscillator-only tests
  // cannot distinguish that method from Crank-Nicolson.
  const double midpoint = (1.0 + y(0)) / 2.0;
  REQUIRE(std::abs(y(0) - 1.0 - h * midpoint * midpoint) > 1e-5);
}

TEMPLATE_TEST_CASE("Large negative eigenvalues separate explicit and implicit stability", "[stability]",
                   ExplicitEuler, ImprovedEuler, ImplicitEuler, CrankNicolson)
{
  auto rhs = std::make_shared<ScalarLinear>(-10000.0);
  TestType stepper(rhs);
  Vector<> y = {1.0};
  constexpr double z = -10.0;
  double amplification;
  if constexpr (std::is_same_v<TestType, ExplicitEuler>)
    amplification = 1.0 + z;
  else if constexpr (std::is_same_v<TestType, ImprovedEuler>)
    amplification = 1.0 + z + z * z / 2.0;
  else if constexpr (std::is_same_v<TestType, ImplicitEuler>)
    amplification = 1.0 / (1.0 - z);
  else
    amplification = (1.0 + z / 2.0) / (1.0 - z / 2.0);
  stepper.doStep(0.001, y);
  REQUIRE(std::abs(y(0) - amplification) < 1e-11);
  if constexpr (std::is_same_v<TestType, ExplicitEuler>
                || std::is_same_v<TestType, ImprovedEuler>)
    REQUIRE(std::abs(y(0)) > 1.0);
  else
    REQUIRE(std::abs(y(0)) < 1.0);
}

TEST_CASE("Autonomous RC circuit Jacobian matches finite differences", "[rc][jacobian]")
{
  for (auto parameters : {std::array<double, 2>{1.0, 1.0},
                          std::array<double, 2>{100.0, 1e-6}})
  {
    RCCircuit rhs(parameters[0], parameters[1]);
    Vector<> x = {0.37, 0.003};
    Matrix<> jacobian(2, 2);
    rhs.evaluateDeriv(x, jacobian);
    constexpr double epsilon = 1e-7;
    for (size_t column = 0; column < 2; ++column)
    {
      Vector<> plus = x;
      Vector<> minus = x;
      Vector<> fplus(2), fminus(2);
      plus(column) += epsilon;
      minus(column) -= epsilon;
      rhs.evaluate(plus, fplus);
      rhs.evaluate(minus, fminus);
      for (size_t row = 0; row < 2; ++row)
      {
        const double numerical = (fplus(row) - fminus(row)) / (2.0 * epsilon);
        CAPTURE(parameters[0], parameters[1], row, column);
        REQUIRE(std::abs(numerical - jacobian(row, column))
                <= 1e-6 * (1.0 + std::abs(jacobian(row, column))));
      }
    }
    REQUIRE(std::abs(rhs.exactVoltage(0.0)) < 1e-15);
  }
}

TEMPLATE_TEST_CASE("RC integration agrees with the exact solution and advances its clock", "[rc][accuracy]",
                   ExplicitEuler, ImprovedEuler, ImplicitEuler, CrankNicolson)
{
  for (auto parameters : {std::array<double, 2>{1.0, 1.0},
                          std::array<double, 2>{100.0, 1e-6}})
  {
    auto rhs = std::make_shared<RCCircuit>(parameters[0], parameters[1]);
    TestType stepper(rhs);
    Vector<> y = {0.0, 0.0};
    constexpr double h = 1e-5;
    constexpr int steps = 2000;
    double max_error = 0.0;
    for (int i = 0; i < steps; ++i)
    {
      stepper.doStep(h, y);
      max_error = std::max(max_error, std::abs(y(0) - rhs->exactVoltage((i + 1) * h)));
    }
    CAPTURE(parameters[0], parameters[1], max_error);
    REQUIRE(std::isfinite(y(0)));
    REQUIRE(std::abs(y(1) - steps * h) < 2e-12);
    const bool stiff = parameters[1] < 1.0;
    // For the nonstiff second-order runs, exact trapezoidal quadrature has
    // max error 2.64e-9. The existing Newton tolerance 1e-10 permits stopping
    // after one iterate (residual <= 2.47e-11), giving max error 5.25e-9.
    // The bound includes both time-discretization and nonlinear-solve error.
    const double tolerance = expectedOrder<TestType> == 1.0
        ? (stiff ? 0.025 : 1.1e-5) : (stiff ? 0.001 : 1e-8);
    REQUIRE(max_error < tolerance);
  }
}
