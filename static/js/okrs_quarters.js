
//Script CSAT Quarter
document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);
  const quarterCharts = {};
  const metas = await fetchMetas(); // Pega metas dinâmicas do banco

  // Plugin para desenhar linha pontilhada da meta
  const linhaMetaPlugin = {
    id: 'linhaMetaCSAT',
    afterDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;
      const yMeta = metas.csat; // valor da meta

      if (yMeta != null) {
        const y = yScale.getPixelForValue(yMeta);
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(85, 251, 8, 0.4)';
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();
      }
    }
  };

  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/getMetas');
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  async function fetchCsatQuarter() {
    try {
      const res = await fetch('/okrs/csatQuarter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  async function atualizarGraficosQuarter() {
    const dados = await fetchCsatQuarter();
    if (dados.status !== "success") return;

    const quarters = dados.quarters;

    Object.entries(quarters).forEach(([q, info]) => {
      const ctx = document.getElementById(`grafico${q}CSAT`)?.getContext('2d');
      if (!ctx) return;

      if (quarterCharts[q]) {
        quarterCharts[q].data.labels = info.labels;
        quarterCharts[q].data.datasets[0].data = info.valores;
        quarterCharts[q].update();
      } else {
        quarterCharts[q] = new Chart(ctx, {
          type: 'line',
          data: {
            labels: info.labels,
            datasets: [{
              label: 'CSAT (%)',
              data: info.valores,
              backgroundColor: 'rgba(92, 0, 252, 0.6)',
              borderColor: '#673ab7',
              borderWidth: 1,
              tension: 0.3
            }]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { display: false },
              title: { display: false }
            },
            scales: {
              y: { beginAtZero: true, max: 100, ticks: { color: '#fff' } },
              x: { ticks: { color: '#fff' } }
            }
          },
          plugins: [linhaMetaPlugin] // adiciona a linha da meta em cada gráfico
        });
      }
    });
  }

  atualizarGraficosQuarter();
});


// Script TMA & TMS Quarter
// Script TMA & TMS Quarter
document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);
  const quarterChartsTMATMS = {};
  const metas = await fetchMetas();

  const linhaMetaPlugin = {
    id: 'linhaMetaTMATMS',
    afterDraw: (chart) => {
      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;

      ctx.save();

      if (metas.tma != null) {
        const y = yScale.getPixelForValue(metas.tma);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(76, 175, 80, 0.4)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      if (metas.tms != null) {
        const y = yScale.getPixelForValue(metas.tms);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(33, 150, 243, 0.4)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      ctx.restore();
    }
  };

  // Busca as metas no backend
  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/getMetas');
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  async function fetchCsatQuarterTMATMS() {
    try {
      const res = await fetch('/okrs/tmaTmsQuarter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  async function atualizarGraficosQuarterTMATMS() {
    const dados = await fetchCsatQuarterTMATMS();
    if (dados.status !== "success") return;

    const quarters = dados.quarters;

    Object.entries(quarters).forEach(([q, info]) => {
      const ctx = document.getElementById(`grafico${q}TMATMS`)?.getContext('2d');
      if (!ctx) return;

      if (quarterChartsTMATMS[q]) {
        quarterChartsTMATMS[q].data.labels = info.labels;
        quarterChartsTMATMS[q].data.datasets[0].data = info.tma;
        quarterChartsTMATMS[q].data.datasets[1].data = info.tms;
        quarterChartsTMATMS[q].update();
      } else {
        quarterChartsTMATMS[q] = new Chart(ctx, {
          type: 'line',
          data: {
            labels: info.labels,
            datasets: [
              {
                label: 'TMA',
                data: info.tma,
                borderColor: '#673ab7',
                backgroundColor: 'rgba(103, 58, 183, 0.4)',
                tension: 0.3
              },
              {
                label: 'TMS',
                data: info.tms,
                borderColor: '#03a9f4',
                backgroundColor: 'rgba(3, 169, 244, 0.3)',
                tension: 0.3
              }
            ]
          },
          options: {
            responsive: true,
            plugins: {
              legend: { position: 'top', labels: { color: '#fff' } },
              title: { display: false }
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  color: '#fff',
                  callback: function(value) {
                    const h = Math.floor(value / 60);
                    const m = Math.round(value % 60);
                    return `${h}h ${m}min`;
                  }
                }
              },
              x: { ticks: { color: '#fff' } }
            }
          },
          plugins: [linhaMetaPlugin]
        });
      }
    });
  }

  atualizarGraficosQuarterTMATMS();
});



