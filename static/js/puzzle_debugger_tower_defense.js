(() => {
  const boot = window.DEBUGGER_TD_BOOT || {};
  const canvas = document.getElementById("td-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  const ui = {
    wave: document.getElementById("td-wave"),
    credits: document.getElementById("td-credits"),
    lives: document.getElementById("td-lives"),
    kills: document.getElementById("td-kills"),
    status: document.getElementById("td-status"),
    start: document.getElementById("td-start"),
    save: document.getElementById("td-save"),
    reset: document.getElementById("td-reset"),
  };

  const baseState = {
    wave: 1,
    credits: 120,
    lives: 20,
    kills: 0,
    highWave: 1,
    awardedXp: false,
    towers: [],
  };

  let state = { ...baseState };
  let bugs = [];
  let shots = [];
  let waveInProgress = false;
  let spawnRemaining = 0;
  let spawnTimer = 0;
  let lastTime = performance.now();

  const gridSize = 40;
  const mapOffset = { x: 10, y: 10 };
  const mapWidth = 800;
  const mapHeight = 440;
  const pathWidth = 52;
  const towerCost = 25;

  const pathPoints = [
    { x: mapOffset.x, y: mapOffset.y + 220 },
    { x: mapOffset.x + 200, y: mapOffset.y + 220 },
    { x: mapOffset.x + 200, y: mapOffset.y + 120 },
    { x: mapOffset.x + 420, y: mapOffset.y + 120 },
    { x: mapOffset.x + 420, y: mapOffset.y + 320 },
    { x: mapOffset.x + 640, y: mapOffset.y + 320 },
    { x: mapOffset.x + 640, y: mapOffset.y + 180 },
    { x: mapOffset.x + 800, y: mapOffset.y + 180 },
  ];

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

  const pointToSegmentDistance = (point, a, b) => {
    const lengthSquared = (b.x - a.x) ** 2 + (b.y - a.y) ** 2;
    if (lengthSquared === 0) return distance(point, a);
    let t =
      ((point.x - a.x) * (b.x - a.x) + (point.y - a.y) * (b.y - a.y)) /
      lengthSquared;
    t = clamp(t, 0, 1);
    const projection = {
      x: a.x + t * (b.x - a.x),
      y: a.y + t * (b.y - a.y),
    };
    return distance(point, projection);
  };

  const isOnPath = (point) => {
    for (let i = 0; i < pathPoints.length - 1; i += 1) {
      const d = pointToSegmentDistance(point, pathPoints[i], pathPoints[i + 1]);
      if (d <= pathWidth / 2 - 4) {
        return true;
      }
    }
    return false;
  };

  const formatStatus = (text) => {
    if (ui.status) {
      ui.status.textContent = `Status: ${text}`;
    }
  };

  const syncUI = () => {
    if (ui.wave) ui.wave.textContent = state.wave;
    if (ui.credits) ui.credits.textContent = state.credits;
    if (ui.lives) ui.lives.textContent = state.lives;
    if (ui.kills) ui.kills.textContent = state.kills;
  };

  const serializeState = () => ({
    wave: state.wave,
    credits: state.credits,
    lives: state.lives,
    kills: state.kills,
    highWave: state.highWave,
    awardedXp: state.awardedXp,
    towers: state.towers.map((tower) => ({ ...tower })),
  });

  const hydrateState = (payload) => {
    if (!payload) return;
    state = { ...baseState, ...payload };
  };

  const createBug = () => ({
    position: { ...pathPoints[0] },
    segmentIndex: 0,
    progress: 0,
    speed: 40 + state.wave * 4,
    health: 30 + state.wave * 8,
    maxHealth: 30 + state.wave * 8,
    slowed: 0,
  });

  const startWave = () => {
    if (waveInProgress || state.lives <= 0) return;
    waveInProgress = true;
    spawnRemaining = 5 + state.wave * 2;
    spawnTimer = 0;
    formatStatus(`Wave ${state.wave} engaged.`);
  };

  const completeWave = () => {
    waveInProgress = false;
    state.wave += 1;
    state.highWave = Math.max(state.highWave, state.wave);
    state.credits += 30 + state.wave * 4;
    formatStatus(`Wave cleared. Prep for wave ${state.wave}.`);
    if (state.wave >= 3 && !state.awardedXp) {
      awardXp();
      state.awardedXp = true;
    }
  };

  const awardXp = async () => {
    if (!boot.completeUrl) return;
    try {
      await fetch(boot.completeUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ puzzle_name: boot.puzzleName }),
      });
    } catch (error) {
      console.error("XP award failed", error);
    }
  };

  const saveState = async () => {
    if (!boot.saveUrl) return;
    formatStatus("Saving progress...");
    try {
      const response = await fetch(boot.saveUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: serializeState() }),
      });
      if (!response.ok) throw new Error("Save failed");
      formatStatus("Progress saved to server.");
    } catch (error) {
      console.error(error);
      formatStatus("Save failed. Try again.");
    }
  };

  const loadState = async () => {
    if (boot.savedState) {
      hydrateState(boot.savedState);
      syncUI();
      return;
    }
    if (!boot.loadUrl) return;
    try {
      const response = await fetch(boot.loadUrl);
      if (!response.ok) throw new Error("Load failed");
      const payload = await response.json();
      hydrateState(payload.state);
      syncUI();
    } catch (error) {
      console.error(error);
      formatStatus("Load failed. Starting fresh.");
    }
  };

  const resetRun = () => {
    state = { ...baseState };
    bugs = [];
    shots = [];
    waveInProgress = false;
    spawnRemaining = 0;
    syncUI();
    formatStatus("Run reset. Ready to deploy.");
  };

  const drawGrid = () => {
    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 1;
    for (let x = 0; x <= mapWidth; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(mapOffset.x + x, mapOffset.y);
      ctx.lineTo(mapOffset.x + x, mapOffset.y + mapHeight);
      ctx.stroke();
    }
    for (let y = 0; y <= mapHeight; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(mapOffset.x, mapOffset.y + y);
      ctx.lineTo(mapOffset.x + mapWidth, mapOffset.y + y);
      ctx.stroke();
    }
  };

  const drawPath = () => {
    ctx.strokeStyle = "rgba(90,200,255,0.35)";
    ctx.lineWidth = pathWidth;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(pathPoints[0].x, pathPoints[0].y);
    for (let i = 1; i < pathPoints.length; i += 1) {
      ctx.lineTo(pathPoints[i].x, pathPoints[i].y);
    }
    ctx.stroke();
  };

  const drawTowers = () => {
    state.towers.forEach((tower) => {
      ctx.fillStyle = "rgba(76, 233, 203, 0.9)";
      ctx.beginPath();
      ctx.arc(tower.x, tower.y, 12, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = "rgba(76, 233, 203, 0.2)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(tower.x, tower.y, tower.range, 0, Math.PI * 2);
      ctx.stroke();
    });
  };

  const drawBugs = () => {
    bugs.forEach((bug) => {
      ctx.fillStyle = bug.slowed > 0 ? "rgba(255, 191, 0, 0.9)" : "rgba(255, 107, 107, 0.9)";
      ctx.beginPath();
      ctx.arc(bug.position.x, bug.position.y, 10, 0, Math.PI * 2);
      ctx.fill();

      const healthWidth = 26;
      ctx.fillStyle = "rgba(0,0,0,0.4)";
      ctx.fillRect(bug.position.x - 13, bug.position.y - 18, healthWidth, 4);
      ctx.fillStyle = "rgba(69,240,200,0.9)";
      ctx.fillRect(
        bug.position.x - 13,
        bug.position.y - 18,
        (bug.health / bug.maxHealth) * healthWidth,
        4
      );
    });
  };

  const drawShots = () => {
    shots.forEach((shot) => {
      ctx.strokeStyle = "rgba(255,255,255,0.6)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(shot.from.x, shot.from.y);
      ctx.lineTo(shot.to.x, shot.to.y);
      ctx.stroke();
    });
  };

  const updateBugs = (dt) => {
    bugs.forEach((bug) => {
      let speed = bug.speed;
      if (bug.slowed > 0) {
        speed *= 0.6;
        bug.slowed -= dt;
      }
      const a = pathPoints[bug.segmentIndex];
      const b = pathPoints[bug.segmentIndex + 1];
      const segmentLength = distance(a, b);
      bug.progress += (speed * dt) / segmentLength;
      if (bug.progress >= 1) {
        bug.segmentIndex += 1;
        bug.progress = 0;
        if (bug.segmentIndex >= pathPoints.length - 1) {
          bug.reachedEnd = true;
          return;
        }
      }
      const current = pathPoints[bug.segmentIndex];
      const next = pathPoints[bug.segmentIndex + 1];
      bug.position.x = current.x + (next.x - current.x) * bug.progress;
      bug.position.y = current.y + (next.y - current.y) * bug.progress;
    });

    const escaped = bugs.filter((bug) => bug.reachedEnd);
    if (escaped.length) {
      state.lives = Math.max(0, state.lives - escaped.length);
      formatStatus("Bugs breached! Patch the leak.");
    }
    bugs = bugs.filter((bug) => !bug.reachedEnd && bug.health > 0);
    if (state.lives <= 0) {
      waveInProgress = false;
      formatStatus("System compromised. Reset to try again.");
    }
  };

  const updateTowers = (dt) => {
    state.towers.forEach((tower) => {
      tower.cooldown = Math.max(0, tower.cooldown - dt);
      if (tower.cooldown > 0) return;
      const target = bugs.find((bug) => distance(tower, bug.position) <= tower.range);
      if (!target) return;
      target.health -= tower.damage;
      target.slowed = Math.max(target.slowed, 0.6);
      tower.cooldown = tower.fireRate;
      shots.push({
        from: { x: tower.x, y: tower.y },
        to: { x: target.position.x, y: target.position.y },
        ttl: 0.15,
      });
      if (target.health <= 0) {
        state.kills += 1;
        state.credits += 6;
      }
    });
  };

  const updateShots = (dt) => {
    shots.forEach((shot) => {
      shot.ttl -= dt;
    });
    shots = shots.filter((shot) => shot.ttl > 0);
  };

  const updateWave = (dt) => {
    if (!waveInProgress || state.lives <= 0) return;
    spawnTimer -= dt;
    if (spawnRemaining > 0 && spawnTimer <= 0) {
      bugs.push(createBug());
      spawnRemaining -= 1;
      spawnTimer = 0.7;
    }
    if (spawnRemaining === 0 && bugs.length === 0) {
      completeWave();
    }
  };

  const render = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawPath();
    drawGrid();
    drawTowers();
    drawBugs();
    drawShots();
  };

  const tick = (timestamp) => {
    const dt = Math.min(0.033, (timestamp - lastTime) / 1000);
    lastTime = timestamp;
    updateWave(dt);
    updateBugs(dt);
    updateTowers(dt);
    updateShots(dt);
    syncUI();
    render();
    requestAnimationFrame(tick);
  };

  const placeTower = (event) => {
    const rect = canvas.getBoundingClientRect();
    const x = clamp(event.clientX - rect.left, mapOffset.x, mapOffset.x + mapWidth);
    const y = clamp(event.clientY - rect.top, mapOffset.y, mapOffset.y + mapHeight);
    const snapped = {
      x: mapOffset.x + Math.round((x - mapOffset.x) / gridSize) * gridSize,
      y: mapOffset.y + Math.round((y - mapOffset.y) / gridSize) * gridSize,
    };

    if (isOnPath(snapped)) {
      formatStatus("That tile is reserved for bug traffic.");
      return;
    }
    if (state.credits < towerCost) {
      formatStatus("Insufficient credits for deployment.");
      return;
    }
    if (state.towers.some((tower) => distance(tower, snapped) < 30)) {
      formatStatus("Tower spacing too tight.");
      return;
    }
    state.credits -= towerCost;
    state.towers.push({
      x: snapped.x,
      y: snapped.y,
      range: 110,
      fireRate: 0.45,
      damage: 12,
      cooldown: 0,
    });
    formatStatus("Tower deployed.");
  };

  canvas.addEventListener("click", placeTower);
  if (ui.start) ui.start.addEventListener("click", startWave);
  if (ui.save) ui.save.addEventListener("click", saveState);
  if (ui.reset) ui.reset.addEventListener("click", resetRun);

  loadState().then(() => {
    syncUI();
    formatStatus("Ready to deploy debugger towers.");
  });
  requestAnimationFrame(tick);
})();
