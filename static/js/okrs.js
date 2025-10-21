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
document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);

  const metas = await fetchMetas();
  let chartTmaTms; // gráfico global

  // Plugin da linha pontilhada (metas TMA e TMS)
  const horizontalLinePluginTmaTms = {
    id: 'horizontalLineTmaTms',
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

    // Lógica: menor valor = melhor desempenho
    if (metas.tma != null) {
      if (tmaMedio <= metas.tma) {
        setaTma.className = "bi bi-arrow-up-circle text-success";
      } else {
        setaTma.className = "bi bi-arrow-down-circle text-danger";
      }
    }

    if (metas.tms != null) {
      if (tmsMedio <= metas.tms) {
        setaTms.className = "bi bi-arrow-up-circle text-success";
      } else {
        setaTms.className = "bi bi-arrow-down-circle text-danger";
      }
    }
  }


  // Atualiza gráfico e indicadores
  async function atualizarGraficoTmaTms(dias) {
    const tmaTmsDados = await fetchTmaTmsMensal(dias);

    if (!tmaTmsDados.status || tmaTmsDados.status !== "success") {
      console.error("Erro ao carregar dados TMA/TMS");
      return;
    }

    const labels = tmaTmsDados.labels || [];
    const tma = tmaTmsDados.media_tma_min || [];
    const tmsMin = tmaTmsDados.media_tms_min || [];
    const tms = tmsMin.map(v => v !== null ? +(v / 60).toFixed(2) : null);

    // Cria gráfico se ainda não existir
    if (!chartTmaTms) {
      const ctx = document.getElementById('graficoTmaTms').getContext('2d');
      chartTmaTms = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'TMA (min)',
              data: tma,
              borderColor: '#4caf50',
              backgroundColor: 'rgba(76, 175, 80, 0.4)',
              tension: 0.3
            },
            {
              label: 'TMS (h)',
              data: tms,
              borderColor: '#2196f3',
              backgroundColor: 'rgba(33, 150, 243, 0.4)',
              tension: 0.3
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

                  if (label.includes('TMA')) {
                    if (value < 60) {
                      return `${label}: ${Math.round(value)} min`;
                    } else {
                      return `${label}: ${(value / 60).toFixed(2)} h`;
                    }
                  } else if (label.includes('TMS')) {
                    return `${label}: ${value} h`;
                  }
                  return `${label}: ${value}`;
                }
              }
            }
          },
          scales: {
            y: { beginAtZero: true, ticks: { color: '#fff' } },
            x: { ticks: { color: '#fff' } }
          }
        },
        plugins: [horizontalLinePluginTmaTms]
      });
    } else {
      chartTmaTms.data.labels = labels;
      chartTmaTms.data.datasets[0].data = tma;
      chartTmaTms.data.datasets[1].data = tms;
      chartTmaTms.update();
    }

    // Calcula médias e atualiza setas
    const tmaMedio = tma.length ? tma.reduce((a, b) => a + b, 0) / tma.length : 0;
    const tmsMedio = tms.length ? tms.reduce((a, b) => a + b, 0) / tms.length : 0;

    atualizarIndicadoresMetas(tmaMedio, tmsMedio, metas);
  }

  // Inicializa com 30 dias
  atualizarGraficoTmaTms(30);

  // Eventos dos botões de filtro
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

  // Plugin da linha pontilhada
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
        ctx.strokeStyle = 'rgba(76, 175, 80, 0.4)';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      if (metas.sla_resolucao_prazo != null) {
        const y = yScale.getPixelForValue(metas.sla_resolucao_prazo);
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

  // 🔹 Atualiza ícones dos cards de SLA
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
    const slaDados = await fetchSlaMensal(dias);

    const labels = slaDados.labels || [];
    const slaAtendimentoData = slaDados.sla_atendimento || [];
    const slaResolucaoData = slaDados.sla_resolucao || [];

    if (!chartSLA) {
      // cria gráfico na primeira vez
      const ctx = document.getElementById('graficoSLA').getContext('2d');
      chartSLA = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'SLA Atendimento (%)',
              data: slaAtendimentoData,
              borderColor: '#4caf50',
              backgroundColor: 'rgba(76, 175, 80, 0.4)',
              tension: 0.3
            },
            {
              label: 'SLA Solução (%)',
              data: slaResolucaoData,
              borderColor: '#2196f3',
              backgroundColor: 'rgba(33, 150, 243, 0.4)',
              tension: 0.3
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'top',
              labels: { color: '#fff' }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: { color: '#fff' }
            },
            x: {
              ticks: { color: '#fff' }
            }
          }
        },
        plugins: [horizontalLinePlugin]
      });
    } else {
      // só atualiza dados se já existir
      chartSLA.data.labels = labels;
      chartSLA.data.datasets[0].data = slaAtendimentoData;
      chartSLA.data.datasets[1].data = slaResolucaoData;
      chartSLA.update();
    }

    // 🔹 Calcula médias e atualiza setas
    const mediaAtendimento = slaAtendimentoData.length
      ? slaAtendimentoData.reduce((a, b) => a + b, 0) / slaAtendimentoData.length
      : 0;
    const mediaResolucao = slaResolucaoData.length
      ? slaResolucaoData.reduce((a, b) => a + b, 0) / slaResolucaoData.length
      : 0;

    atualizarIndicadoresSLA(mediaAtendimento, mediaResolucao);
  }

  // Inicializa com 30 dias
  atualizarGraficoSLA(30);

  // Eventos dos botões
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarGraficoSLA(dias);
    });
  });
});



//Script do gráfico de FCR-->

 document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);

  const metas = await fetchMetas();
  let chartFCR;

  // Exibe no card apenas o valor da meta cadastrada no banco
  if (metas.fcr != null) {
    const metaEl = document.getElementById('meta-fcr');
    metaEl.textContent = `${metas.fcr}%`;
  }

  // Plugin: linha pontilhada no gráfico representando a meta FCR
  const linhaMetaFcrPlugin = {
    id: 'linhaMetaFCR',
    afterDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;
      const yMeta = metas.fcr;

      if (yMeta != null) {
        const y = yScale.getPixelForValue(yMeta);
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(255, 152, 0, 0.4)';
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

  async function atualizarGraficoFCR(dias) {
    const fcrDados = await fetchFcrMensal(dias);
    const labels = fcrDados.labels || [];
    const fcrData = fcrDados.fcr || [];

    // Atualiza apenas a seta do card conforme a meta
    if (fcrData.length > 0 && metas.fcr != null) {
      const valorAtual = fcrData[fcrData.length - 1];
      const metaValor = metas.fcr;

      const metaEl = document.getElementById('meta-fcr');
      const icone = metaEl.previousElementSibling; // o <i> da seta

      if (valorAtual >= metaValor) {
        // Quando está acima ou igual à meta → seta para baixo (ruim)
        icone.className = 'bi bi-arrow-up-circle text-success'

        
      } else {
        // Quando está abaixo da meta → seta para cima (bom)
        icone.className = 'bi bi-arrow-down-circle text-danger';;
      }

    }

    if (!chartFCR) {
      const ctx = document.getElementById('graficoFCR').getContext('2d');
      chartFCR = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'FCR (%)',
              data: fcrData,
              borderColor: '#ff9800',
              backgroundColor: 'rgba(255, 152, 0, 0.4)',
              tension: 0.3
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: 'top',
              labels: { color: '#fff' }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: { color: '#fff' }
            },
            x: {
              ticks: { color: '#fff' }
            }
          }
        },
        plugins: [linhaMetaFcrPlugin]
      });
    } else {
      chartFCR.data.labels = labels;
      chartFCR.data.datasets[0].data = fcrData;
      chartFCR.update();
    }
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

  const metas = await fetchMetas();
  let chartCSAT;

  // 🔹 Linha da meta dinâmica vinda do banco
  const linhaMetaCsatPlugin = {
    id: 'linhaMetaCSAT',
    afterDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;
      const yMeta = metas.csat; // ← valor dinâmico do banco

      if (yMeta != null) {
        const y = yScale.getPixelForValue(yMeta);
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(103, 58, 183, 0.4)';
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

  // 🔹 Atualiza apenas o ícone conforme a meta dinâmica
  function atualizarIndicadorCsat(mediaCsat) {
    const metaCsatEl = document.getElementById("meta-csat");
    if (!metaCsatEl || metas.csat == null) return;

    const setaCsat = metaCsatEl.previousElementSibling;
    const metaValor = metas.csat;

    // Regra: se atingir ou ultrapassar a meta → verde, caso contrário → vermelho
    if (mediaCsat >= metaValor) {
      setaCsat.className = "bi bi-arrow-up-circle text-success";
    } else {
      setaCsat.className = "bi bi-arrow-down-circle text-danger";
    }

    // Exibe a meta no card, sem alterar o conteúdo fixo
    metaCsatEl.textContent = `${metaValor.toFixed(1)}%`;
  }

  async function atualizarGraficoCSAT(dias) {
    const csatDados = await fetchCsatMensal(dias);
    const labels = csatDados.labels || [];
    const csatData = csatDados.csat || [];

    if (!chartCSAT) {
      const ctx = document.getElementById('graficoCSAT').getContext('2d');
      chartCSAT = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'CSAT (%)',
              data: csatData,
              borderColor: '#673ab7',
              backgroundColor: 'rgba(103, 58, 183, 0.4)',
              tension: 0.3
            }
          ]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'top', labels: { color: '#fff' } }
          },
          scales: {
            y: { beginAtZero: true, max: 100, ticks: { color: '#fff' } },
            x: { ticks: { color: '#fff' } }
          }
        },
        plugins: [linhaMetaCsatPlugin]
      });
    } else {
      chartCSAT.data.labels = labels;
      chartCSAT.data.datasets[0].data = csatData;
      chartCSAT.update();
    }

    // 🔹 Calcula média e atualiza seta e valor
    const mediaCsat = csatData.length
      ? csatData.reduce((a, b) => a + b, 0) / csatData.length
      : 0;
    atualizarIndicadorCsat(mediaCsat);
  }

  // Inicializa com 30 dias
  atualizarGraficoCSAT(30);

  // Eventos dos botões
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

    icone.className = ""; // limpa classes

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
      document.getElementById('meta-tms').textContent = data.tms + ' h';
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
      icone.className = "bi bi-arrow-bar-down"; // seta padrão
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
      icone.className = "bi bi-arrow-bar-down"; // meta não definida
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
