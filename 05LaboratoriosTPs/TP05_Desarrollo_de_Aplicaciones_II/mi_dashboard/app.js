/* Dashboard de telemetría — TP05
 *
 * El recorrido de un dato, de punta a punta (explicado en docs/COMO_FUNCIONA.md):
 *
 *   conectar()        pide /info: qué robot es, cuántos motores, qué patas.
 *   armarPantalla()   con eso arma la tabla, los botones del gráfico, las marcas.
 *   abrirWebSocket()  se suscribe a /ws: llega un JSON ~10 veces por segundo.
 *   iniciarPolling()  plan B si el WebSocket no anda: pide /telemetria en bucle.
 *   recibir()         guarda el último dato y lo suma al historial.
 *   cuadro()          en cada refresco de pantalla dibuja lo último que llegó.
 *
 * Recibir y dibujar están separados a propósito (ver ADR-0004).
 */

"use strict";

const PUERTO = 8001;
const VENTANA_SEGUNDOS = 30;       // historia que muestra el gráfico
const ESPERA_WS_MS = 3000;         // si el WebSocket no manda nada en este tiempo, plan B
const INTERVALO_POLLING_MS = 100;  // 10 por segundo, igual que el WebSocket
const DATO_VIEJO_MS = 2000;        // sin datos por más de esto, se avisa
const REINTENTO_MS = 3000;

const TEMP_TIBIA = 40;
const TEMP_CALIENTE = 50;

// Qué es medición y qué no, EN EL SIMULADOR (API.md, sección "Qué es real y
// qué está derivado"). El JSON no lo dice, así que lo sabe el dashboard.
// Ver ADR-0005.
const ORIGEN_EN_SIMULADOR = {
  angulo: "real",
  velocidad: "real",
  yaw: "real",
  torque: "derivado",
  temperatura: "derivado",
  roll: "derivado",
  pitch: "derivado",
  fuerzas: "derivado",
  bms: "inventado",
};

// Dónde va cada pata en el dibujo visto desde arriba (x: derecha, y: atrás).
const POSICION_PATAS = {
  FR: [0.45, -0.7], FL: [-0.45, -0.7],
  RR: [0.45, 0.7],  RL: [-0.45, 0.7],
  R_foot: [0.4, 0], L_foot: [-0.4, 0],
};

// Ordenados para que los motores elegidos por defecto (muslos del Go2: 1, 4,
// 7, 10; rodillas del G1: 3, 9) caigan en colores bien distintos.
const COLORES = ["#4da3ff", "#3fb950", "#f0883e", "#bc8cff", "#ff7b72", "#f778ba", "#e3b341", "#39c5cf"];

const estado = {
  host: "",             // lo que escribió el usuario, ej. "10.0.0.5"
  base: "",             // "http://10.0.0.5:8001"
  info: null,           // respuesta de /info
  ultimo: null,         // último JSON de telemetría
  hayNuevo: false,      // llegó un dato que todavía no se dibujó
  historial: [],        // [{ t, angulos }] de los últimos 30 s
  seleccion: new Set(), // motores que se grafican
  celdas: [],           // referencias a las celdas de la tabla
  llegadas: [],         // cuándo llegó cada dato, para medir cuántos por segundo
  ultimaLlegada: 0,
  ultimoAvance: 0,      // cuándo cambió `ts` por última vez (ver ADR-0006)
  modo: null,           // "websocket" | "polling" | null
  ws: null,
  timers: [],
  intento: 0,           // cada conexión nueva invalida las respuestas de la anterior
};

const $ = (id) => document.getElementById(id);


/* ------------------------------------------------------------------ */
/* 1. Conexión                                                         */
/* ------------------------------------------------------------------ */

async function conectar(host) {
  desconectar();
  const intento = ++estado.intento;
  estado.host = host;
  const hostPuerto = host.includes(":") ? host : `${host}:${PUERTO}`;
  estado.base = `http://${hostPuerto}`;
  recordarHost(host);
  ponerEstado("conectando…", "apagado");

  try {
    const r = await fetch(`${estado.base}/info`, { cache: "no-store" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const info = await r.json();
    if (intento !== estado.intento) return;
    estado.info = info;
    armarPantalla(info);
    abrirWebSocket(`ws://${hostPuerto}/ws`, intento);
  } catch (err) {
    if (intento !== estado.intento) return;
    ponerEstado("sin conexión", "error");
    $("robot-detalle").textContent =
      `No responde ${estado.base}. ¿Está abierto INICIAR_TP05? Reintentando…`;
    programar(() => conectar(host), REINTENTO_MS);
  }
}

function abrirWebSocket(url, intento) {
  let ws;
  try {
    ws = new WebSocket(url);
  } catch {
    iniciarPolling(intento);
    return;
  }
  estado.ws = ws;

  // Plan B: si en 3 segundos no llegó nada, el WebSocket no sirve.
  programar(() => {
    if (intento === estado.intento && estado.modo !== "websocket") iniciarPolling(intento);
  }, ESPERA_WS_MS);

  ws.onmessage = (evento) => {
    if (intento !== estado.intento) return;
    estado.modo = "websocket";
    recibir(JSON.parse(evento.data));
  };

  // onerror siempre viene seguido de onclose: alcanza con escuchar éste.
  ws.onclose = () => {
    if (intento !== estado.intento) return;
    if (estado.modo === "websocket") {
      // Andaba y se cortó (se cerró el backend, se cayó el wifi): empezar de nuevo.
      ponerEstado("se cortó, reconectando…", "error");
      programar(() => conectar(estado.host), REINTENTO_MS);
    } else {
      // Nunca llegó a andar: el backend no tiene WebSocket. Plan B ya.
      iniciarPolling(intento);
    }
  };
}

function iniciarPolling(intento) {
  if (estado.modo === "polling") return;
  cerrarWebSocket();
  estado.modo = "polling";

  const pedir = async () => {
    if (intento !== estado.intento) return;
    try {
      const r = await fetch(`${estado.base}/telemetria`, { cache: "no-store" });
      if (r.ok && intento === estado.intento) recibir(await r.json());
    } catch {
      // No hace falta hacer nada: si dejan de llegar datos, la pastilla lo avisa.
    }
    // El próximo pedido sale cuando terminó éste: nunca se apilan. Ver ADR-0002.
    if (intento === estado.intento) programar(pedir, INTERVALO_POLLING_MS);
  };
  pedir();
}

function desconectar() {
  estado.timers.forEach(clearTimeout);
  estado.timers = [];
  cerrarWebSocket();
  estado.modo = null;
  estado.ultimo = null;
  estado.historial = [];
  estado.llegadas = [];
  estado.ultimaLlegada = 0;
  estado.ultimoAvance = 0;
  $("frecuencia").textContent = "";
}

function cerrarWebSocket() {
  if (!estado.ws) return;
  estado.ws.onmessage = null;
  estado.ws.onclose = null;
  estado.ws.close();
  estado.ws = null;
}

function programar(fn, ms) {
  estado.timers.push(setTimeout(fn, ms));
}


/* ------------------------------------------------------------------ */
/* 2. Armar la pantalla según el robot                                 */
/* ------------------------------------------------------------------ */

function armarPantalla(info) {
  $("robot-nombre").textContent = info.nombre;
  $("robot-detalle").textContent =
    `${info.tipo} · ${info.n_motores} motores · ${info.modo === "simulador" ? "simulador" : "robot real"}`;

  const esSimulador = info.modo === "simulador";
  $("aviso-simulador").hidden = !esSimulador;
  document.querySelectorAll("[data-origen]").forEach((el) => {
    const origen = esSimulador ? ORIGEN_EN_SIMULADOR[el.dataset.origen] : "";
    el.textContent = origen || "";
    el.className = origen ? `marca marca--${origen}` : "marca";
  });

  armarSelector(info.motores_nombres);
  armarTabla(info.motores_nombres);
}

function armarSelector(nombres) {
  // Por defecto: los motores que más se mueven al caminar (muslos y rodillas).
  const porDefecto = nombres
    .map((n, i) => (/thigh|knee/.test(n) ? i : -1))
    .filter((i) => i >= 0)
    .slice(0, 4);
  estado.seleccion = new Set(porDefecto.length ? porDefecto : [0, 1, 2, 3]);

  const cont = $("selector-motores");
  cont.replaceChildren();
  nombres.forEach((nombre, i) => {
    const chip = document.createElement("label");
    const casilla = document.createElement("input");
    const punto = document.createElement("span");
    casilla.type = "checkbox";
    casilla.checked = estado.seleccion.has(i);
    punto.className = "chip__color";
    chip.append(casilla, punto, nombre);

    const pintar = () => {
      chip.className = casilla.checked ? "chip chip--activo" : "chip";
      punto.style.background = casilla.checked ? colorDe(i) : "";
    };
    casilla.addEventListener("change", () => {
      if (casilla.checked) estado.seleccion.add(i);
      else estado.seleccion.delete(i);
      pintar();
    });
    pintar();
    cont.append(chip);
  });
}

function armarTabla(nombres) {
  // Las filas se crean UNA vez. Después sólo se cambia el texto (ver ADR-0004).
  const cuerpo = $("tabla-motores");
  cuerpo.replaceChildren();
  estado.celdas = nombres.map((nombre, i) => {
    const fila = cuerpo.insertRow();
    fila.insertCell().textContent = i;
    fila.insertCell().textContent = nombre;
    const celdas = {};
    for (const campo of ["angulo", "velocidad", "torque", "temperatura"]) {
      const td = fila.insertCell();
      td.className = "num";
      celdas[campo] = td;
    }
    celdas.temperatura.innerHTML = '<span class="temp">--</span>';
    celdas.temperatura = celdas.temperatura.firstChild;
    return celdas;
  });
}

const colorDe = (i) => COLORES[i % COLORES.length];


/* ------------------------------------------------------------------ */
/* 3. Recibir                                                          */
/* ------------------------------------------------------------------ */

function recibir(t) {
  const ahora = performance.now();
  // Si el simulador (o el robot) se cae, el backend sigue mandando el ÚLTIMO
  // dato una y otra vez. Que lleguen mensajes no alcanza: `ts` tiene que avanzar.
  if (!estado.ultimo || t.ts !== estado.ultimo.ts) estado.ultimoAvance = ahora;
  estado.ultimo = t;
  estado.hayNuevo = true;
  estado.ultimaLlegada = ahora;

  estado.llegadas.push(ahora);
  while (ahora - estado.llegadas[0] > 1000) estado.llegadas.shift();

  estado.historial.push({ t: ahora, angulos: t.motores.map((m) => m.angulo) });
  while (ahora - estado.historial[0].t > VENTANA_SEGUNDOS * 1000) estado.historial.shift();
}


/* ------------------------------------------------------------------ */
/* 4. Dibujar                                                          */
/* ------------------------------------------------------------------ */

function cuadro() {
  actualizarPastilla();
  if (estado.hayNuevo && estado.ultimo) {
    pintarDatos(estado.ultimo);
    estado.hayNuevo = false;
  }
  // El gráfico se redibuja siempre para que se desplace suave aunque no lleguen datos.
  dibujarGrafico();
  requestAnimationFrame(cuadro);
}

function actualizarPastilla() {
  if (!estado.modo) return;
  const ahora = performance.now();
  const porSegundo = estado.llegadas.filter((t) => ahora - t <= 1000).length;
  ponerTexto($("frecuencia"), `${porSegundo} datos/s`);

  if (!estado.ultimaLlegada) ponerEstado("esperando datos…", "apagado");
  else if (ahora - estado.ultimaLlegada > DATO_VIEJO_MS) ponerEstado("no llegan datos", "viejo");
  else if (ahora - estado.ultimoAvance > DATO_VIEJO_MS) ponerEstado("datos congelados", "viejo");
  else if (estado.modo === "websocket") ponerEstado("en vivo · WebSocket", "ok");
  else ponerEstado("en vivo · polling", "polling");
}

function pintarDatos(t) {
  // Batería
  const soc = t.bms?.soc ?? 0;
  ponerTexto($("bateria-valor"), String(Math.round(soc)));
  const relleno = $("bateria-relleno");
  relleno.style.width = `${Math.max(0, Math.min(100, soc))}%`;
  relleno.style.backgroundColor = soc > 50 ? "var(--ok)" : soc > 20 ? "var(--tibio)" : "var(--caliente)";

  // IMU
  const imu = t.imu ?? {};
  ponerTexto($("imu-roll"), grados(imu.roll));
  ponerTexto($("imu-pitch"), grados(imu.pitch));
  ponerTexto($("imu-yaw"), grados(imu.yaw));
  dibujarHorizonte(imu.roll ?? 0, imu.pitch ?? 0);

  // Patas
  dibujarPatas(t.fuerzas);

  // Tabla
  t.motores.forEach((m, i) => {
    const c = estado.celdas[i];
    if (!c) return;
    ponerTexto(c.angulo, m.angulo.toFixed(1));
    ponerTexto(c.velocidad, m.velocidad.toFixed(3));
    ponerTexto(c.torque, m.torque.toFixed(2));
    ponerTexto(c.temperatura, m.temperatura.toFixed(1));
    const nivel = m.temperatura >= TEMP_CALIENTE ? "caliente" : m.temperatura >= TEMP_TIBIA ? "tibio" : "ok";
    c.temperatura.className = `temp temp--${nivel}`;
  });
}

function dibujarHorizonte(roll, pitch) {
  const { ctx, w, h } = prepararLienzo($("horizonte"));
  const r = Math.min(w, h) / 2 - 4;
  const cx = w / 2, cy = h / 2;
  const pxPorGrado = r / 30;   // ±30° llenan el círculo

  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.clip();

  // Cielo y tierra: giran con el roll, suben/bajan con el pitch.
  ctx.translate(cx, cy);
  ctx.rotate((-roll * Math.PI) / 180);
  ctx.translate(0, pitch * pxPorGrado);
  ctx.fillStyle = "#1f4e79";
  ctx.fillRect(-2 * r, -4 * r, 4 * r, 4 * r);
  ctx.fillStyle = "#6b4a2b";
  ctx.fillRect(-2 * r, 0, 4 * r, 4 * r);
  ctx.strokeStyle = "#e6edf3";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(-2 * r, 0);
  ctx.lineTo(2 * r, 0);
  ctx.stroke();

  // Marcas cada 10° de pitch
  ctx.lineWidth = 1;
  ctx.fillStyle = "#e6edf3";
  ctx.font = "10px system-ui";
  ctx.textBaseline = "middle";
  for (const g of [-20, -10, 10, 20]) {
    const y = -g * pxPorGrado;
    ctx.beginPath();
    ctx.moveTo(-r * 0.2, y);
    ctx.lineTo(r * 0.2, y);
    ctx.stroke();
    ctx.fillText(String(g), r * 0.24, y);
  }
  ctx.restore();

  // El "robot": fijo en el centro.
  ctx.strokeStyle = "#f0883e";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(cx - r * 0.5, cy);
  ctx.lineTo(cx - r * 0.15, cy);
  ctx.lineTo(cx, cy + r * 0.1);
  ctx.lineTo(cx + r * 0.15, cy);
  ctx.lineTo(cx + r * 0.5, cy);
  ctx.stroke();

  ctx.strokeStyle = "#2a3440";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.stroke();
}

function dibujarPatas(fuerzas) {
  const { ctx, w, h } = prepararLienzo($("patas"));
  const patas = Object.entries(fuerzas ?? {}).filter(([nombre]) => POSICION_PATAS[nombre]);

  // Por si algún robot no manda patas: en vez de un dibujo vacío, se explica.
  ponerTexto($("patas-nota"), patas.length ? "vista desde arriba · frente hacia arriba" : "Este robot no reporta qué patas están apoyadas.");
  if (!patas.length) return;

  const escala = Math.min(w, h) / 2 - 20;
  const cx = w / 2, cy = h / 2;

  // Cuerpo: un lomo largo para el perro, la cadera para el humanoide.
  const cuadrupedo = patas.length === 4;
  const anchoCuerpo = escala * (cuadrupedo ? 0.55 : 1.1);
  const largoCuerpo = escala * (cuadrupedo ? 1.5 : 0.45);
  ctx.fillStyle = "#2a3440";
  ctx.beginPath();
  ctx.roundRect(cx - anchoCuerpo / 2, cy - largoCuerpo / 2, anchoCuerpo, largoCuerpo, 10);
  ctx.fill();
  ctx.fillStyle = "#8b98a5";
  ctx.font = "11px system-ui";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const yFrente = cuadrupedo ? cy - largoCuerpo / 2 + 12 : cy - largoCuerpo / 2 - 14;
  ctx.fillText("▲ frente", cx, yFrente);

  for (const [nombre, apoyada] of patas) {
    const [px, py] = POSICION_PATAS[nombre];
    const x = cx + px * escala, y = cy + py * escala;
    ctx.beginPath();
    ctx.arc(x, y, 16, 0, Math.PI * 2);
    if (apoyada) {
      ctx.fillStyle = "#3fb950";
      ctx.fill();
    } else {
      ctx.strokeStyle = "#8b98a5";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    ctx.fillStyle = apoyada ? "#0f1419" : "#8b98a5";
    ctx.font = "bold 11px system-ui";
    ctx.fillText(nombre.replace("_foot", ""), x, y);
  }
}

function dibujarGrafico() {
  const { ctx, w, h } = prepararLienzo($("grafico"));
  const m = { izq: 48, der: 12, arr: 8, abj: 24 };
  const ancho = w - m.izq - m.der;
  const alto = h - m.arr - m.abj;
  const ahora = performance.now();
  const seleccion = [...estado.seleccion];
  const historial = estado.historial;

  // Eje Y: se ajusta a los motores elegidos, con un mínimo de 10°.
  let min = Infinity, max = -Infinity;
  for (const p of historial) {
    for (const i of seleccion) {
      const v = p.angulos[i];
      if (v < min) min = v;
      if (v > max) max = v;
    }
  }
  if (!Number.isFinite(min)) { min = -90; max = 90; }
  if (max - min < 10) { const c = (max + min) / 2; min = c - 5; max = c + 5; }
  const margen = (max - min) * 0.08;
  min -= margen;
  max += margen;

  const x = (t) => m.izq + ancho * (1 - (ahora - t) / (VENTANA_SEGUNDOS * 1000));
  const y = (v) => m.arr + alto * (1 - (v - min) / (max - min));

  // Grilla
  ctx.font = "11px system-ui";
  ctx.fillStyle = "#8b98a5";
  ctx.strokeStyle = "#2a3440";
  ctx.lineWidth = 1;
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  const paso = pasoRedondo((max - min) / 5);
  for (let v = Math.ceil(min / paso) * paso; v <= max; v += paso) {
    const yy = Math.round(y(v)) + 0.5;
    ctx.beginPath();
    ctx.moveTo(m.izq, yy);
    ctx.lineTo(w - m.der, yy);
    ctx.stroke();
    ctx.fillText(`${Number(v.toFixed(1))}°`, m.izq - 6, yy);
  }
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  for (let s = 0; s <= VENTANA_SEGUNDOS; s += 5) {
    ctx.fillText(s === 0 ? "ahora" : `-${s} s`, x(ahora - s * 1000), h - m.abj + 6);
  }

  if (!historial.length) {
    ctx.textBaseline = "middle";
    ctx.fillText("esperando datos…", m.izq + ancho / 2, m.arr + alto / 2);
    return;
  }

  // Líneas
  ctx.save();
  ctx.beginPath();
  ctx.rect(m.izq, m.arr, ancho, alto);
  ctx.clip();
  ctx.lineWidth = 1.75;
  ctx.lineJoin = "round";
  for (const i of seleccion) {
    ctx.strokeStyle = colorDe(i);
    ctx.beginPath();
    historial.forEach((p, k) => {
      const px = x(p.t), py = y(p.angulos[i]);
      if (k === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
  }
  ctx.restore();
}


/* ------------------------------------------------------------------ */
/* 5. Ayudas                                                           */
/* ------------------------------------------------------------------ */

// Ajusta la resolución interna del canvas a su tamaño en pantalla, para que
// no se vea borroso en pantallas retina. Devuelve el contexto limpio.
function prepararLienzo(canvas) {
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  const anchoReal = Math.round(w * dpr);
  const altoReal = Math.round(h * dpr);
  if (canvas.width !== anchoReal || canvas.height !== altoReal) {
    canvas.width = anchoReal;
    canvas.height = altoReal;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  return { ctx, w, h };
}

// 1, 2, 5, 10, 20, 50… : los pasos que usaría una persona para una escala.
function pasoRedondo(bruto) {
  const potencia = 10 ** Math.floor(Math.log10(bruto));
  const f = bruto / potencia;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * potencia;
}

const grados = (v) => (typeof v === "number" ? `${v.toFixed(1)}°` : "--");

// Tocar el DOM sólo si el texto cambió.
function ponerTexto(el, texto) {
  if (el.textContent !== texto) el.textContent = texto;
}

function ponerEstado(texto, tipo) {
  const el = $("estado");
  ponerTexto(el, texto);
  const clase = `pastilla pastilla--${tipo}`;
  if (el.className !== clase) el.className = clase;
}

function recordarHost(host) {
  try { localStorage.setItem("tp05-host", host); } catch { /* modo privado */ }
}

function hostRecordado() {
  try { return localStorage.getItem("tp05-host"); } catch { return null; }
}


/* ------------------------------------------------------------------ */
/* Arranque                                                            */
/* ------------------------------------------------------------------ */

$("form-conexion").addEventListener("submit", (e) => {
  e.preventDefault();
  conectar($("ip").value.trim() || "localhost");
});

const hostInicial = new URLSearchParams(location.search).get("ip") || hostRecordado() || "localhost";
$("ip").value = hostInicial;
conectar(hostInicial);
requestAnimationFrame(cuadro);
