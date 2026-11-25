#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numbers>
#include <ode_models.hpp>
#include "methods.hpp"

int main()
{
  using namespace ASC_ode;
  auto rhs = std::make_shared<MassSpring>(1.0, 1.0);
  const double end_time = 2 * std::numbers::pi;
  std::ofstream file("convergence.csv");
  if (!file) throw std::runtime_error("Cannot open convergence.csv");
  file << std::setprecision(17) << "method,N,tau,error,order\n";
  std::cout << "method N tau error order\n" << std::setprecision(8);
  for (auto name : method_names)
  {
    double previous_error = 0;
    for (int n = 16; n <= 4096; n *= 2)
    {
      Vector<> y = {1.0, 0.0};
      auto stepper = make_stepper(name, rhs);
      const double tau = end_time / n;
      for (int i = 0; i < n; ++i) stepper->doStep(tau, y);
      const double error = std::hypot(y(0)-1.0, y(1));
      if (!std::isfinite(error) || error <= 0)
        throw std::runtime_error("Invalid convergence error");
      file << name << ',' << n << ',' << tau << ',' << error << ',';
      std::cout << name << ' ' << n << ' ' << tau << ' ' << error << ' ';
      if (previous_error > 0)
      {
        const double order = std::log2(previous_error / error);
        file << order;
        std::cout << order;
      }
      else std::cout << "n/a";
      file << '\n';
      std::cout << '\n';
      previous_error = error;
    }
  }
}
