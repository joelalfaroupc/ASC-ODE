#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <ode_models.hpp>
#include "methods.hpp"

int main()
{
  using namespace ASC_ode;
  constexpr double resistances[] = {1.0, 100.0};
  constexpr double capacitances[] = {1.0, 1e-6};
  constexpr double requested_steps[] = {0.005, 0.001, 0.0001, 0.00005};
  constexpr double end_time = 0.1; // Five periods of the forcing.
  std::cout << "R C tau method final_error max_error max_abs_voltage file\n"
            << std::setprecision(8);
  for (int parameter = 0; parameter < 2; ++parameter)
  {
    auto rhs = std::make_shared<RCCircuit>(resistances[parameter], capacitances[parameter]);
    for (int h = 0; h < 4; ++h)
    {
      const int steps = static_cast<int>(std::ceil(end_time / requested_steps[h]));
      const double tau = end_time / steps;
      const std::string filename = "rc_p" + std::to_string(parameter) + "_h" + std::to_string(h) + ".csv";
      std::ofstream file(filename);
      if (!file) throw std::runtime_error("Cannot open " + filename);
      file << std::setprecision(17) << "t,exact";
      std::array<Vector<>, 4> states = {Vector<>({0.0,0.0}), Vector<>({0.0,0.0}),
                                      Vector<>({0.0,0.0}), Vector<>({0.0,0.0})};
      std::array<std::unique_ptr<TimeStepper>, 4> steppers;
      std::array<double, 4> max_errors{}, max_voltages{};
      for (size_t j = 0; j < steppers.size(); ++j)
      {
        steppers[j] = make_stepper(method_names[j], rhs);
        file << ',' << method_names[j];
      }
      file << '\n';
      for (int i = 0; i <= steps; ++i)
      {
        const double t = i * tau;
        const double exact = rhs->exactVoltage(t);
        file << t << ',' << exact;
        for (size_t j = 0; j < steppers.size(); ++j)
        {
          const double voltage = states[j](0);
          if (!std::isfinite(voltage)) throw std::runtime_error("Non-finite RC voltage");
          file << ',' << voltage;
          max_errors[j] = std::max(max_errors[j], std::abs(voltage-exact));
          max_voltages[j] = std::max(max_voltages[j], std::abs(voltage));
          if (i < steps) steppers[j]->doStep(tau, states[j]);
        }
        file << '\n';
      }
      for (size_t j = 0; j < steppers.size(); ++j)
        std::cout << resistances[parameter] << ' ' << capacitances[parameter] << ' '
                  << tau << ' ' << method_names[j] << ' '
                  << std::abs(states[j](0)-rhs->exactVoltage(end_time)) << ' '
                  << max_errors[j] << ' ' << max_voltages[j] << ' ' << filename << '\n';
    }
  }
}
