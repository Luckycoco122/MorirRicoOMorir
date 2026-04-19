const phrasesLeft = [
  { text: "El dinero no duerme", accent: false },
  { text: "MORIR RICO O MORIR", accent: true },
  { text: "Construye activos, no excusas", accent: false },
  { text: "Tu tiempo vale más que tu sueldo", accent: false },
  { text: "RICO O NADA", accent: true },
  { text: "Invierte en lo que no puedes perder", accent: false },
  { text: "El lujo es la meta", accent: false },
  { text: "LIBERTAD FINANCIERA", accent: true },
  { text: "Trabaja para vivir, no para sobrevivir", accent: false },
  { text: "Cada euro es un soldado", accent: false },
  { text: "ESCALA O MUERE", accent: true },
  { text: "Los pobres tienen excusas, los ricos tienen planes", accent: false },
  { text: "Hazlo grande o vete a casa", accent: false },
];

const phrasesCenter = [
  { text: "MORIR RICO O MORIR", accent: true },
  { text: "No hay plan B cuando el plan A es la riqueza", accent: false },
  { text: "EL PRECIO DE LA MEDIOCRIDAD", accent: true },
  { text: "es vivir sin haber intentado", accent: false },
  { text: "RICO O MUERTO", accent: true },
  { text: "Aquí no hay vuelta atrás", accent: false },
  { text: "La riqueza es una mentalidad", accent: false },
  { text: "CONSTRUYE UN IMPERIO", accent: true },
  { text: "o quédate como estás", accent: false },
  { text: "Tu legado empieza hoy", accent: false },
  { text: "MORIR RICO O MORIR", accent: true },
  { text: "Sin excusas. Sin límites.", accent: false },
];

const phrasesRight = [
  { text: "La riqueza premia a los valientes", accent: false },
  { text: "MILLONES O MISERIA", accent: true },
  { text: "Aprende lo que no enseñan en la escuela", accent: false },
  { text: "El mercado no espera", accent: false },
  { text: "SÉ EL 1%", accent: true },
  { text: "Fracasar es parte del precio", accent: false },
  { text: "La comodidad es el enemigo", accent: false },
  { text: "EMPIEZA HOY O NUNCA", accent: true },
  { text: "Los ricos piensan en activos", accent: false },
  { text: "Los demás piensan en gastos", accent: false },
  { text: "RICO O MORIR", accent: true },
  { text: "No hay término medio", accent: false },
];

const tickerItems = [
  "MORIR RICO O MORIR",
  "LIBERTAD FINANCIERA",
  "SIN EXCUSAS",
  "CONSTRUYE TU IMPERIO",
  "EL DINERO ES LA META",
  "RICO O NADA",
  "ESCALA SIN LÍMITES",
  "MORIR RICO O MORIR",
];

// --- Shared scroll velocity ---
let scrollVelocity = 0;      // extra speed added by user input
let touchStartY = 0;
let lastTouchY = 0;
let lastTouchTime = 0;

// Wheel
window.addEventListener('wheel', (e) => {
  e.preventDefault();
  scrollVelocity += e.deltaY * 0.04;
}, { passive: false });

// Touch
window.addEventListener('touchstart', (e) => {
  touchStartY = e.touches[0].clientY;
  lastTouchY = touchStartY;
  lastTouchTime = Date.now();
}, { passive: true });

window.addEventListener('touchmove', (e) => {
  const y = e.touches[0].clientY;
  const dy = lastTouchY - y;
  const dt = Date.now() - lastTouchTime || 1;
  scrollVelocity += dy * 0.06;
  lastTouchY = y;
  lastTouchTime = Date.now();
}, { passive: true });

// Keyboard arrows / space
window.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowDown' || e.key === ' ')  scrollVelocity += 40;
  if (e.key === 'ArrowUp')                      scrollVelocity -= 40;
});

function buildCol(id, phrases, baseSpeed, scrollMult) {
  const el = document.getElementById(id);
  const allPhrases = [...phrases, ...phrases, ...phrases, ...phrases];
  allPhrases.forEach(p => {
    const div = document.createElement('div');
    div.className = 'phrase-item' + (p.accent ? ' accent' : '');
    div.textContent = p.text;
    el.appendChild(div);
  });

  let offset = 0;
  const itemH = 65;
  const loopH = phrases.length * itemH;

  function animate() {
    // Base auto-scroll + user-driven velocity scaled per column
    const totalSpeed = baseSpeed + scrollVelocity * scrollMult;
    offset -= totalSpeed;
    // Seamless loop
    if (offset <= -loopH * 2) offset += loopH * 2;
    if (offset > 0)           offset -= loopH * 2;
    el.style.transform = `translateY(${offset}px)`;
    requestAnimationFrame(animate);
  }
  animate();
}

function buildTicker() {
  const el = document.getElementById('ticker');
  const items = [...tickerItems, ...tickerItems, ...tickerItems, ...tickerItems, ...tickerItems];
  items.forEach(t => {
    const span = document.createElement('span');
    span.className = 'ticker-item';
    span.innerHTML = t + ' <span class="ticker-sep">◆</span>';
    el.appendChild(span);
  });

  let offset = 0;
  const loopW = tickerItems.length * 222;

  function animate() {
    // Ticker also reacts slightly to scroll (goes faster when scrolling down)
    offset -= 1.2 + scrollVelocity * 0.15;
    if (Math.abs(offset) >= loopW * 2) offset += loopW * 2;
    el.style.transform = `translateX(${offset}px)`;
    requestAnimationFrame(animate);
  }
  animate();
}

// Decay loop — smoothly brings scrollVelocity back to 0
function decayLoop() {
  scrollVelocity *= 0.92;
  if (Math.abs(scrollVelocity) < 0.01) scrollVelocity = 0;
  requestAnimationFrame(decayLoop);
}
decayLoop();

// Each column gets a different scroll multiplier for parallax feel
buildCol('col-left',   phrasesLeft,   0.45, 0.6);
buildCol('col-center', phrasesCenter, 0.3,  1.0);
buildCol('col-right',  phrasesRight,  0.55, 0.75);
buildTicker();