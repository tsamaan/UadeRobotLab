/*
=============================================================
  Unitree G1 — TALLER de Programación (C++)
=============================================================

  El G1 es un robot humanoide bípedo. A diferencia del Go2
  (que es cuadrúpedo), el G1 camina erguido sobre dos piernas
  y tiene brazos con los que puede interactuar.

  COMANDOS DISPONIBLES:
  ┌─ Postura ──────────────────────────────────────────────┐
  │  client.HighStand()       → Se para bien erguido (alto)│
  │  client.LowStand()        → Postura más baja           │
  ├─ Movimiento ───────────────────────────────────────────┤
  │  mover(client, adelante, costado, giro, duracion)      │
  │    adelante : +avanza / -retrocede  (recomendado ≤ 0.4)│
  │    costado  : +izquierda / -derecha (recomendado ≤ 0.3)│
  │    giro     : +gira izq / -gira der (recomendado ≤ 0.5)│
  │    duracion : segundos que dura el movimiento          │
  │  client.StopMove()        → Frena inmediatamente       │
  ├─ Brazos / Gestos ──────────────────────────────────────┤
  │  client.WaveHand()        → Saluda con la mano         │
  │  client.WaveHand(true)    → Saluda girando el cuerpo   │
  │  client.ShakeHand(0)      → Inicia el saludo de manos  │
  │  client.ShakeHand(1)      → Finaliza el saludo de manos│
  ├─ Balance ──────────────────────────────────────────────┤
  │  client.BalanceStand()    → Balance normal             │
  └────────────────────────────────────────────────────────┘
  UTILIDADES:
    esperar(segundos)          → Pausa el programa

  SECUENCIA SEGURA DE INICIO:
    1. ... tu código ...  ← el robot ya está parado
    2. Al final: client.StopMove() para que quede quieto

=============================================================
  USO:
    ./g1_taller [interfaz_de_red]
    ./g1_taller eth0
=============================================================
*/

#include <chrono>
#include <csignal>
#include <iostream>
#include <string>
#include <thread>

#include <unitree/robot/channel/channel_factory.hpp>
#include <unitree/robot/g1/loco/g1_loco_client.hpp>

using namespace unitree::robot;
using namespace unitree::robot::g1;

// ── Funciones auxiliares ──────────────────────────────────

/**
 * Mueve el robot durante 'duracion' segundos y luego frena.
 *   adelante : velocidad lineal hacia adelante/atrás  (m/s)
 *   costado  : velocidad lateral izquierda/derecha    (m/s)
 *   giro     : velocidad angular (rad/s)
 *   duracion : tiempo en segundos
 */
void mover(LocoClient& robot,
           float adelante = 0.0f,
           float costado  = 0.0f,
           float giro     = 0.0f,
           float duracion = 1.0f)
{
    auto inicio = std::chrono::steady_clock::now();
    while (true) {
        auto ahora   = std::chrono::steady_clock::now();
        float elapsed = std::chrono::duration<float>(ahora - inicio).count();
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

void mi_programa(LocoClient& robot)
{
    // ── Escribí tu código aquí ────────────────────────────────

    mover(robot, /*adelante=*/0.0f, /*costado=*/0.0f, /*giro=*/0.5f, /*duracion=*/2.0f);
    std::cout << "Gira hacia el costado" << std::endl;
    esperar(1.0f);

    mover(robot, /*adelante=*/0.5f, /*costado=*/0.0f, /*giro=*/0.0f, /*duracion=*/3.0f);
    std::cout << "Camina hacia adelante" << std::endl;
    esperar(1.0f);

    mover(robot, /*adelante=*/0.0f, /*costado=*/0.0f, /*giro=*/0.5f, /*duracion=*/10.0f);
    std::cout << "Gira para el otro lado" << std::endl;
    esperar(1.0f);

    // ─────────────────────────────────────────────────────────
}

// =============================================================
//   FIN ZONA DEL ALUMNO — no tocar lo que sigue
// =============================================================

// ── Main ──────────────────────────────────────────────────

int main(int argc, char* argv[])
{
    std::string interfaz = (argc > 1) ? argv[1] : "enp0s31f6";

    std::cout << std::string(50, '=') << "\n";
    std::cout << "  Unitree G1 — Taller de Programación\n";
    std::cout << std::string(50, '=') << "\n";
    std::cout << "[INFO] Conectando vía '" << interfaz << "'...\n";

    ChannelFactory::Instance()->Init(0, interfaz);

    LocoClient robot;
    robot.SetTimeout(10.0f);
    robot.Init();

    std::cout << "[OK]  Conectado. Iniciando en 3 segundos...\n\n";
    esperar(3.0f);

    try {
        mi_programa(robot);
    } catch (const std::exception& e) {
        std::cerr << "\n[ERROR] " << e.what() << "\n";
    }

    std::cout << "\n[FIN]  Frenando...\n";
    robot.StopMove();
    std::cout << "[OK]   Listo!\n";

    return 0;
}
