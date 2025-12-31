//Metas globais para ser utilizada nas funções-->

  let metasGlobais = {};

  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/getMetas');
      metasGlobais = res.ok ? await res.json() : {};
    } catch (err) {
      console.error("Erro ao buscar metas:", err);
      metasGlobais = {};
    }
  }

  // Carrega as metas assim que o DOM estiver pronto
document.addEventListener("DOMContentLoaded", fetchMetas);
//Script que traz os Reabertos-->

  let chamadosReabertosCodigos = [];

  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/getMetas');
      return res.ok ? await res.json() : {};
    } catch (err) {
      console.error("Erro ao buscar metas:", err);
      return {};
    }
  }

  async function atualizarReabertos(dias) {
    const metas = await fetchMetas();

    fetch('/okrs/reabertosOkrs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias })
    })
    .then(response => response.json())
    .then(data => {
      const reabertosSpan = document.getElementById("chamado_reaberto");
      const percentualSpan = document.getElementById("percentual_reaberto");
      const icone = document.getElementById("icone_reaberto");

      if (data.status === "success") {
        const total = data.total_chamados || 0;
        const reabertos = data.total_reabertos || 0;
        chamadosReabertosCodigos = data.cod_chamados || [];

        reabertosSpan.textContent = reabertos;

        let percentual = "-";
        let percentualValor = 0;

        if (total > 0) {
          percentualValor = (reabertos / total) * 100;
          percentual = percentualValor.toFixed(1) + "%";
        }

        percentualSpan.textContent = percentual;

        // Avalia com a meta
        if (metas.reabertos != null && total > 0) {
          const meta = metas.reabertos;
          if (percentualValor <= meta) {
            icone.className = "bi bi-arrow-up-short text-success ms-2 fs-4";
            icone.title = "Dentro da meta";
          } else {
            icone.className = "bi bi-arrow-down-short text-danger ms-2 fs-4";
            icone.title = "Acima da meta";
          }
        } else {
          icone.className = "";
          icone.title = "";
        }

      } else {
        reabertosSpan.textContent = "Erro";
        percentualSpan.textContent = "-";
        chamadosReabertosCodigos = [];
        console.error("Erro na resposta:", data.message);
      }
    })
    .catch(error => {
      console.error("Erro ao buscar reabertos:", error);
      document.getElementById("chamado_reaberto").textContent = "Erro";
      document.getElementById("percentual_reaberto").textContent = "-";
      chamadosReabertosCodigos = [];
    });
  }

  function mostrarChamadosOperador(titulo, codigos) {
    const lista = document.getElementById("listaCodigos");
    const tituloModal = document.getElementById("modalCodigosLabel");

    if (!lista || !tituloModal) return;

    lista.innerHTML = "";
    tituloModal.textContent = titulo;

    if (!Array.isArray(codigos) || codigos.length === 0) {
      const item = document.createElement("li");
      item.className = "text-muted";
      item.textContent = "Nenhum chamado encontrado.";
      lista.appendChild(item);
    } else {
      codigos.forEach(codigo => {
        const li = document.createElement("li");
        li.style.marginBottom = "8px";

        const link = document.createElement("a");
        link.href = `https://comnect.desk.ms/?Ticket#ChamadosSuporte:${codigo}`;
        link.target = "_blank";
        link.textContent = codigo;
        link.style.color = "#ffc107";

        li.appendChild(link);
        lista.appendChild(li);
      });
    }

    const modal = new bootstrap.Modal(document.getElementById("modalCodigos"));
    modal.show();
  }

  // Inicialização padrão
  document.addEventListener("DOMContentLoaded", function () {
    atualizarReabertos(30); // valor padrão de dias

    // Filtro por dias
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        const dias = parseInt(this.getAttribute('data-dias'), 10);
        atualizarReabertos(dias);
      });
    });
  });


// Script que traz o TMA e TMS -->
// Script que traz o TMA e TMS -->
document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);

  // 🔹 Converte minutos em formato HH:MM
  function formatarMinutos(minutos) {
    if (minutos == null || isNaN(minutos)) return '-';
    const h = Math.floor(minutos / 60);
    const m = Math.floor(minutos % 60);
    return `${h}h ${m.toString().padStart(2, '0')}m`;
  }

  // 🔹 Converte minutos em formato HH:MM (para TMS)
  function formatarHoras(minutos) {
    if (minutos == null || isNaN(minutos)) return '-';
    const h = Math.floor(minutos / 60);
    const m = Math.floor(minutos % 60);
    return `${h}h ${m.toString().padStart(2, '0')}m`;
  }

  // Busca acumulado
  async function fetchAcumuladoTmaTms() {
    try {
      const res = await fetch('/okrs/tmaTmsAcumulado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias: 365 })
      });
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  // Busca metas
  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/getMetas');
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  // Busca dados do gráfico TMA/TMS
  async function fetchTmaTmsMensal(dias) {
    try {
      const res = await fetch('/okrs/tmaTmsMensal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })
      });
      const data = await res.json();
      return res.ok ? data : {};
    } catch {
      return {};
    }
  }

  // Atualiza setas e valores das metas nos cards
  function atualizarIndicadoresMetas(tmaMedio, tmsMedio, metas) {
    const metaTmaEl = document.getElementById("meta-tma");
    const metaTmsEl = document.getElementById("meta-tms");

    if (!metaTmaEl || !metaTmsEl) return;

    const setaTma = metaTmaEl.previousElementSibling;
    const setaTms = metaTmsEl.previousElementSibling;

    if (metas.tma != null) {
      setaTma.className = tmaMedio <= metas.tma
        ? "bi bi-arrow-up-circle text-success"
        : "bi bi-arrow-down-circle text-danger";
    }

    if (metas.tms != null) {
      setaTms.className = tmsMedio <= metas.tms
        ? "bi bi-arrow-up-circle text-success"
        : "bi bi-arrow-down-circle text-danger";
    }
  }

  // Plugin da linha pontilhada (metas TMA e TMS)
  const horizontalLinePluginTmaTms = {
    id: 'horizontalLineTmaTms',
    afterDraw: (chart) => {
      const metas = chart.options._metas;
      if (!metas) return;

      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;
      ctx.save();

      if (metas.tma != null) {
        const y = yScale.getPixelForValue(metas.tma);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(76, 175, 80, 0.5)';
        ctx.lineWidth = 2; 
        ctx.stroke();
      }

      if (metas.tms != null) {
        const y = yScale.getPixelForValue(metas.tms);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(33, 150, 243, 0.5)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      ctx.restore();
    }
  };

  // Atualiza gráfico e indicadores
  async function atualizarGraficoTmaTms(dias) {
    const [tmaTmsDados, metas, acumuladoDados] = await Promise.all([
      fetchTmaTmsMensal(dias),
      fetchMetas(),
      fetchAcumuladoTmaTms()
    ]);

    if (!tmaTmsDados.status || tmaTmsDados.status !== "success") {
      console.error("Erro ao carregar dados TMA/TMS");
      return;
    }

    const labels = tmaTmsDados.labels || [];
    const tma = tmaTmsDados.media_tma_min || [];
    const tms = tmaTmsDados.media_tms_min || []; // 🔹 mantido em minutos

    const tmaAcum = acumuladoDados.tma_acumulado_min || [];
    const tmsAcum = acumuladoDados.tms_acumulado_min || [];

    const ctx = document.getElementById('graficoTmaTms').getContext('2d');
    if (window.chartTmaTms) window.chartTmaTms.destroy();

    window.chartTmaTms = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'TMA (min)',
            data: tma,
            borderColor: '#4caf50',
            backgroundColor: 'rgba(76, 175, 80, 0.4)',
            borderWidth: 3,
          },
          {
            label: 'TMS (min)',
            data: tms,
            borderColor: '#2196f3',
            backgroundColor: 'rgba(33, 150, 243, 0.4)',
            borderWidth: 3,
          },
          {
            label: 'TMA Acumulado',
            data: tmaAcum,
            borderColor: '#4caf50',
            borderDash: [6, 6],
            borderWidth: 2,
            fill: false,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: 'TMS Acumulado',
            data: tmsAcum,
            borderColor: '#2196f3',
            borderDash: [6, 6],
            borderWidth: 2,
            fill: false,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'top', labels: { color: '#fff' } },
          tooltip: {
            callbacks: {
              label: function (context) {
                const label = context.dataset.label || '';
                const value = context.parsed.y;
                if (label.includes('TMA')) return `${label}: ${formatarMinutos(value)}`;
                if (label.includes('TMS')) return `${label}: ${formatarHoras(value)}`;
                return `${label}: ${value}`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              color: '#fff',
              callback: function (value) {
                return formatarMinutos(value);
              }
            }
          },
          x: { ticks: { color: '#fff' } }
        },
        _metas: metas
      },
      plugins: [horizontalLinePluginTmaTms]
    });

    const tmaMedio = tma.length ? tma.reduce((a, b) => a + b, 0) / tma.length : 0;
    const tmsMedio = tms.length ? tms.reduce((a, b) => a + b, 0) / tms.length : 0;
    atualizarIndicadoresMetas(tmaMedio, tmsMedio, metas);
  }

  atualizarGraficoTmaTms(30);

  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarGraficoTmaTms(dias);
    });
  });
});


//Script que traz a evolução do SLA com o passar dos periodos-->
document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);

  const metas = await fetchMetas();
  let chartSLA; // guardamos o gráfico aqui

  const horizontalLinePlugin = {
    id: 'horizontalLine',
    afterDraw: (chart) => {
      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;

      ctx.save();

      if (metas.sla_atendimento_prazo != null) {
        const y = yScale.getPixelForValue(metas.sla_atendimento_prazo);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(231, 251, 6, 0.3)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      if (metas.sla_resolucao_prazo != null) {
        const y = yScale.getPixelForValue(metas.sla_resolucao_prazo);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(244, 67, 54, 0.3)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      ctx.restore();
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

  async function fetchSlaMensal(dias) {
    try {
      const res = await fetch('/okrs/slaOkrsMes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })
      });
      const data = await res.json();
      return res.ok ? data : {};
    } catch {
      return {};
    }
  }

  async function fetchSlaAcumulado(dias) {
    try {
      const res = await fetch('/okrs/slaOkrsAcumulado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })
      });
      const data = await res.json();
      return res.ok ? data : {};
    } catch {
      return {};
    }
  }

  function atualizarIndicadoresSLA(mediaAtendimento, mediaResolucao) {
    const metaAtendimentoEl = document.getElementById("meta-sla-atendimento");
    const metaResolucaoEl = document.getElementById("meta-sla-solucao");

    if (metaAtendimentoEl) {
      const setaAt = metaAtendimentoEl.previousElementSibling;
      if (mediaAtendimento >= metas.sla_atendimento_prazo) {
        setaAt.className = "bi bi-arrow-up-circle text-success";
      } else {
        setaAt.className = "bi bi-arrow-down-circle text-danger";
      }
    }

    if (metaResolucaoEl) {
      const setaRes = metaResolucaoEl.previousElementSibling;
      if (mediaResolucao >= metas.sla_resolucao_prazo) {
        setaRes.className = "bi bi-arrow-up-circle text-success";
      } else {
        setaRes.className = "bi bi-arrow-down-circle text-danger";
      }
    }
  }

  async function atualizarGraficoSLA(dias) {
    const [slaDados, slaAcumDados] = await Promise.all([
      fetchSlaMensal(dias),
      fetchSlaAcumulado(dias)
    ]);

    const labels = slaDados.labels || [];
    const slaAtendimentoData = slaDados.sla_atendimento || [];
    const slaResolucaoData = slaDados.sla_resolucao || [];

    const slaAtendimentoAcum = slaAcumDados.sla_atendimento_acumulado || [];
    const slaResolucaoAcum = slaAcumDados.sla_resolucao_acumulado || [];

    if (!chartSLA) {
      const ctx = document.getElementById('graficoSLA').getContext('2d');
      chartSLA = new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'SLA Atendimento (%)',
              data: slaAtendimentoData,
              borderColor: '#dedb41',
              backgroundColor: 'rgba(231, 251, 6, 0.3)',
              borderWidth: 3,
              fill: true
            },
            {
              label: 'SLA Solução (%)',
              data: slaResolucaoData,
              borderColor: '#f44336',
              backgroundColor: 'rgba(244, 67, 54, 0.3)',
              borderWidth: 3,
              fill: true
            },
            {
              label: 'SLA Atendimento Acumulado (%)',
              data: slaAtendimentoAcum,
              borderColor: '#cddc39',
              borderWidth: 2,
              fill: false,
              tension: 0.3,
              pointRadius: 3
            },
            {
              label: 'SLA Solução Acumulado (%)',
              data: slaResolucaoAcum,
              borderColor: '#ff9800',
              borderWidth: 2,
              fill: false,
              tension: 0.3,
              pointRadius: 3
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'top', labels: { color: '#fff' } },
            tooltip: { mode: 'index', intersect: false }
          },
          interaction: { mode: 'index', intersect: false },
          scales: {
            y: { beginAtZero: true, max: 100, ticks: { color: '#fff', callback: v => `${v}%` } },
            x: { ticks: { color: '#fff' } }
          }
        },
        plugins: [horizontalLinePlugin]
      });
    } else {
      chartSLA.data.labels = labels;
      chartSLA.data.datasets[0].data = slaAtendimentoData;
      chartSLA.data.datasets[1].data = slaResolucaoData;
      chartSLA.data.datasets[2].data = slaAtendimentoAcum;
      chartSLA.data.datasets[3].data = slaResolucaoAcum;
      chartSLA.update();
    }

    const mediaAtendimento = slaAtendimentoData.length
      ? slaAtendimentoData.reduce((a, b) => a + b, 0) / slaAtendimentoData.length
      : 0;
    const mediaResolucao = slaResolucaoData.length
      ? slaResolucaoData.reduce((a, b) => a + b, 0) / slaResolucaoData.length
      : 0;

    atualizarIndicadoresSLA(mediaAtendimento, mediaResolucao);
  }

  atualizarGraficoSLA(30);

  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarGraficoSLA(dias);
    });
  });
});


// Script do gráfico de FCR (com FCR Acumulado)
document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);

  //  Busca metas do backend
  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/getMetas');
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  // Busca dados do FCR Mensal
  async function fetchFcrMensal(dias) {
    try {
      const res = await fetch('/okrs/fcrMensal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })
      });
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  // 🔹 Busca dados do FCR acumulado
  async function fetchFcrAcumulado(dias) {
    try {
      const res = await fetch('/okrs/fcrAcumulado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })
      });
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  // Plugin da linha de meta
  const linhaMetaFcrPlugin = {
    id: 'linhaMetaFCR',
    afterDraw(chart, args, options) {
      const metaFcr = options.metaFcr;
      if (metaFcr == null) return;

      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;
      const y = yScale.getPixelForValue(metaFcr);

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(chartArea.left, y);
      ctx.lineTo(chartArea.right, y);
      ctx.setLineDash([6, 6]);
      ctx.strokeStyle = 'rgba(255, 152, 0, 0.5)';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();

      // Desenha o rótulo "Meta"
      ctx.save();
      ctx.fillStyle = 'rgba(241, 145, 20, 0.8)';
      ctx.font = '12px sans-serif';
      ctx.fillText(`Meta FCR (${metaFcr}%)`, chartArea.right - 90, y - 5);
      ctx.restore();
    }
  };

  // Atualiza o gráfico (mensal + acumulado)
  async function atualizarGraficoFCR(dias) {
    const [metas, fcrDados, fcrAcumDados] = await Promise.all([
      fetchMetas(),
      fetchFcrMensal(dias),
      fetchFcrAcumulado(dias)
    ]);

    const labels = fcrDados.labels || [];
    const fcrData = fcrDados.fcr || [];

    // Alinha valores acumulados com as labels do mensal
    const acumLabels = fcrAcumDados.labels || [];
    const acumValues = fcrAcumDados.fcr_acumulado || [];
    const mapAcum = Object.fromEntries(acumLabels.map((l, i) => [l, acumValues[i]]));
    const fcrAcumAligned = labels.map(l => mapAcum[l] ?? null);

    // Atualiza valor e seta do card
    if (metas.fcr != null) {
      const metaEl = document.getElementById('meta-fcr');
      if (metaEl) metaEl.textContent = `${metas.fcr}%`;
      const icone = metaEl ? metaEl.previousElementSibling : null;
      if (icone && fcrData.length > 0) {
        const valorAtual = fcrData[fcrData.length - 1];
        icone.className = valorAtual >= metas.fcr
          ? 'bi bi-arrow-up-circle text-success'
          : 'bi bi-arrow-down-circle text-danger';
      }
    }

    const ctx = document.getElementById('graficoFCR').getContext('2d');
    if (window.chartFCR) window.chartFCR.destroy();

    // Criação do gráfico com plugin da linha de meta
    window.chartFCR = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'FCR (%)',
            data: fcrData,
            borderColor: '#ff9800',
            backgroundColor: 'rgba(255, 152, 0, 0.4)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 5,
            pointHoverRadius: 8
          },
          {
            label: 'FCR Acumulado (%)',
            data: fcrAcumAligned,
            borderColor: '#ffb74d',
            borderDash: [6, 6],
            borderWidth: 2,
            fill: false,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
            yAxisID: 'y'
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: 'top',
            labels: { color: '#fff' }
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label(context) {
                const label = context.dataset.label || '';
                const value = context.parsed.y;
                return value == null ? `${label}: -` : `${label}: ${value}%`;
              }
            }
          },
          //  Aqui passamos a meta para o plugin
          linhaMetaFCR: { metaFcr: metas.fcr }
        },
        interaction: { mode: 'index', intersect: false },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              color: '#fff',
              callback: (v) => `${v}%`
            }
          },
          x: { ticks: { color: '#fff' } }
        }
      },
      plugins: [linhaMetaFcrPlugin]
    });
  }

  // Inicializa com 30 dias
  atualizarGraficoFCR(30);

  // Eventos dos botões
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarGraficoFCR(dias);
    });
  });
});

//Script do gráfico de CSAT-->
document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);

  let csatMeta = 0;

  // 🔹 Busca metas do backend
  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/getMetas');
      const data = res.ok ? await res.json() : {};
      csatMeta = data.csat || 0; // salva meta para o plugin
      return data;
    } catch {
      csatMeta = 0;
      return {};
    }
  }

  // 🔹 Busca CSAT mensal
  async function fetchCsatMensal(dias) {
    try {
      const res = await fetch('/okrs/csatMensal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })
      });
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  // 🔹 Busca CSAT acumulado
  async function fetchCsatAcumulado(dias) {
    try {
      const res = await fetch('/okrs/csatAcumulado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })
      });
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  // 🔹 Plugin: desenha a linha pontilhada da meta
  const linhaMetaCsatPlugin = {
    id: 'linhaMetaCSAT',
    afterDatasetsDraw(chart) {
      if (!csatMeta) return;

      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;
      const y = yScale.getPixelForValue(csatMeta);

      // Linha pontilhada
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(chartArea.left, y);
      ctx.lineTo(chartArea.right, y);
      ctx.setLineDash([6, 6]);
      ctx.strokeStyle = '#673ab7';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();

      // Texto "Meta"
      ctx.save();
      ctx.font = "bold 12px sans-serif";
      ctx.fillStyle = '#673ab7';
      ctx.fillText(`Meta: ${csatMeta}%`, chartArea.right - 80, y - 8);
      ctx.restore();
    }
  };

  // 🔹 Atualiza o gráfico CSAT (mensal + acumulado)
  async function atualizarGraficoCSAT(dias) {
    const [metas, csatMensal, csatAcumDados] = await Promise.all([
      fetchMetas(),
      fetchCsatMensal(dias),
      fetchCsatAcumulado(dias)
    ]);

    const labels = csatMensal.labels || [];
    const csatData = csatMensal.csat || [];

    // Alinhamento dos dados acumulados
    const acumLabels = csatAcumDados.labels || [];
    const acumValues = csatAcumDados.csat_acumulado || [];
    const csatAcumAligned = labels.map(l => acumLabels.includes(l) ? acumValues[acumLabels.indexOf(l)] : null);

    // Atualiza valor no card
    if (csatMeta) {
      const metaEl = document.getElementById('meta-csat');
      if (metaEl) metaEl.textContent = `${csatMeta}%`;
      const icone = metaEl ? metaEl.previousElementSibling : null;
      if (icone && csatData.length > 0) {
        const valorAtual = csatData[csatData.length - 1];
        icone.className = valorAtual >= csatMeta
          ? 'bi bi-arrow-up-circle text-success'
          : 'bi bi-arrow-down-circle text-danger';
      }
    }

    // Criação / atualização do gráfico
    const ctx = document.getElementById('graficoCSAT').getContext('2d');
    if (window.chartCSAT) window.chartCSAT.destroy();

    window.chartCSAT = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: 'CSAT (%)', data: csatData, borderColor: '#673ab7', backgroundColor: 'rgba(103, 58, 183, 0.4)', borderWidth: 3 },
          { label: 'CSAT Acumulado (%)', data: csatAcumAligned, borderColor: '#b388ff', borderWidth: 2, fill: false, tension: 0.3 }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'top', labels: { color: '#fff' } },
          tooltip: {
            mode: 'index', intersect: false,
            callbacks: {
              label: (context) => {
                const label = context.dataset.label || '';
                const value = context.parsed.y;
                return value == null ? `${label}: -` : `${label}: ${value}%`;
              }
            }
          }
        },
        interaction: { mode: 'index', intersect: false },
        scales: {
          y: { beginAtZero: true, max: 100, ticks: { color: '#fff', callback: v => `${v}%` } },
          x: { ticks: { color: '#fff' } }
        }
      },
      plugins: [linhaMetaCsatPlugin]
    });
  }

  // Inicializa com 30 dias
  atualizarGraficoCSAT(30);

  // Eventos dos botões de filtro
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarGraficoCSAT(dias);
    });
  });
});



//Script que traz os chamados de first call resolution-->
  let chamadosFcrCodigos = [];

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        const dias = parseInt(this.getAttribute('data-dias'), 10);
        atualizarFCR(dias);
      });
    });

    // Atualiza com valor padrão ao carregar
    atualizarFCR(30); // 30 dias como padrão
  });

  async function atualizarFCR(dias, nomeOperador) {
    try {
      const res = await fetch('/okrs/fcrOkrs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })
      });

      const data = await res.json();

      const fcrSpan = document.getElementById("chamado_fcr");
      const percentualSpan = document.getElementById("percentual_fcr");
      const icone = document.getElementById("icone_fcr");

      if (data.status === "success") {
        const totalFcr = data.total_fcr || 0;
        const percentualRaw = data.percentual_fcr;
        const percentual = typeof percentualRaw === "number" ? percentualRaw.toFixed(1) + "%" : "-";
        const percentualValor = typeof percentualRaw === "number" ? percentualRaw : null;

        fcrSpan.textContent = totalFcr;
        percentualSpan.textContent = percentual;
        chamadosFcrCodigos = data.cod_chamados || [];

        // Buscar a meta e comparar
        const metaRes = await fetch('/okrs/getMetas');
        if (metaRes.ok) {
          const metas = await metaRes.json();
          const metaFcr = metas.fcr;

          if (metaFcr != null && percentualValor != null) {
            if (percentualValor >= metaFcr) {
              icone.className = "bi bi-arrow-up-short text-success ms-2 fs-4";
              icone.title = "Dentro da meta";
            } else {
              icone.className = "bi bi-arrow-down-short text-danger ms-2 fs-4";
              icone.title = "Abaixo da meta";
            }
          } else {
            icone.className = "";
            icone.title = "";
          }
        }

      } else {
        fcrSpan.textContent = "Erro";
        percentualSpan.textContent = "-";
        chamadosFcrCodigos = [];
        console.error("Erro na resposta:", data.message);
      }
    } catch (error) {
      console.error("Erro ao buscar FCR:", error);
      document.getElementById("chamado_fcr").textContent = "Erro";
      document.getElementById("percentual_fcr").textContent = "-";
      document.getElementById("icone_fcr").className = "";
      chamadosFcrCodigos = [];
    }
  }

  function mostrarChamadosOperador(titulo, codigos) {
    const lista = document.getElementById("listaCodigos");
    const tituloModal = document.getElementById("modalCodigosLabel");

    if (!lista || !tituloModal) return;

    lista.innerHTML = "";
    tituloModal.textContent = titulo;

    if (!Array.isArray(codigos) || codigos.length === 0) {
      const item = document.createElement("li");
      item.className = "text-muted";
      item.textContent = "Nenhum chamado encontrado.";
      lista.appendChild(item);
    } else {
      codigos.forEach(codigo => {
        const li = document.createElement("li");
        li.style.marginBottom = "8px";

        const link = document.createElement("a");
        link.href = `https://comnect.desk.ms/?Ticket#ChamadosSuporte:${codigo}`;
        link.target = "_blank";
        link.textContent = codigo;
        link.style.color = "#ffc107";

        li.appendChild(link);
        lista.appendChild(li);
      });
    }

    const modal = new bootstrap.Modal(document.getElementById("modalCodigos"));
    modal.show();
  }


//Script que traz o TMA e TMS-->

document.addEventListener("DOMContentLoaded", function () {
    let diasSelecionados = 30;
    carregarTmaTms(diasSelecionados);

    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        diasSelecionados = parseInt(this.getAttribute('data-dias'), 10);
        carregarTmaTms(diasSelecionados);
      });
    });
  });

function carregarTmaTms(dias) {
    fetch(`/okrs/tmaTmsOkrs?dias=${dias}`)
      .then(response => response.json())
      .then(data => {
        if (data.status === "success") {
          document.getElementById("percentual-tma").innerText = data.mediana_tma;
          document.getElementById("percentual-tms").innerText = data.mediana_tms;

          // Pega as metas para comparar
          fetch('/okrs/getMetas')
            .then(res => res.json())
            .then(metas => {
              atualizarIconeTmaTms("icone_tma", data.mediana_tma, metas.tma, "baixo"); // Quanto menor, melhor
              atualizarIconeTmaTms("icone_tms", data.mediana_tms, metas.tms, "baixo");
            });
        } else {
          console.error("Erro ao carregar TMA/TMS:", data.message);
        }
      })
      .catch(err => {
        console.error("Erro na requisição TMA/TMS:", err);
      });
  }

function atualizarIconeTmaTms(idIcone, valorTexto, metaTexto) {
  const icone = document.getElementById(idIcone);
  if (!icone) return;

  icone.className = "";

  // Extrai minutos do texto (ex: "1.5 h" -> 90, "12 min" -> 12)
  let valorMin = 0;

  if (valorTexto.includes("h")) {
    valorMin = parseFloat(valorTexto) * 60;
  } else if (valorTexto.includes("dias")) {
    valorMin = parseFloat(valorTexto) * 1440;
  } else {
    valorMin = parseFloat(valorTexto);
  }

  const metaMin = parseFloat(metaTexto);

  if (isNaN(valorMin) || isNaN(metaMin)) {
    icone.classList.add("d-none");
    return;
  }

  const margem = 5;

  if (valorMin <= metaMin) {
    // Melhor que a meta → seta para baixo verde
    icone.className = "bi bi-arrow-down-short text-success ms-2 fs-4";
  } else if (valorMin <= metaMin + margem) {
    // Aceitável (margem) → seta para baixo amarela
    icone.className = "bi bi-arrow-down-short text-warning ms-2 fs-4";
  } else {
    // Pior que a meta → seta para cima vermelha
    icone.className = "bi bi-arrow-up-short text-danger ms-2 fs-4";
  }
}

//Bloco que traz a relação de tempo maximo e minimo-->
  document.addEventListener("DOMContentLoaded", function () {

    // Chamada inicial para 1 dia
    atualizarTminTmax(1);

    // Atualiza ao clicar no botão de filtro de dias
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        const dias = parseInt(this.getAttribute('data-dias'), 10);
        atualizarTminTmax(dias);
      });
    });
  });

  function atualizarTminTmax(dias) {
    fetch('/okrs/tminTmaxOkrs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias })
    })
    .then(response => response.json())
    .then(data => {
      const spanTmin = document.getElementById("percentual-tma-ligacoes");
      const spanTmax = document.getElementById("percentual-tms-ligacoes");

      if (data.status === "success") {
        spanTmin.textContent = data.tmin_media || 0;
        spanTmax.textContent = data.tmax_media || 0;
      } else {
        spanTmin.textContent = "Erro";
        spanTmax.textContent = "Erro";
        console.error("Erro na resposta:", data.message);
      }
    })
    .catch(error => {
      console.error("Erro ao buscar TMIN/TMAX:", error);
      document.getElementById("percentual-tma-ligacoes").textContent = "Erro";
      document.getElementById("percentual-tms-ligacoes").textContent = "Erro";
    });
  }


//Script que traz o SLA expirados global-->
  let codigosAtendimento = [];
  let codigosResolucao = [];

  function mostrarCodigosSla(titulo, listaCodigos) {
    const lista = document.getElementById("listaCodigos");
    const tituloModal = document.getElementById("modalCodigosLabel");

    if (!lista || !tituloModal) {
      console.warn("Elemento do modal não encontrado.");
      return;
    }

    lista.innerHTML = "";
    tituloModal.textContent = titulo;

    if (!Array.isArray(listaCodigos) || listaCodigos.length === 0) {
      const item = document.createElement("li");
      item.className = "text-muted";
      item.textContent = "Nenhum chamado encontrado.";
      lista.appendChild(item);
    } else {
      listaCodigos.forEach(codigo => {
        const li = document.createElement("li");
        li.style.marginBottom = "8px";

        const link = document.createElement("a");
        link.href = `https://comnect.desk.ms/?Ticket#ChamadosSuporte:${codigo}`;
        link.target = "_blank";
        link.textContent = codigo;
        link.style.color = "#ffc107";

        li.appendChild(link);
        lista.appendChild(li);
      });
    }

    const modal = new bootstrap.Modal(document.getElementById("modalCodigos"));
    modal.show();
  }

  function carregarSlaGlobal(dias = 1) {
    fetch('/okrs/slaOkrs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias: dias })
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === "success") {
        // Atualiza os textos
        document.getElementById("sla_atendimento_expirado").textContent = data.percentual_atendimento + "%";
        document.getElementById("sla_atendimento_prazo").textContent = data.percentual_prazo_atendimento + "%";
        document.getElementById("sla_resolucao_expirado").textContent = data.percentual_resolucao + "%";
        document.getElementById("percentual_prazo_resolucao").textContent = data.percentual_prazo_resolucao + "%";

        codigosAtendimento = data.codigos_atendimento || [];
        codigosResolucao = data.codigos_resolucao || [];

        // Atualiza ícones com base na meta
        atualizarIcone("icone_prazo_atendimento", data.percentual_prazo_atendimento, data.meta_prazo_atendimento);
        atualizarIcone("icone_prazo_resolucao", data.percentual_prazo_resolucao, data.meta_prazo_resolucao);

      } else {
        document.getElementById("sla_atendimento_expirado").textContent = "Erro";
        document.getElementById("sla_resolucao_expirado").textContent = "Erro";
        removerIcones();
      }
    })
    .catch(() => {
      document.getElementById("sla_atendimento_expirado").textContent = "Erro";
      document.getElementById("sla_resolucao_expirado").textContent = "Erro";
      removerIcones();
    });
  }

  function atualizarIcone(idIcone, valorAtual, meta) {
  const icone = document.getElementById(idIcone);
  if (!icone) return;

  // Resetar a classe
  icone.className = "";

  // Limpar símbolo de porcentagem se houver
  let valorLimpo = typeof valorAtual === "string" ? valorAtual.replace("%", "").trim() : valorAtual;
  let valAtualNum = parseFloat(valorLimpo);
  const metaNum = parseFloat(meta);

  console.log(`[${idIcone}] Valor atual: ${valAtualNum}, Meta: ${metaNum}`);

  if (isNaN(valAtualNum) || isNaN(metaNum)) {
    icone.classList.add("d-none");
    return;
  }

  const margem = 5;

  if (valAtualNum >= metaNum) {
    icone.className = "bi bi-arrow-up-short text-success ms-2 fs-4";
  } else if (valAtualNum >= (metaNum - margem)) {
    icone.className = "bi bi-arrow-up-short text-warning ms-2 fs-4";
  } else {
    icone.className = "bi bi-arrow-down-short text-danger ms-2 fs-4";
  }
}


  function removerIcones() {
    ["icone_prazo_atendimento", "icone_prazo_resolucao"].forEach(id => {
      const icone = document.getElementById(id);
      if (icone) icone.className = "d-none";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    carregarSlaGlobal(1);
  });

  document.querySelectorAll(".filtro-btn").forEach(button => {
    button.addEventListener("click", () => {
      const dias = parseInt(button.getAttribute("data-dias"), 10);
      carregarSlaGlobal(dias);
    });
  });


//Script que traz a pesquisa de satisfação-->

  document.addEventListener("DOMContentLoaded", function () {
    // Carrega o card com valor padrão (exemplo: 1 dia)
    atualizarCardPesquisaSatisfacao(30);

    // Botões de filtro (se houver)
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        const dias = parseInt(this.getAttribute('data-dias'), 10);
        atualizarCardPesquisaSatisfacao(dias);
      });
    });
  });

  function atualizarCardPesquisaSatisfacao(dias) {
    fetch('/okrs/csatOkrs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias })
    })
    .then(response => response.json())
    .then(data => {
      console.log("Dados recebidos:", data);

      const csatPercentualEl = document.getElementById("csat-percentual");
      const totalAvaliadoEl = document.getElementById("total-avaliado");
      const iconeCsatEl = document.getElementById("icone_csat");

      if (!csatPercentualEl || !totalAvaliadoEl || !iconeCsatEl) {
        console.warn("Elementos do card de CSAT não encontrados.");
        return;
      }

      if (data.status === 'success') {
        csatPercentualEl.textContent = `${data.csat}%`;
        totalAvaliadoEl.textContent = data.total_respondidas;

        const metaCsat = 80; // Defina sua meta aqui (exemplo: 80%)
        atualizarIconeCsat("icone_csat", data.csat, metaCsat, "alto");
      } else {
        csatPercentualEl.textContent = '-';
        totalAvaliadoEl.textContent = '-';
        iconeCsatEl.className = "d-none";
        console.error("Erro ao buscar dados da pesquisa:", data);
      }
    })
    .catch(error => {
      document.getElementById("csat-percentual").textContent = '-';
      document.getElementById("total-avaliado").textContent = '-';
      document.getElementById("icone_csat").className = "d-none";
      console.error("Erro de conexão com a API de pesquisa:", error);
    });
  }

  function atualizarIconeCsat(idIcone, valorAtual, meta, direcaoMelhoria = "alto") {
    const icone = document.getElementById(idIcone);
    if (!icone) return;

    icone.className = ""; 

    let valNum = parseFloat(String(valorAtual).replace("%", "").trim());
    let metaNum = parseFloat(meta);

    if (isNaN(valNum) || isNaN(metaNum)) {
      icone.classList.add("d-none");
      return;
    }

    const margem = 5;

    const isMelhor = direcaoMelhoria === "alto" ? valNum >= metaNum : valNum <= metaNum;
    const isAceitavel = direcaoMelhoria === "alto"
      ? valNum >= metaNum - margem
      : valNum <= metaNum + margem;

    if (isMelhor) {
      icone.className = "bi bi-arrow-up-short text-success ms-2 fs-4";
    } else if (isAceitavel) {
      icone.className = "bi bi-arrow-up-short text-warning ms-2 fs-4";
    } else {
      icone.className = "bi bi-arrow-down-short text-danger ms-2 fs-4";
    }
  }


//Script que persiste as metas no banco-->

document.getElementById('formMetas').addEventListener('submit', async function (e) {
  e.preventDefault();

  const formData = new FormData(this);
  const data = {};

  formData.forEach((value, key) => {
    data[key] = value !== "" ? parseFloat(value) : null;
  });

  try {
    const response = await fetch('okrs/setMetas', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (result.status === 'success') {
      alert('Metas salvas com sucesso!');
      const modal = bootstrap.Modal.getInstance(document.getElementById('modalDefinirMetas'));
      modal.hide();
    } else {
      alert('Erro ao salvar metas: ' + result.message);
    }

  } catch (error) {
    console.error('Erro na requisição:', error);
    alert('Ocorreu um erro ao enviar os dados.');
  }
});


//Script que traz as metas nos cards-->
document.addEventListener('DOMContentLoaded', () => {
  fetch('/okrs/getMetas')
    .then(response => {
      if (!response.ok) {
        throw new Error('Erro ao buscar metas');
      }
      return response.json();
    })
    .then(data => {
      // Preenche os campos da interface com os dados da meta
      document.getElementById('meta-csat').textContent = data.csat + ' %';
      document.getElementById('meta-sla-atendimento').textContent = data.sla_atendimento_prazo + ' %';
      document.getElementById('meta-sla-solucao').textContent = data.sla_resolucao_prazo + ' %';
      document.getElementById('meta-reabertura').textContent = data.reabertos + ' %';
      document.getElementById('meta-tma').textContent = data.tma + ' min';
      document.getElementById('meta-tms').textContent = data.tms + ' min';
      document.getElementById('meta-fcr').textContent = data.fcr + ' %';
    })
    .catch(error => {
      console.error('Erro ao carregar metas:', error);
    });
});

 // Script de Reabertos Metas
document.addEventListener("DOMContentLoaded", function () {

  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/getMetas');
      return res.ok ? await res.json() : {};
    } catch (err) {
      console.error("Erro ao buscar metas:", err);
      return {};
    }
  }

  async function fetchReabertos(dias) {
    try {
      const res = await fetch('/insights/reabertos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })
      });
      return res.ok ? await res.json() : {};
    } catch (err) {
      console.error("Erro ao buscar reabertos:", err);
      return {};
    }
  }

  async function atualizarReabertos(dias) {
    const metas = await fetchMetas();
    const dados = await fetchReabertos(dias);

    const spanValor = document.getElementById("meta-reabertura");
    const icone = spanValor.previousElementSibling; // <i> da seta

    if (!dados || dados.status !== "success") {
      icone.className = "bi bi-arrow-bar-down-circle"; // seta padrão
      return;
    }

    const total = dados.total_chamados || 0;
    const reabertos = dados.total_reabertos || 0;

    let percentual = 0;
    if (total > 0) {
      percentual = (reabertos / total) * 100;
    }

    // 🔹 Atualiza apenas a seta, sem mudar o valor do card
    if (metas.reabertos != null) {
      if (percentual <= metas.reabertos) {
        icone.className = "bi bi-arrow-up-circle text-success"; // dentro da meta
      } else {
        icone.className = "bi bi-arrow-down-circle text-danger"; // acima da meta
      }
    } else {
      icone.className = "bi bi-arrow-bar-down-circle"; // meta não definida
    }
  }

  // Inicializa com 30 dias
  atualizarReabertos(30);

  // Eventos dos botões
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarReabertos(dias);
    });
  });
});


// Export OKRs Anual
document.addEventListener("DOMContentLoaded", function() {
  const btnExportar = document.querySelector('#btnExportarAnual');

  if (!btnExportar) return;

  btnExportar.addEventListener("click", async () => {
    try {
      const res = await fetch("/okrs/exportarOkrs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}) 
      });

      if (!res.ok) throw new Error("Erro ao gerar relatório.");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Relatorio_OKRs_CSAT_${new Date().getFullYear()}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Erro ao exportar OKRs:", err);
      alert("Não foi possível gerar o relatório. Tente novamente.");
    }
  });
});