#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <numbers>
#include <stdexcept>
#include <string>

#include <nonlinfunc.hpp>
#include <timestepper.hpp>
#include <ode_models.hpp>

using namespace ASC_ode;

int main()
{
  // m = k = 1 and (x(0), v(0)) = (1, 0): x = cos(t), v = -sin(t).
  auto rhs = std::make_shared<MassSpring>(1.0, 1.0);
  constexpr double requested_steps[] = {0.4, 0.2, 0.1};
  const double end_times[] = {4.0 * std::numbers::pi, 40.0 * std::numbers::pi};

  std::cout << std::setprecision(8);
  std::cout << "end_time requested_dt actual_dt method final_error energy_ratio file\n";

  for (int end_index = 0; end_index < 2; ++end_index)
  {
    const double end_time = end_times[end_index];
    for (int step_index = 0; step_index < 3; ++step_index)
    {
      const double requested_dt = requested_steps[step_index];
      const int steps = static_cast<int>(std::ceil(end_time / requested_dt));
      const double dt = end_time / steps; // Land exactly on the requested end time.
      const std::string filename = "massspring_T" + std::to_string(end_index)
          + "_h" + std::to_string(step_index) + ".csv";

      std::ofstream file(filename);
      if (!file) throw std::runtime_error("Cannot open " + filename);
      file << std::setprecision(17);
      file << "t,euler_x,euler_v,improved_x,improved_v,implicit_x,implicit_v,cn_x,cn_v,exact_x,exact_v\n";

      Vector<> euler = {1.0, 0.0};
      Vector<> improved = {1.0, 0.0};
      Vector<> implicit = {1.0, 0.0};
      Vector<> cn = {1.0, 0.0};
      ExplicitEuler explicit_stepper(rhs);
      ImprovedEuler midpoint_stepper(rhs);
      ImplicitEuler implicit_stepper(rhs);
      CrankNicolson cn_stepper(rhs);

      for (int i = 0; i <= steps; ++i)
      {
        const double t = i * dt;
        file << t << ',' << euler(0) << ',' << euler(1) << ','
             << improved(0) << ',' << improved(1) << ','
             << implicit(0) << ',' << implicit(1) << ','
             << cn(0) << ',' << cn(1) << ','
             << std::cos(t) << ',' << -std::sin(t) << '\n';
        if (i < steps)
        {
          explicit_stepper.doStep(dt, euler);
          midpoint_stepper.doStep(dt, improved);
          implicit_stepper.doStep(dt, implicit);
          cn_stepper.doStep(dt, cn);
        }
      }

      const auto report = [&](const char* method, VectorView<double> y)
      {
        const double error = std::hypot(y(0) - std::cos(end_time),
                                        y(1) + std::sin(end_time));
        const double energy_ratio = y(0) * y(0) + y(1) * y(1);
        std::cout << end_time << ' ' << requested_dt << ' ' << dt << ' '
                  << method << ' ' << error << ' ' << energy_ratio << ' '
                  << filename << '\n';
      };
      report("explicit", euler);
      report("improved", improved);
      report("implicit", implicit);
      report("crank_nicolson", cn);
    }
  }
}
