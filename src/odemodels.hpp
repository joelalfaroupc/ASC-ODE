#ifndef ASC_ODE_MODELS_HPP
#define ASC_ODE_MODELS_HPP

#include <cmath>
#include <numbers>
#include <stdexcept>
#include "nonlinfunc.hpp"

namespace ASC_ode
{
  // State (position, velocity); initial (1, 0) gives
  // position = cos(sqrt(k/m)*t), velocity = -sqrt(k/m)*sin(sqrt(k/m)*t).
  class MassSpring : public NonlinearFunction
  {
    double m_mass, m_stiffness;
  public:
    MassSpring(double mass, double stiffness) : m_mass(mass), m_stiffness(stiffness)
    {
      if (!std::isfinite(mass) || !std::isfinite(stiffness) || mass <= 0 || stiffness <= 0)
        throw std::invalid_argument("Mass and stiffness must be finite and positive");
    }
    size_t dimX() const override { return 2; }
    size_t dimF() const override { return 2; }
    void evaluate(VectorView<double> x, VectorView<double> f) const override
    {
      f(0) = x(1);
      f(1) = -m_stiffness / m_mass * x(0);
    }
    void evaluateDeriv(VectorView<double>, MatrixView<double> df) const override
    {
      df = 0.0;
      df(0, 1) = 1.0;
      df(1, 0) = -m_stiffness / m_mass;
    }
  };

  // RC*U' + U = cos(100*pi*t). Autonomous state (U, t), with t' = 1.
  class RCCircuit : public NonlinearFunction
  {
    double m_rc;
    static constexpr double omega = 100.0 * std::numbers::pi;
  public:
    RCCircuit(double resistance, double capacitance) : m_rc(resistance * capacitance)
    {
      if (!std::isfinite(resistance) || !std::isfinite(capacitance)
          || resistance <= 0 || capacitance <= 0 || !std::isfinite(m_rc) || m_rc <= 0)
        throw std::invalid_argument("Resistance and capacitance must be finite and positive");
    }
    size_t dimX() const override { return 2; }
    size_t dimF() const override { return 2; }
    void evaluate(VectorView<double> x, VectorView<double> f) const override
    {
      f(0) = (std::cos(omega * x(1)) - x(0)) / m_rc;
      f(1) = 1.0;
    }
    void evaluateDeriv(VectorView<double> x, MatrixView<double> df) const override
    {
      df = 0.0;
      df(0, 0) = -1.0 / m_rc;
      df(0, 1) = -omega * std::sin(omega * x(1)) / m_rc;
    }
    // Exact voltage for U(0)=0; useful for accuracy comparisons.
    double exactVoltage(double t) const
    {
      const double a = omega * m_rc;
      return (std::cos(omega*t) + a*std::sin(omega*t) - std::exp(-t/m_rc)) / (1+a*a);
    }
  };
}
#endif
