# Ejercicios de Euler explícito e implícito

Implementación de `IntroSC/ODEs/implementation_ee.md` y
`implementation_ie.md`. La comparación explícita anterior se conserva en
[exercise_17_2_2.md](exercise_17_2_2.md); ahora se comparan los cuatro métodos.

## Métodos

Para una EDO autónoma `y' = f(y)`, `src/timestepper.hpp` proporciona:

- **ExplicitEuler:** `y_next = y + h*f(y)`.
- **ImprovedEuler:** punto medio **explícito**, no Heun:
  `y_mid = y + h/2*f(y)`, `y_next = y + h*f(y_mid)`.
- **ImplicitEuler:** Newton resuelve `y_next - y - h*f(y_next) = 0`.
- **CrankNicolson:** Newton resuelve
  `y_next - y - h/2*(f(y) + f(y_next)) = 0`.
  Es la regla trapezoidal, no el punto medio implícito. Para funciones no
  lineales esas dos fórmulas son distintas y hay una prueba que lo comprueba.

Los métodos implícitos reutilizan la función compuesta y actualizan sus
constantes y el parámetro del paso. Usan `y` como aproximación inicial para
Newton. Improved Euler reutiliza sus vectores auxiliares sin reasignarlos
en cada paso. No se ha modificado la implementación preexistente de Newton.

## Compilar y reproducir

Desde la raíz de ASC-ODE, con CMake >= 3.20 y compilador C++20:

```sh
git submodule update --init
python3 -m venv build/venv
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

Catch2 3 se busca instalado; si no está disponible, CMake descarga la
versión 3.8.1 fijada por commit. La primera configuración necesita acceso
a GitHub. `-DBUILD_TESTING=OFF` permite compilar solamente los experimentos.
Las gráficas usan únicamente la biblioteca estándar de Python, sin matplotlib.
Todos los resultados quedan en `build/`, excluido de Git.

## Masa–muelle: tiempo, fase y energía

`src/ode_models.hpp` define el modelo `MassSpring`. Para `m=k=1` y
`y(0)=(1,0)`, la solución es `(cos(t),-sin(t))` y la energía es
`E=(x²+v²)/2`.

`test_ode` compara los cuatro métodos con pasos nominales `0.4,0.2,0.1`
y tiempos finales `4π,40π`. Ajusta cada paso a `T/ceil(T/h)` para llegar
exactamente a T. Genera seis CSV, doce SVG (tiempo y fase) y un resumen de
error final y cociente de energía. Cada gráfica incluye la solución exacta;
los paneles tienen escalas independientes para no ocultar los métodos
acotados cuando Euler explícito crece mucho.

Con `T=4π` y `h≈0.0997331`, los resultados son:

| Método | Error final | E(T)/E(0) |
| --- | ---: | ---: |
| Explícito | 0.867377 | 3.48020 |
| Mejorado | 0.0208441 | 1.00312 |
| Implícito | 0.464949 | 0.287339 |
| Crank–Nicolson | 0.0104006 | 1.00000 |

Euler explícito espirala hacia fuera y gana energía. El mejorado también
gana energía, pero mucho más lentamente. Euler implícito espirala hacia
dentro y amortigua un sistema que físicamente no tiene amortiguamiento.
Crank–Nicolson conserva la energía de este oscilador lineal (salvo redondeo
y tolerancia de Newton), pero tiene error de fase. A `T=40π` y el paso más
grande, su error final es aproximadamente `1.454`, aunque su energía sea 1:
conservar amplitud no equivale a reproducir la fase.

Newton usa tolerancia absoluta de residuo `1e-10`. En las ejecuciones
implícitas muy amortiguadas el estado puede llegar al suelo de tolerancia;
no debe interpretarse su diminuta energía final como una medida de
amortiguamiento exacta hasta precisión arbitraria.

## Orden de convergencia y pruebas Catch2

`convergence` integra hasta `T=2π` con `N=2^4,...,2^12` y calcula
`e(h)=hypot(y_N(0)-1,y_N(1))` y `p=log2(e(h)/e(h/2))`.
Produce `convergence.csv`, y `plotexperiments.py` crea `convergence.svg`,
con ambos ejes logarítmicos, curvas y marcas para cada N.

Resultados medidos para el último refinamiento (`N=2048 → 4096`):

| Método | Error con N=4096 | p |
| --- | ---: | ---: |
| explicit | 0.0048307703 | 1.0034776 |
| improved | 2.4641574e-06 | 1.9999998 |
| implicit | 0.0048075462 | 0.9965251 |
| crank_nicolson | 1.2320783e-06 | 1.9999985 |

Los órdenes esperados son 1, 2, 1 y 2. La suite calcula todos los errores
y comprueba `|p-p_expected| <= 0.1` en **cada** refinamiento cuyo N grueso
es al menos 512. No se exige ese margen en mallas gruesas fuera del régimen
asintótico: por ejemplo, el primer cociente explícito da `p≈1.40`, y el
implícito `p≈0.62`, sin que sus métodos dejen de ser de primer orden.

`tests/test_timestepper.cpp` usa casos plantilla de Catch2. Para un método
nuevo, añadirlo a las listas de tipos y declarar su `MethodOrder` y fórmula
de amplificación independiente: así se reutiliza la medición de orden sin
asignarle por defecto un orden incorrecto. Hay además pruebas de pasos
variables y cero, reutilización de objetos, fórmula de amplificación,
Crank–Nicolson no lineal, Jacobiano RC por diferencias finitas y precisión
RC incluyendo avance del reloj.

## Circuito RC y forma autónoma

Ohm: `U_R=R*I`; condensador: `I=C*U_C'`; Kirchhoff:
`U_0=U_R+U_C`. Por tanto:

```text
RC U_C' + U_C = cos(100π t),  U_C(0)=0.
```

Con estado `y=(U_C,s)` y `s(0)=0`, se obtiene la EDO autónoma:

```text
U_C' = (cos(ω s) - U_C)/(RC),  s' = 1,  ω=100π.
Jacobian = [[-1/(RC), -ω sin(ω s)/(RC)], [0, 0]].
```

`RCCircuit` implementa esa función y su Jacobiano. La referencia exacta es:

```text
U_C(t) = [cos(ωt) + ωRC sin(ωt) - exp(-t/(RC))] / [1+(ωRC)²].
```

`test_rc` compara **los cuatro métodos** con `(R,C)=(1,1)` y `(100,10^-6)`,
hasta `T=0.1` (cinco periodos de la fuente), usando pasos
`0.005,0.001,0.0001,0.00005`. Produce ocho CSV, ocho SVG y un resumen con
error final, máximo error en los nodos y máxima tensión absoluta. Mostrar
el error máximo importa: el error final puede ocultar un transitorio mal
resuelto. Las gráficas tienen escalas independientes y la referencia exacta
trazada en gris discontinuo.

Para el circuito rígido con `h=0.001`:

| Método | Máximo error en [0,T] | Error final |
| --- | ---: | ---: |
| Explícito | 2.66663e95 | 2.66663e95 |
| Mejorado | 1.90237e161 | 1.90237e161 |
| Implícito | 0.0951751 | 0.00482466 |
| Crank–Nicolson | 0.666109 | 1.64321e-5 |

Los métodos explícitos son inestables con los dos pasos grandes en ese
circuito. Implícito amortigua rápidamente el transitorio. Crank–Nicolson
queda acotado, pero produce oscilaciones alternantes artificiales cuando
no se resuelve la escala rápida. Con `h=0.00005`, sus errores máximos son
respectivamente `0.117948,0.0227482,0.0766265,0.00787167`: reducir el paso
mejora la resolución del transitorio.

## Explicación mediante funciones de estabilidad

Para `y'=λy`, `y_next=R(z)y`, con `z=hλ`:

| Método | R(z) | Orden |
| --- | --- | ---: |
| Explícito | 1+z | 1 |
| Mejorado | 1+z+z²/2 | 2 |
| Implícito | 1/(1-z) | 1 |
| Crank–Nicolson | (1+z/2)/(1-z/2) | 2 |

En el oscilador `λ=±i`:
`|R_exp(ih)|²=1+h²`, `|R_mej(ih)|²=1+h⁴/4`,
`|R_imp(ih)|²=1/(1+h²)`, y `|R_CN(ih)|²=1`.
Estos factores explican directamente los cambios de energía observados.

En RC la componente homogénea tiene `λ=-1/(RC)`. Los dos explícitos
requieren `0 <= h/(RC) <= 2` para estabilidad absoluta sobre ese eje real;
para amortiguamiento estricto debe ser `<2`. Es una restricción de
estabilidad del modo homogéneo, no una garantía de precisión con la fuente
oscilante. Los implícitos son A-estables, pero **solo Euler implícito es
L-estable**: cuando `z→-∞`, su R tiende a 0, mientras el de CN tiende a -1.
Por eso CN puede alternar de signo y amortiguar lentamente modos muy rápidos.

- `(R,C)=(1,1)`: constante de tiempo `RC=1 s`, sin modo de decaimiento
  rápido; la precisión de la fuente (periodo `0.02 s`) domina el paso.
- `(R,C)=(100,10^-6)`: `RC=10^-4 s`, mucho menor que el periodo de la
  fuente; es el caso **rígido**. Los explícitos necesitan `h<2·10^-4 s`
  para amortiguar el modo rápido, incluso si interesa solo la evolución
  posterior al transitorio.

Las curvas comprueban estabilidad y precisión como propiedades distintas:
un método estable puede ser poco preciso si el paso no resuelve la fuente
o el transitorio.
