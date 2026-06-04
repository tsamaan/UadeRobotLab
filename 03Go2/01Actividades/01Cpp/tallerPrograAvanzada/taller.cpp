/*
=============================================================
  Unitree Go2 — TALLER de Programación (C++)
=============================================================

  El Go2 es un robot cuadrúpedo. Camina sobre cuatro patas
  y puede realizar acrobacias, bailes y movimientos precisos.

  COMANDOS DISPONIBLES:
  ┌─ Postura ──────────────────────────────────────────────┐
  │  robot.StandUp()        → Se para                      │
  │  robot.StandDown()      → Se acuesta                   │
  │  robot.Sit()            → Se sienta                    │
  │  robot.RiseSit()        → Se levanta desde sentado     │
  │  robot.BalanceStand()   → Modo balance                 │
  ├─ Movimiento ───────────────────────────────────────────┤
  │  mover(robot, adelante, costado, giro, duracion)       │
  │    adelante : +avanza / -retrocede  (recomendado ≤ 0.5)│
  │    costado  : +izquierda / -derecha (recomendado ≤ 0.3)│
  │    giro     : +gira izq / -gira der (recomendado ≤ 0.5)│
  │    duracion : segundos que dura el movimiento          │
  │  robot.StopMove()       → Frena inmediatamente         │
  ├─ Gestos / Acrobacias ──────────────────────────────────┤
  │  robot.Hello()          → Saluda                       │
  │  robot.Stretch()        → Se estira                    │
  │  robot.Heart()          → Dibuja un corazón            │
  │  robot.Dance1()         → Baile 1                      │
  │  robot.Dance2()         → Baile 2                      │
  │  robot.FrontJump()      → Salto hacia adelante         │
  │  robot.FrontFlip()      → Salto mortal adelante        │
  │  robot.Scrape()         → Rasca el piso                │
  └────────────────────────────────────────────────────────┘
  UTILIDADES:
    esperar(segundos)        → Pausa el programa

  SECUENCIA SEGURA DE CIERRE (ya incluida en main):
    robot.StandDown() → robot.Damp()

=============================================================
  USO:
    ./go2_taller [interfaz_de_red]
    ./go2_taller eth0
=============================================================
*/

#include <chrono>
#include <iostream>
#include <string>
#include <thread>

#include <unitree/robot/channel/channel_factory.hpp>
#include <unitree/robot/go2/sport/sport_client.hpp>

using namespace unitree::robot;
using namespace unitree::robot::go2;

// ── Funciones auxiliares ──────────────────────────────────

/**
 * Mueve el robot durante 'duracion' segundos y luego frena.
 *   adelante : velocidad lineal hacia adelante/atrás  (m/s)
 *   costado  : velocidad lateral izquierda/derecha    (m/s)
 *   giro     : velocidad angular (rad/s)
 *   duracion : tiempo en segundos
 */
void mover(SportClient& robot,
           float adelante = 0.0f,
           float costado  = 0.0f,
           float giro     = 0.0f,
           float duracion = 1.0f)
{
    auto inicio = std::chrono::steady_clock::now();
    while (true) {
        float elapsed = std::chrono::duration<float>(
            std::chrono::steady_clock::now() - inicio).count();
        if (elapsed >= duracion) break;

        robot.Move(adelante, costado, giro);
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    robot.StopMove();
}

/** Pausa la ejecución del programa. */
void esperar(float segundos)
{
    std::this_thread::sleep_for(
        std::chrono::duration<float>(segundos));
}

// =============================================================
//   ¡¡ ZONA DEL ALUMNO — SOLO MODIFICAR ESTA FUNCIÓN !!
// =============================================================

void mi_programa(SportClient& robot)
{
    // ── Escribí tu código aquí ────────────────────────────────

    robot.StandUp();
    esperar(2.0f);
    robot.BalanceStand();
    robot.Stretch();
    esperar(7.0f);
    mover(robot, /*adelante=*/0.2f, /*duracion=*/2.0f);
    esperar(5.0f);

    // ─────────────────────────────────────────────────────────
}

// =============================================================
//   FIN ZONA DEL ALUMNO — no tocar lo que sigue
// =============================================================

int main(int argc, char* argv[])
{
    std::string interfaz = (argc > 1) ? argv[1] : "enp0s31f6";

    std::cout << std::string(50, '=') << "\n";
    std::cout << "  Unitree Go2 — Taller de Programación\n";
    std::cout << std::string(50, '=') << "\n";
    std::cout << "[INFO] Conectando vía '" << interfaz << "'...\n";

    ChannelFactory::Instance()->Init(0, interfaz);

    SportClient robot;
    robot.SetTimeout(10.0f);
    robot.Init();

    std::cout << "[OK]  Conectado. Iniciando en 2 segundos...\n\n";
    esperar(2.0f);

    try {
        mi_programa(robot);
    } catch (const std::exception& e) {
        std::cerr << "\n[ERROR] " << e.what() << "\n";
    }

    std::cout << "\n[FIN]  Llevando al robot a reposo...\n";
    robot.StandDown();
    esperar(1.0f);
    robot.Damp();
    std::cout << "[OK]   Listo!\n";

    return 0;
}
