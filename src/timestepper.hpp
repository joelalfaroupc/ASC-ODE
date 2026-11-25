#ifndef TIMERSTEPPER_HPP
#define TIMERSTEPPER_HPP

#include <functional>
#include <exception>

#include "Newton.hpp"


namespace ASC_ode
{

  // base class of all time-stepping methods for y' = rhs(y)
  class TimeStepper
  {
  protected:
    std::shared_ptr<NonlinearFunction> m_rhs;
  public:
    TimeStepper(std::shared_ptr<NonlinearFunction> rhs) : m_rhs(rhs) {}
    virtual ~TimeStepper() = default;
    // advances y by one time-step tau
    virtual void doStep(double tau, VectorView<double> y) = 0;
  };

  // y_{n+1} = y_n + tau f(y_n)
  class ExplicitEuler : public TimeStepper
  {
    Vector<> m_vecf;   // allocated once, not in every step
  public:
    ExplicitEuler(std::shared_ptr<NonlinearFunction> rhs) 
    : TimeStepper(rhs), m_vecf(rhs->dimF()) {}
    void doStep(double tau, VectorView<double> y) override
    {
      this->m_rhs->evaluate(y, m_vecf);
      y += tau * m_vecf;
    }
  };

  // Explicit midpoint (second-order Runge--Kutta) method.
  // y_mid = y_n + tau/2 f(y_n), y_{n+1} = y_n + tau f(y_mid).
  class ImprovedEuler : public TimeStepper
  {
    Vector<> m_slope;
    Vector<> m_midpoint;
  public:
    ImprovedEuler(std::shared_ptr<NonlinearFunction> rhs)
      : TimeStepper(rhs), m_slope(rhs->dimF()), m_midpoint(rhs->dimX()) {}

    void doStep(double tau, VectorView<double> y) override
    {
      m_rhs->evaluate(y, m_slope);
      m_midpoint = y;
      m_midpoint += (tau / 2) * m_slope;
      m_rhs->evaluate(m_midpoint, m_slope);
      y += tau * m_slope;
    }
  };

  // solves y - y_n - tau f(y) = 0 with Newton's method. The equation is built once
  // by the function algebra, y_n and tau are updated in every step.
  class ImplicitEuler : public TimeStepper
  {
    std::shared_ptr<NonlinearFunction> m_equ;
    std::shared_ptr<Parameter> m_tau;
    std::shared_ptr<ConstantFunction> m_yold;
  public:
    ImplicitEuler(std::shared_ptr<NonlinearFunction> rhs) 
    : TimeStepper(rhs), m_tau(std::make_shared<Parameter>(0.0)) 
    {
      m_yold = std::make_shared<ConstantFunction>(rhs->dimX());
      auto ynew = std::make_shared<IdentityFunction>(rhs->dimX());
      m_equ = ynew - m_yold - m_tau * m_rhs;
    }

    void doStep(double tau, VectorView<double> y) override
    {
      m_yold->set(y);
      m_tau->set(tau);
      NewtonSolver(m_equ, y);
    }
  };


  // Trapezoidal rule: y - y_n - tau/2 (f(y_n) + f(y)) = 0.
  // Cache f(y_n) as a constant; Newton differentiates only f(y).
  class CrankNicolson : public TimeStepper
  {
    std::shared_ptr<NonlinearFunction> m_equ;
    std::shared_ptr<Parameter> m_half_tau;
    std::shared_ptr<ConstantFunction> m_yold, m_fold;
    Vector<> m_slope;
  public:
    CrankNicolson(std::shared_ptr<NonlinearFunction> rhs)
      : TimeStepper(rhs), m_half_tau(std::make_shared<Parameter>(0.0)),
        m_yold(std::make_shared<ConstantFunction>(rhs->dimX())),
        m_fold(std::make_shared<ConstantFunction>(rhs->dimX())),
        m_slope(rhs->dimF())
    {
      auto ynew = std::make_shared<IdentityFunction>(rhs->dimX());
      m_equ = ynew - m_yold - m_half_tau * (m_rhs + m_fold);
    }

    void doStep(double tau, VectorView<double> y) override
    {
      m_yold->set(y);
      m_rhs->evaluate(y, m_slope);
      m_fold->set(m_slope);
      m_half_tau->set(tau / 2);
      NewtonSolver(m_equ, y);
    }
  };


  

}


#endif
