/* Static scientific explorer for CarbonApp. */
(() => {
  const base = (window.CARBONAPP_API_BASE || "").replace(/\/$/, "");
  const $ = (id) => document.getElementById(id);
  const target = $("target"), status = $("status");
  const targetCache = new Map(), profileCache = new Map();
  let current = null, catalogRows = [];

  async function get(path) {
    const response = await fetch(base + path);
    if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`);
    return response.json();
  }

  async function loadTarget(selectedTarget) {
    if (targetCache.has(selectedTarget)) return targetCache.get(selectedTarget);
    const health = await get("/health");
    if (!health.dataset_configured) throw new Error("API disponível, mas o conjunto de dados não está configurado no servidor.");
    const [summary, cloud] = await Promise.all([
      get(`/api/v1/dataset/summary?target=${selectedTarget}`),
      get(`/api/v1/profiles-3d?target=${selectedTarget}`)
    ]);
    const data = {summary, cloud};
    targetCache.set(selectedTarget, data);
    return data;
  }

  async function loadProfile(pointId, selectedTarget) {
    const key = `${selectedTarget}::${pointId}`;
    if (!profileCache.has(key)) {
      profileCache.set(key, get(`/api/v1/profiles/${encodeURIComponent(pointId)}?target=${selectedTarget}`));
    }
    try { return await profileCache.get(key); }
    catch (error) { profileCache.delete(key); throw error; }
  }

  function drawCloud(cloud, selectedTarget) {
    Plotly.react("threeD", [{
      type: "scatter3d", mode: "markers", x: cloud.x, y: cloud.y, z: cloud.z,
      text: cloud.points.map(p => `Ponto ${p.point_id} · camada ${p.depth_code} · ${p.top_cm}–${p.bottom_cm} cm`),
      marker: {size: 4, color: cloud.y, colorscale: "Earth", showscale: true, colorbar: {title: selectedTarget}},
      hovertemplate: "%{text}<br>Valor: %{y:.3f}<extra></extra>"
    }], {
      margin: {l: 0, r: 0, t: 8, b: 0},
      scene: {xaxis: {title: "Ponto (índice categórico)", tickmode: "array",
        tickvals: cloud.point_ids.map((_, i) => i), ticktext: cloud.point_ids},
        yaxis: {title: selectedTarget}, zaxis: {title: "Profundidade (cm)"},
        aspectmode: "manual", aspectratio: {x: 1.4, y: 1, z: 1.5}},
      paper_bgcolor: "rgba(0,0,0,0)", font: {color: "#26352d"}
    }, {responsive: true, displayModeBar: false});
  }

  function selectedIds() {
    return Array.from($("pointsSelect").selectedOptions).map(option => option.value);
  }

  function updateSelectionOptions(ids) {
    const select = $("pointsSelect"), previous = new Set(selectedIds());
    select.replaceChildren();
    ids.forEach(id => {
      const option = new Option(id, id);
      option.selected = previous.has(id);
      select.add(option);
    });
    $("selectionHint").textContent = `${ids.length} pontos disponíveis · selecione um ou mais para comparar`;
  }

  function renderCatalog() {
    const query = $("catalogSearch").value.trim().toLocaleLowerCase("pt-BR");
    const rows = catalogRows.filter(row => row.point.toLocaleLowerCase("pt-BR").includes(query));
    const body = $("catalogBody");
    body.replaceChildren();
    rows.forEach(row => {
      const tr = document.createElement("tr");
      [row.point, String(row.observations), row.depths.join(", ")].forEach(value => {
        const td = document.createElement("td"); td.textContent = value; tr.append(td);
      });
      body.append(tr);
    });
    $("catalogCount").textContent = `${rows.length} de ${catalogRows.length} pontos`;
  }

  function buildCatalog(cloud) {
    const grouped = new Map();
    cloud.points.forEach(p => {
      if (!grouped.has(p.point_id)) grouped.set(p.point_id, {point: p.point_id, observations: 0, depths: []});
      const row = grouped.get(p.point_id);
      row.observations += 1;
      row.depths.push(p.depth_code);
    });
    catalogRows = Array.from(grouped.values()).sort((a,b) => a.point.localeCompare(b.point, "pt-BR", {numeric:true}));
    renderCatalog();
  }

  function drawComparison(profiles, selectedTarget) {
    const traces = profiles.map(profile => {
      const layers = profile.layers.filter(layer => layer.value !== null);
      return {type: "scatter", mode: "lines+markers", name: profile.point_id,
        x: layers.map(layer => layer.value),
        y: layers.map(layer => (layer.top_cm + layer.bottom_cm) / 2),
        customdata: layers.map(layer => [layer.top_cm, layer.bottom_cm, layer.n_sample_numbers]),
        hovertemplate: `Ponto ${profile.point_id}<br>Profundidade: %{customdata[0]}–%{customdata[1]} cm<br>${selectedTarget}: %{x:.4f}<br>n: %{customdata[2]}<extra></extra>`};
    });
    Plotly.react("comparison", traces, {
      margin: {l: 65, r: 20, t: 12, b: 52},
      xaxis: {title: selectedTarget}, yaxis: {title: "Profundidade (cm)", autorange: "reversed"},
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {color: "#26352d"}, legend: {orientation: "h", y: -0.22}
    }, {responsive: true, displayModeBar: true});
  }

  function downloadCsv(profiles, selectedTarget) {
    const lines = [["point_id","target","depth_code","top_cm","bottom_cm","midpoint_cm","value","n_sample_numbers"]];
    profiles.forEach(profile => profile.layers.forEach(layer => lines.push([
      profile.point_id, selectedTarget, layer.code, layer.top_cm, layer.bottom_cm,
      layer.midpoint_cm, layer.value ?? "", layer.n_sample_numbers
    ])));
    const csv = "\uFEFF" + lines.map(row => row.map(value => {
      const text = String(value ?? "");
      return /[",\n;]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
    }).join(",")).join("\r\n");
    const url = URL.createObjectURL(new Blob([csv], {type:"text/csv;charset=utf-8"}));
    const link = document.createElement("a");
    link.href = url; link.download = `carbonapp_${selectedTarget.toLowerCase()}_perfis.csv`;
    document.body.append(link); link.click(); link.remove(); URL.revokeObjectURL(url);
  }

  async function refreshComparison() {
    const ids = selectedIds();
    if (!ids.length) {
      $("comparisonHint").textContent = "Selecione pontos no catálogo para gerar a comparação.";
      Plotly.purge("comparison"); $("exportCsv").disabled = true; return;
    }
    $("comparisonHint").textContent = "Carregando perfis selecionados…";
    const profiles = await Promise.all(ids.map(id => loadProfile(id, target.value)));
    drawComparison(profiles, target.value);
    $("comparisonHint").textContent = `${profiles.length} perfis comparados · profundidade crescente para baixo`;
    $("exportCsv").disabled = false;
    $("exportCsv").onclick = () => downloadCsv(profiles, target.value);
  }

  async function refresh() {
    try {
      status.textContent = "Atualizando dados…";
      const selectedTarget = target.value;
      const data = await loadTarget(selectedTarget);
      current = data;
      $("rows").textContent = data.summary.n_rows.toLocaleString("pt-BR");
      $("points").textContent = data.summary.n_points.toLocaleString("pt-BR");
      $("bands").textContent = data.summary.n_spectral_bands.toLocaleString("pt-BR");
      updateSelectionOptions(data.cloud.point_ids);
      buildCatalog(data.cloud);
      drawCloud(data.cloud, selectedTarget);
      await refreshComparison();
      status.textContent = `API conectada · ${data.cloud.points.length} observações de perfil`;
    } catch (error) { status.textContent = error.message; }
  }

  target.addEventListener("change", refresh);
  $("pointsSelect").addEventListener("change", () => refreshComparison().catch(e => status.textContent = e.message));
  $("catalogSearch").addEventListener("input", renderCatalog);
  $("exportCsv").addEventListener("click", () => {});
  refresh();
})();
