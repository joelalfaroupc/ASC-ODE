#ifndef ASC_ODE_DEMO_METHODS_HPP
#define ASC_ODE_DEMO_METHODS_HPP
#include <array>
#include <memory>
#include <stdexcept>
#include <string_view>
#include <timestepper.hpp>

// Shared experiment registry: new methods should also be added to the order tests.
inline constexpr std::array<std::string_view, 4> method_names = {
  "explicit", "improved", "implicit", "crank_nicolson"
};
inline std::unique_ptr<ASC_ode::TimeStepper> make_stepper(
    std::string_view name, std::shared_ptr<ASC_ode::NonlinearFunction> rhs)
{
  using namespace ASC_ode;
  if (name == "explicit") return std::make_unique<ExplicitEuler>(rhs);
  if (name == "improved") return std::make_unique<ImprovedEuler>(rhs);
  if (name == "implicit") return std::make_unique<ImplicitEuler>(rhs);
  if (name == "crank_nicolson") return std::make_unique<CrankNicolson>(rhs);
  throw std::invalid_argument("Unknown time-stepping method");
}
#endif
