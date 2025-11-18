// Script de SLA acumulado
document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);

  const metas = await fetchMetas();
  let chartSlaAcumulado;

  // 🔹 Plugin de linhas pontilhadas das metas
  const horizontalLinePlugin = {
    id: 'horizontalLine',
    afterDraw: (chart) => {
      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;
      ctx.save();

      // Linha meta SLA Atendimento
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

      // Linha meta SLA Resolução
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

  // 🔹 Busca metas do banco
  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/getMetas');
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  // 🔹 Busca dados acumulados
  async function fetchSlaAcumulado(dias = 365) {
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

  async function atualizarGraficoSlaAcumulado(dias = 365) {
    const dados = await fetchSlaAcumulado(dias);

    if (dados.status !== "success") {
      console.error("Erro ao carregar dados:", dados.message);
      return;
    }

    const ctx = document.getElementById("graficoAcumuladoSLA").getContext("2d");

    if (chartSlaAcumulado) chartSlaAcumulado.destroy();

    // 🔹 Gráfico com linha de evolução acumulada
    chartSlaAcumulado = new Chart(ctx, {
      type: "bar",
      data: {
        labels: dados.labels,
        datasets: [
          {
            label: "SLA Atendimento Acumulado (%)",
            data: dados.sla_atendimento_acumulado,
            borderColor: '#dedb41',
            backgroundColor: 'rgba(231, 251, 6, 0.3)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 5,
            pointHoverRadius: 8
          },
          {
            label: "SLA Resolução Acumulado (%)",
            data: dados.sla_resolucao_acumulado,
            borderColor: '#f44336',
            backgroundColor: 'rgba(244, 67, 54, 0.3)',
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 5,
            pointHoverRadius: 8
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" },
          tooltip: { mode: "index", intersect: false },
          annotation: {
            annotations: {
              // As linhas horizontais são desenhadas pelo plugin customizado
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            title: { display: true, text: "SLA (%)" },
            ticks: { stepSize: 10 }
          },
          x: {
            title: { display: true, text: "Mês" }
          }
        }
      },
      plugins: [horizontalLinePlugin]
    });
  }

  // Carrega gráfico ao abrir a página
  atualizarGraficoSlaAcumulado();

  // Exemplo de botões de filtro
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarGraficoSlaAcumulado(dias);
    });
  });
});

// Script de CSAT acumulado

document.addEventListener("DOMContentLoaded", async function () {
  let chartCsatAcumulado;
  const metas = await fetchMetas();

  // 🔹 Plugin de linha pontilhada da meta CSAT
  const horizontalLinePlugin = {
    id: 'horizontalLine',
    afterDraw: (chart) => {
      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;
      ctx.save();

      if (metas.csat != null) {
        const y = yScale.getPixelForValue(metas.csat);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(103,58,183,0.6)';
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

  async function fetchCsatAcumulado(dias = 365) {
    try {
      const res = await fetch('/okrs/csatAcumulado', {
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

  async function atualizarGraficoCsatAcumulado(dias = 365) {
    const dados = await fetchCsatAcumulado(dias);

    if (dados.status !== "success") {
      console.error("Erro ao carregar CSAT:", dados.message);
      return;
    }

    const ctx = document.getElementById("graficoAcumuladoCSAT").getContext("2d");
    if (chartCsatAcumulado) chartCsatAcumulado.destroy();

    chartCsatAcumulado = new Chart(ctx, {
      type: "bar",
      data: {
        labels: dados.labels,
        datasets: [
          {
            label: "CSAT Acumulado (%)",
            data: dados.csat_acumulado,
            borderColor: "#673ab7",
            backgroundColor: "rgba(103,58,183,0.25)",
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 5,
            pointHoverRadius: 8
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" },
          tooltip: { mode: "index", intersect: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            title: { display: true, text: "CSAT (%)" },
            ticks: { stepSize: 10 }
          },
          x: {
            title: { display: true, text: "Mês" }
          }
        }
      },
      plugins: [horizontalLinePlugin]
    });
  }

  atualizarGraficoCsatAcumulado();

  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarGraficoCsatAcumulado(dias);
    });
  });
});


// Script de TMA e TMS acumulado

document.addEventListener("DOMContentLoaded", async function () {
  let chartTmaTms;
  const metas = await fetchMetas();

  // 🔹 Plugin de linha pontilhada das metas
  const horizontalLinePlugin = {
    id: "horizontalLine",
    afterDraw: (chart) => {
      const { ctx, chartArea, scales } = chart;
      ctx.save();

      if (metas.tma != null) {
        const posY = scales.y.getPixelForValue(metas.tma);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, posY);
        ctx.lineTo(chartArea.right, posY);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = "rgba(0, 80, 254, 0.7)"; // azul pontilhado
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      if (metas.tms != null) {
        const posY = scales.y.getPixelForValue(metas.tms);
        ctx.beginPath();
        ctx.moveTo(chartArea.left, posY);
        ctx.lineTo(chartArea.right, posY);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = "rgba(25, 135, 84, 0.7)"; // verde pontilhado
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      ctx.restore();
    },
  };

  async function fetchMetas() {
    try {
      const res = await fetch("/okrs/getMetas");
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  async function fetchTmaTmsAcumulado(dias = 365) {
    try {
      const res = await fetch("/okrs/tmaTmsAcumulado", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dias }),
      });
      const data = await res.json();
      return res.ok ? data : {};
    } catch {
      return {};
    }
  }

  async function atualizarGraficoTmaTms(dias = 365) {
    const dados = await fetchTmaTmsAcumulado(dias);
    if (dados.status !== "success") {
      console.error("Erro ao carregar TMA/TMS:", dados.message);
      return;
    }

    const ctx = document.getElementById("graficoAcumuladoTmaTms").getContext("2d");
    if (chartTmaTms) chartTmaTms.destroy();

    chartTmaTms = new Chart(ctx, {
      type: "bar",
      data: {
        labels: dados.labels,
        datasets: [
          {
            label: "TMA Acumulado",
            data: dados.tma_acumulado_min,
            borderColor: "#0d6efd",
            backgroundColor: "rgba(13,110,253,0.15)",
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 5,
            pointHoverRadius: 8,
          },
          {
            label: "TMS Acumulado",
            data: dados.tms_acumulado_min,
            borderColor: "#198754",
            backgroundColor: "rgba(25,135,84,0.15)",
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: 5,
            pointHoverRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" },
          tooltip: {
            mode: "index",
            intersect: false,
            callbacks: {
              label: function (context) {
                // Converte minutos para horas:minutos
                const minutos = context.parsed.y;
                const horas = Math.floor(minutos / 60);
                const mins = Math.round(minutos % 60);
                return `${context.dataset.label}: ${horas}h${mins.toString().padStart(2, "0")}min`;
              },
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: "Tempo" },
            ticks: {
              callback: function (value) {
                const horas = Math.floor(value / 60);
                const mins = Math.round(value % 60);
                return `${horas}h${mins.toString().padStart(2, "0")}min`;
              },
            },
          },
          x: {
            title: { display: true, text: "Mês" },
          },
        },
      },
      plugins: [horizontalLinePlugin],
    });
  }

  atualizarGraficoTmaTms();

  // Filtros de período
  document.querySelectorAll(".filtro-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      const dias = parseInt(this.getAttribute("data-dias"), 10);
      atualizarGraficoTmaTms(dias);
    });
  });
});


// Script que traz o FCR acumulado

document.addEventListener("DOMContentLoaded", async function () {
  Chart.register(window['chartjs-plugin-annotation']);

  // 🔸 Busca metas atuais (incluindo FCR)
  async function fetchMetas() {
    try {
      const res = await fetch('/okrs/metasAtuais', { method: 'GET' });
      return res.ok ? await res.json() : {};
    } catch {
      return {};
    }
  }

  // 🔸 Busca dados acumulados FCR
  async function fetchFcrAcumulado(dias = 365) {
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

  const metas = await fetchMetas();
  const metaFcr = metas.fcr || 85; // fallback 85% se não vier do backend
  let chartFcrAcumulado;

  // 🔸 Plugin da linha de meta (idêntico ao dos quarters)
  const linhaMetaFcrPlugin = {
    id: 'linhaMetaFCR',
    afterDraw: (chart) => {
      const { ctx, chartArea, scales } = chart;
      const yScale = scales.y;
      const yMeta = metaFcr;

      if (yMeta != null && chartArea) {
        const y = yScale.getPixelForValue(yMeta);
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(chartArea.left, y);
        ctx.lineTo(chartArea.right, y);
        ctx.setLineDash([6, 6]);
        ctx.strokeStyle = 'rgba(255, 152, 0, 0.6)';
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();
      }
    }
  };

  async function atualizarGraficoFcrAcumulado(dias = 365) {
    const dados = await fetchFcrAcumulado(dias);
    if (dados.status !== "success") return;

    const ctx = document.getElementById("graficoAcumuladoFCR").getContext("2d");
    if (chartFcrAcumulado) chartFcrAcumulado.destroy();

    chartFcrAcumulado = new Chart(ctx, {
      type: "bar",
      data: {
        labels: dados.labels,
        datasets: [
          {
            label: "FCR Acumulado (%)",
            data: dados.fcr_acumulado,
            borderColor: "#ff9800",
            backgroundColor: "rgba(255, 152, 0, 0.3)",
            borderWidth: 3,
            tension: 0.3,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "top", labels: { color: "#fff" } },
          tooltip: { mode: "index", intersect: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { color: "#fff", callback: v => v + "%" },
            title: { display: true, text: "FCR (%)", color: "#fff" }
          },
          x: {
            ticks: { color: "#fff" },
            title: { display: true, text: "Mês", color: "#fff" }
          }
        }
      },
      plugins: [linhaMetaFcrPlugin]
    });
  }

  atualizarGraficoFcrAcumulado();

  // Botões de filtro (opcional)
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarGraficoFcrAcumulado(dias);
    });
  });
});


// Exibir CSAT acumulado card de metas acumuladas
function carregarCsatMesAnterior() {
    fetch('/okrs/csatAcumulado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias: 365 })  // janela de 120 dias para garantir mês anterior
    })
    .then(response => response.json())
    .then(data => {

        const elemento = document.getElementById("meta-acumulada-csat");

        // Debug opcional para ver o retorno
        console.log("CSAT Acumulado - retorno do backend:", data);

        // Verifica se retornou sucesso
        if (!data || data.status !== "success") {
            elemento.textContent = "--";
            return;
        }

        const labels = data.labels;           
        const csatMensal = data.csat_mensal; 

        // Se não houver meses processados
        if (!labels || labels.length === 0 || !csatMensal || csatMensal.length === 0) {
            elemento.textContent = "--";
            return;
        }

        // Pega o último mês retornado pelo backend (considerado o mês anterior)
        const indice = labels.length - 1;
        const valor = csatMensal[indice];

        // Exibe no card
        if (typeof valor === "number") {
            elemento.textContent = valor.toFixed(0) + "%";
        } else {
            elemento.textContent = "--";
        }
    })
    .catch(err => {
        console.error("Erro ao carregar CSAT:", err);
        document.getElementById("meta-acumulada-csat").textContent = "--";
    });
}

// Chama a função ao carregar a página
window.addEventListener("DOMContentLoaded", carregarCsatMesAnterior);


// Exibir SLA acumulado card metas acumuladas
function carregarSlaAcumulado(dias = 365) {  
    fetch('/okrs/slaOkrsAcumulado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias })  
    })
    .then(res => res.json())
    .then(data => {
        if (data.status !== "success") {
            document.getElementById("meta-acumulada-sla-atendimento").textContent = "--";
            document.getElementById("meta-acumulada-sla-solucao").textContent = "--";
            return;
        }

        const slaAtendimento = data.sla_atendimento_acumulado;
        const slaSolucao = data.sla_resolucao_acumulado;

        const atendimentoAcumulado = slaAtendimento[slaAtendimento.length - 1];
        const solucaoAcumulado = slaSolucao[slaSolucao.length - 1];

        document.getElementById("meta-acumulada-sla-atendimento").textContent =
            typeof atendimentoAcumulado === "number"
                ? atendimentoAcumulado + "%"
                : "--";

        document.getElementById("meta-acumulada-sla-solucao").textContent =
            typeof solucaoAcumulado === "number"
                ? solucaoAcumulado + "%"
                : "--";
    })
    .catch(err => {
        console.error("Erro ao carregar SLA:", err);
        document.getElementById("meta-acumulada-sla-atendimento").textContent = "--";
        document.getElementById("meta-acumulada-sla-solucao").textContent = "--";
    });
}

// Atualiza ao clicar nos botões de filtro
document.querySelectorAll(".filtro-btn").forEach(button => {
    button.addEventListener("click", () => {
      const dias = parseInt(button.getAttribute("data-dias"), 10);
      carregarSlaAcumulado(dias);  
    });
});




// Exibir FCR card metas acumuladas
function carregarFcrAcumulado() {
    fetch('/okrs/fcrAcumulado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias: 365 }) // período completo
    })
    .then(res => res.json())
    .then(data => {
        if (data.status !== "success") {
            document.getElementById("meta-acumulada-fcr").textContent = "--";
            return;
        }

        const fcrAcumulado = data.fcr_acumulado;

        // Pega o último valor acumulado = acumulado completo
        const ultimoFcr = fcrAcumulado[fcrAcumulado.length - 1];

        document.getElementById("meta-acumulada-fcr").textContent =
            typeof ultimoFcr === "number"
                ? ultimoFcr + "%"  // sem arredondar
                : "--";
    })
    .catch(err => {
        console.error("Erro ao carregar FCR:", err);
        document.getElementById("meta-acumulada-fcr").textContent = "--";
    });
}

// Chama a função ao carregar a página
carregarFcrAcumulado();


// Exibir TMA TMS card metas acumuladas
function carregarTmaTmsAcumulado() {
    fetch('/okrs/tmaTmsAcumulado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias: 365 }) // período completo
    })
    .then(res => res.json())
    .then(data => {
        if (data.status !== "success") {
            document.getElementById("meta-acumulada-tma").textContent = "--";
            document.getElementById("meta-acumulada-tms").textContent = "--";
            return;
        }

        const tma = data.tma_acumulado_min;
        const tms = data.tms_acumulado_min;

        // Últimos valores acumulados
        const tmaAcumulado = tma[tma.length - 1];
        const tmsAcumulado = tms[tms.length - 1];

        function formatarTempo(minutos) {
          const h = Math.floor(minutos / 60);
          const m = Math.round(minutos % 60);
          return `${h}h ${m}m`;
      }


        document.getElementById("meta-acumulada-tma").textContent =
            typeof tmaAcumulado === "number"
                ? formatarTempo(tmaAcumulado)
                : "--";

        document.getElementById("meta-acumulada-tms").textContent =
            typeof tmsAcumulado === "number"
                ? formatarTempo(tmsAcumulado)
                : "--";
    })
    .catch(err => {
        console.error("Erro ao carregar TMA/TMS:", err);
        document.getElementById("meta-acumulada-tma").textContent = "--";
        document.getElementById("meta-acumulada-tms").textContent = "--";
    });
}

// Chama ao carregar a página
carregarTmaTmsAcumulado();


// Exibir os reabertos card metas acumuladas

function carregarReaberturaAcumulada() {
    fetch('/okrs/reabertosOkrs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
    })
    .then(res => res.json())
    .then(data => {

        const el = document.getElementById("meta-acumulada-reabertura");
        if (!el || data.status !== "success") {
            el.textContent = "--";
            return;
        }

        el.textContent = `${data.pct_reabertura}%`;
    })
    .catch(err => {
        console.error("Erro ao carregar acumulado reabertura:", err);
        document.getElementById("meta-acumulada-reabertura").textContent = "--";
    });
}

// carregar ao iniciar
carregarReaberturaAcumulada();
