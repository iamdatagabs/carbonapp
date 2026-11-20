/* Static dashboard client. Configure window.CARBONAPP_API_BASE before app.js when hosted separately. */
(() => {
  const base = (window.CARBONAPP_API_BASE || "").replace(/\/$/, "");
  const $ = (id) => document.getElementById(id);
  const target = $("target"), point = $("point"), status = $("status");
  let summaryCache = null;

  async function get(path) {
    const response = await fetch(base + path);
    if (!response.ok) {
      const detail = await response.text();
      throw new Error(`API ${response.status}: ${detail}`);
    }
    return response.json();
  }

  function drawVertical(layers, selectedTarget) {
    const valid = layers.filter((layer) => layer.value !== null);
    const trace = {
      type: "bar", orientation: "h",
      y: valid.map((x) => `${x.code} · ${x.top_cm}–${x.bottom_cm} cm`),
      x: valid.map((x) => x.value),
      marker: {color: "#71866b"},
      customdata: valid.map((x) => [x.top_cm, x.bottom_cm, x.n_sample_numbers]),
      hovertemplate: "%{y}<br>Valor: %{x:.3f}<br>Sample Numbers: %{customdata[2]}<extra></extra>"
    };
    Plotly.react("vertical", [trace], {
      margin: {l: 120, r: 20, t: 12, b: 48},
      xaxis: {title: selectedTarget, zeroline: true},
      yaxis: {autorange: "reversed"},
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: {color: "#26352d"}
    }, {responsive: true, displayModeBar: false});
  }

  async function refresh() {
    try {
      status.textContent = "Atualizando…";
      const selectedTarget = target.value;
      const [summary, cloud] = await Promise.all([
        get(`/api/v1/dataset/summary?target=${selectedTarget}`),
        get(`/api/v1/profiles-3d?target=${selectedTarget}`)
      ]);
      summaryCache = summary;
      $("rows").textContent = summary.n_rows.toLocaleString("pt-BR");
      $("points").textContent = summary.n_points.toLocaleString("pt-BR");
      $("bands").textContent = summary.n_spectral_bands.toLocaleString("pt-BR");
      const current = point.value;
      const ids = cloud.point_ids;
      point.innerHTML = '<option value="">Todos os pontos</option>' + ids.map((id) => `<option value="${encodeURIComponent(id)}">${id}</option>`).join("");
      if (current && ids.includes(decodeURIComponent(current))) point.value = current;
      if (point.value) {
        const id = decodeURIComponent(point.value);
        const profile = await get(`/api/v1/profiles/${encodeURIComponent(id)}?target=${selectedTarget}`);
        drawVertical(profile.layers, selectedTarget);
      } else {
        drawVertical(summary.profile_summary.map((x) => ({
          code: x.code, top_cm: x.top_cm, bottom_cm: x.bottom_cm, value: x.mean,
          n_sample_numbers: x.n_points
        })), selectedTarget);
      }
      Plotly.react("threeD", [{
        type: "scatter3d", mode: "markers",
        x: cloud.x, y: cloud.y, z: cloud.z,
        text: cloud.points.map((p) => `Ponto ${p.point_id} · camada ${p.depth_code} · ${p.top_cm}–${p.bottom_cm} cm`),
        marker: {size: 4, color: cloud.y, colorscale: "Earth", showscale: true,
          colorbar: {title: selectedTarget}},
        hovertemplate: "%{text}<br>Valor: %{y:.3f}<extra></extra>"
      }], {
        margin: {l: 0, r: 0, t: 8, b: 0},
        scene: {
          xaxis: {title: "Ponto (índice categórico)", tickmode: "array", tickvals: ids.map((_,i)=>i), ticktext: ids},
          yaxis: {title: selectedTarget}, zaxis: {title: "Profundidade (cm)"},
          aspectmode: "manual", aspectratio: {x: 1.4, y: 1, z: 1.5}
        }, paper_bgcolor: "rgba(0,0,0,0)", font: {color: "#26352d"}
      }, {responsive: true, displayModeBar: false});
      status.textContent = `API conectada · ${cloud.points.length} pontos camada`;
    } catch (error) {
      status.textContent = error.message;
    }
  }

  target.addEventListener("change", refresh);
  point.addEventListener("change", refresh);
  refresh();
})();
