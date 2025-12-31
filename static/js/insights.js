document.addEventListener("DOMContentLoaded", function () {
    const botaoPeriodo = document.querySelectorAll(".filtro-btn");
    const campoTotalChamados = document.getElementById("chamados-abertos");

    async function carregarChamados(dias = 1) {
        try {
            const response = await fetch('/insights/ChamadosSuporte', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ dias: dias })
            });

            const data = await response.json();

            if (data.status === "success") {
                campoTotalChamados.textContent = data.total_chamados;
            } else {
                campoTotalChamados.textContent = "Erro ao carregar";
                console.error(data.message);
            }
        } catch (error) {
            campoTotalChamados.textContent = "Erro de conexão";
            console.error(error);
        }
    }

    // Evento de clique nos botões de período
    botaoPeriodo.forEach(button => {
        button.addEventListener("click", function () {
            // Atualiza classe ativa nos botões
            botaoPeriodo.forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");

            const dias = parseInt(this.getAttribute("data-dias"), 10);
            carregarChamados(dias);
        });
    });

    // Carregamento inicial (padrão 7 dias)
    carregarChamados(1);
});


document.addEventListener("DOMContentLoaded", function () {
    function carregarChamadosFinalizados(dias = 1) {
        fetch('/insights/ChamadosSuporte/finalizado', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dias: dias })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                document.getElementById("chamados-finalizados").textContent = data.total_chamados;
            } else {
                document.getElementById("chamados-finalizados").textContent = "Erro ao carregar";
            }
        })
        .catch(error => {
            console.error("Erro:", error);
            document.getElementById("chamados-finalizados").textContent = "Erro de conexão";
        });
    }

    // Adiciona o comportamento aos botões de período
    document.querySelectorAll(".filtro-btn").forEach(button => {
        button.addEventListener("click", () => {
            const dias = parseInt(button.getAttribute("data-dias"), 10);
            carregarChamadosFinalizados(dias);
        });
    });

    // Carregamento inicial com 7 dias
    carregarChamadosFinalizados(1);
});

let codigosEmAberto = [];

  document.addEventListener("DOMContentLoaded", function () {
    carregarChamadosEmAberto(1);

    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        const dias = parseInt(this.getAttribute('data-dias'));
        carregarChamadosEmAberto(dias);
      });
    });
  });

  function carregarChamadosEmAberto(dias = 1) {
    fetch('/insights/ChamadosEmAbertoSuporte', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias })
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === "success") {
        document.getElementById("ChamadosEmAbertoSuporte").textContent = data.total_chamados;
        codigosEmAberto = data.cod_chamados || [];
      } else {
        document.getElementById("ChamadosEmAbertoSuporte").textContent = "Erro ao carregar";
        codigosEmAberto = [];
      }
    })
    .catch(error => {
      document.getElementById("ChamadosEmAbertoSuporte").textContent = "Erro de conexão";
      codigosEmAberto = [];
      console.error("Erro ao buscar chamados em aberto:", error);
    });
  }

  function mostrarCodigosChamadosAbertos(titulo, listaCodigos) {
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

let codigosAtendimento = [];
let codigosResolucao = [];

function mostrarCodigosSla(titulo, listaCodigos) {
  const lista = document.getElementById("listaCodigos");
  const tituloModal = document.getElementById("modalCodigosLabel");

  if (!lista || !tituloModal) return;

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

async function carregarSlaGlobal(dias = 1) {
  try {
    const res = await fetch('/insights/sla', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias })
    });

    const data = await res.json();

    if (data.status === "success") {
      document.getElementById("sla_atendimento_expirado").textContent = data.percentual_atendimento + "%";
      document.getElementById("sla_atendimento_prazo").textContent = data.percentual_prazo_atendimento + "%";
      document.getElementById("sla_resolucao_expirado").textContent = data.percentual_resolucao + "%";
      document.getElementById("percentual_prazo_resolucao").textContent = data.percentual_prazo_resolucao + "%";

      codigosAtendimento = data.codigos_atendimento || [];
      codigosResolucao = data.codigos_resolucao || [];

      const metasRes = await fetch('/okrs/getMetas');
      if (metasRes.ok) {
        const metas = await metasRes.json();

        atualizarIconeSla("icone_prazo_atendimento", data.percentual_prazo_atendimento, metas.prazo_atendimento);
        atualizarIconeSla("icone_prazo_resolucao", data.percentual_prazo_resolucao, metas.prazo_resolucao);
      }

    } else {
      document.getElementById("sla_atendimento_expirado").textContent = "Erro";
      document.getElementById("sla_resolucao_expirado").textContent = "Erro";
      mostrarIconesPadrao();
    }
  } catch (err) {
    console.error("Erro na requisição SLA:", err);
    document.getElementById("sla_atendimento_expirado").textContent = "Erro";
    document.getElementById("sla_resolucao_expirado").textContent = "Erro";
    mostrarIconesPadrao();
  }
}

function atualizarIconeSla(idIcone, valorAtual, meta) {
  const icone = document.getElementById(idIcone);
  if (!icone) return;

  icone.className = "";

  let valNum = parseFloat(String(valorAtual || "0").replace(",", ".").replace("%", "").trim());
  let metaNum = parseFloat(String(meta || "0").replace(",", ".").replace("%", "").trim());

  const margem = 5; 

  if (isNaN(valNum) || isNaN(metaNum)) {
    icone.className = "bi-dash-lg text-muted ms-2 fs-4";
    return;
  }

  if (valNum >= metaNum) {
    icone.className = "bi bi-arrow-up-short text-success ms-2 fs-4";
  } else if (valNum >= (metaNum - margem)) {
    icone.className = "bi bi-arrow-up-short text-warning ms-2 fs-4";
  } else {
    icone.className = "bi bi-arrow-down-short text-danger ms-2 fs-4";
  }
}

function mostrarIconesPadrao() {
  ["icone_prazo_atendimento", "icone_prazo_resolucao"].forEach(id => {
    const icone = document.getElementById(id);
    if (icone) icone.className = "bi-dash-lg text-muted ms-2 fs-4";
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



document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'));
      carregarAbertosResolvidos(dias);
    });
  });

  let adminChartInstance = null;

  function carregarAbertosResolvidos(dias = 1) {
    console.log('Carregando abertos x resolvidos com dias =', dias);

    fetch('/insights/abertos_vs_admin_resolvido_periodo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias: dias })  
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === "success") {
        const ctx = document.getElementById('LinhaAbertosResolvidosAdminChart').getContext('2d');

        if (adminChartInstance) {
          adminChartInstance.destroy();
        }

        adminChartInstance = new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.labels,
            datasets: data.datasets
          },
          options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            stacked: false,
            plugins: {
              title: { display: false },
              legend: {
                labels: { color: '#fff' }
              },
              tooltip: {
                titleColor: '#fff',
                bodyColor: '#fff',
                backgroundColor: 'rgba(0,0,0,0.7)'
              }
            },
            scales: {
              x: {
                ticks: { color: '#fff' },
                grid: { display: false }
              },
              y: {
                beginAtZero: true,
                ticks: { color: '#fff', precision: 0 },
                grid: { color: 'rgba(255,255,255,0.1)' }
              }
            }
          }
        });

        document.getElementById("adminTotalAbertos").textContent = data.resumo.abertos;
        document.getElementById("adminTotalResolvidos").textContent = data.resumo.resolvidos;
        document.getElementById("adminDiferenca").textContent = data.resumo.diferenca;
      } else {
        console.error("Erro ao carregar dados:", data.message);
      }
    })
    .catch(error => console.error("Erro de conexão:", error));
  }

  carregarAbertosResolvidos(1);
});

    let statusChart = null;

    const coresStatusFixas = {
        "Aguardando Atendimento": "#FFD700",
        "Aguardando Cliente": "#20B2AA",
        "Andamento": "#FFD700",
        "Transferência": "#BDB76B",
        "Aguardando Terceiros": "#1E90FF",
        "Aguardando Suporte N2": "#F4A460",
        "Aguardando Analise N2": "#FF0000",
        "Agendamento": "#6A5ACD",
        "Aguardando Aprovação": "#BDB76B",
        "Resolvido" : "#32CD32",
        "Cancelado" : "#BEBEBE",
        "Agendamento | Desenvolvimento": "#9370DB",
    };

    function verificarCanvas() {
        const canvas = document.getElementById('statusChart');
        if (!canvas) {
            console.error('Elemento canvas não encontrado! Verifique se existe um elemento com id="statusChart"');
            return false;
        }
        return true;
    }

    function processarDadosParaBarras(apiData) {
        try {
            const grupos = apiData.grupos;
            const status = apiData.labels;

            const datasets = status.map(statusName => ({
                label: statusName,
                data: grupos.map(grupo =>
                    apiData.chamados_abertos.filter(chamado =>
                        chamado.nome_grupo === grupo && chamado.nome_status === statusName
                    ).length
                ),
                backgroundColor: coresStatusFixas[statusName] || '#999999',
                borderColor: '#2d2d2d',
                borderWidth: 1
            }));

            return {
                labels: grupos,
                datasets: datasets
            };
        } catch (error) {
            console.error('Erro ao processar dados:', error);
            return null;
        }
    }

    function criarGrafico(processedData, totalChamados) {
        try {
            if (!verificarCanvas()) return;

            const ctx = document.getElementById('statusChart').getContext('2d');
            if (statusChart) statusChart.destroy();

            const config = {
                type: 'bar',
                data: processedData,
                options: {
                    indexAxis: 'y', 
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            stacked: true,
                            grid: { display: false },
                            ticks: { color: '#fff' }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            ticks: { color: '#fff', precision: 0 },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                color: '#fff',
                                font: { size: 12 },
                                boxWidth: 12
                            }
                        },
                        title: {
                            display: true,
                            text: `Total de Chamados Abertos: ${totalChamados}`,
                            color: '#fff',
                            font: { size: 16 }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            titleColor: '#fff',
                            bodyColor: '#fff'
                        },
                        datalabels: {
                            color: '#fff',
                            anchor: 'center',
                            align: 'center',
                            formatter: value => value > 0 ? value : null,
                            font: {
                                weight: 'bold',
                                size: 20
                            }
                        }
                    }
                },
                plugins: [ChartDataLabels]
            };

            statusChart = new Chart(ctx, config);
            console.log('Gráfico criado com sucesso!');
        } catch (error) {
            console.error('Erro ao criar gráfico:', error);
        }
    }

    async function carregarDados(dias = 1) {
        try {
            if (!verificarCanvas()) return;

            const response = await fetch('/insights/abertos/status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dias: dias })
            });

            if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);

            const data = await response.json();
            if (data.status === "success") {
                const processedData = processarDadosParaBarras({
                    ...data.data,
                    chamados_abertos: data.chamados_abertos
                });

                if (processedData) {
                    criarGrafico(processedData, data.data.total);
                }
            } else {
                console.error('Erro na API:', data.message);
            }

        } catch (error) {
            console.error('Erro ao carregar dados:', error);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        const botoesFiltro = document.querySelectorAll('.filtro-btn');

        botoesFiltro.forEach(botao => {
            botao.addEventListener('click', function () {
                botoesFiltro.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                const dias = parseInt(this.getAttribute('data-dias'));
                carregarDados(dias);
            });
        });

        carregarDados(1);

        window.addEventListener('resize', () => {
            if (statusChart) statusChart.update();
        });
    });

    function carregarTicketsPorCanal(dias = 1) {
        fetch('/insights/ticketsCanal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dias: dias })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                const ctx = document.getElementById('TicketsAdminCanalChart').getContext('2d');

                if (window.ticketsCanalChartInstance) {
                    window.ticketsCanalChartInstance.destroy();
                }

                data.data.datasets.forEach(ds => {
                    ds.barThickness = 15;
                    ds.maxBarThickness = 40;
                    ds.categoryPercentage = 0.8;
                    ds.barPercentage = 0.9;
                });

                window.ticketsCanalChartInstance = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.data.labels,
                        datasets: data.data.datasets
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { labels: { color: '#fff' } },
                            tooltip: {
                                titleColor: '#fff',
                                bodyColor: '#fff',
                                backgroundColor: 'rgba(0,0,0,0.7)'
                            }
                        },
                        scales: {
                            x: {
                                ticks: { color: '#fff' },
                                grid: { color: 'rgba(255,255,255,0.1)' }
                            },
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Quantidade de Chamados',
                                    color: '#fff'
                                },
                                ticks: { color: '#fff', precision: 0 },
                                grid: { color: 'rgba(255,255,255,0.1)' }
                            }
                        }
                    }
                });
            } else {
                console.error("Erro ao carregar dados:", data.message);
            }
        })
        .catch(err => console.error("Erro de conexão:", err));
    }

    document.addEventListener('DOMContentLoaded', () => {
        const botoesFiltro = document.querySelectorAll('.filtro-btn');

        botoesFiltro.forEach(botao => {
            botao.addEventListener('click', () => {
                const dias = parseInt(botao.getAttribute('data-dias'), 10);
                botoesFiltro.forEach(btn => btn.classList.remove('active'));
                botao.classList.add('active');
                carregarTicketsPorCanal(dias);
            });
        });
        carregarTicketsPorCanal(1);
    });

function carregarTicketsPorOperador(dias = 1) {
    fetch('/insights/ChamadosSuporte/ticketsOperador', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias: dias })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            const ctx = document.getElementById('OperadorAtendimentoChart').getContext('2d');
            if (window.operadorChartInstance) {
                window.operadorChartInstance.destroy();
            }
            window.operadorChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.data.labels,
                    datasets: [{
                        label: "Chamados por Operador",
                        data: data.data.datasets[0].data,
                        backgroundColor: data.data.datasets[0].backgroundColor,
                        barThickness: 20
                    }]
                },
                options: {
                    plugins: {
                        title: {
                            display: true,
                            color: '#fff'
                        },
                        legend: {
                            display: false,
                            labels: { color: '#fff' }
                        }
                    },
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0, color: '#fff' }
                        },
                        x: {
                            ticks: {
                                autoSkip: false,
                                maxRotation: 45,
                                minRotation: 0,
                                color: '#fff'
                            }
                        }
                    }
                }
            });
        } else {
            console.error("Erro ao carregar dados:", data.message);
        }
    })
    .catch(err => console.error("Erro de conexão:", err));
}

document.addEventListener('DOMContentLoaded', () => {
    carregarTicketsPorOperador(30);

    document.querySelectorAll('.filtro-btn').forEach(botao => {
        botao.addEventListener('click', () => {
            const dias = parseInt(botao.getAttribute('data-dias'));
            carregarTicketsPorOperador(dias);
        });
    });
});


document.addEventListener("DOMContentLoaded", () => {
    const modalElement = document.getElementById('modalChamadosGrupos');
    const listaChamados = document.getElementById('listaChamadosGrupos');
    const modalInstance = new bootstrap.Modal(modalElement);
    modalElement.addEventListener('shown.bs.modal', () => {
        const botaoFechar = modalElement.querySelector('button.btn-close');
        if (botaoFechar) botaoFechar.focus();
    });
    function criarSlaGrupoChart(ctx, label, naoExpirado, quaseEstourando, expirado, codigosCriticos, codigosExpirados) {
        const total = naoExpirado + quaseEstourando + expirado;
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Dentro do Prazo', 'Prazo Crítico', 'Expirado'],
                datasets: [{
                    label: label,
                    data: [naoExpirado, quaseEstourando, expirado],
                    backgroundColor: ['#007bffcc', '#ffc107cc', '#dc3545cc'],
                    borderRadius: 6,
                    barThickness: 30
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: false,
                    tooltip: {
                        callbacks: {
                            label: ctx => {
                                const value = ctx.raw;
                                const percent = ((value / total) * 100).toFixed(1);
                                return `${value} (${percent}%)`;
                            }
                        }
                    },
                    datalabels: {
                        color: '#fff',
                        anchor: 'center',
                        align: 'top',
                        formatter: val => {
                            if (total === 0) return '0%';
                            return ((val / total) * 100).toFixed(1) + '%';
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#fff' }, grid: { display: false } },
                    y: { beginAtZero: true, ticks: { color: '#fff' }, grid: { display: false } }
                },

                onClick: (evt, elements) => {
                    if (elements.length > 0) {
                        const idx = elements[0].index;
                        let codigos = [];

                        if (idx === 1 && codigosCriticos.length > 0) {
                            codigos = codigosCriticos; 
                        } 
                        else if (idx === 2 && codigosExpirados.length > 0) {
                            codigos = codigosExpirados; 
                        }

                        if (codigos.length > 0) {
                            listaChamados.innerHTML = '';
                            codigos.forEach(codigo => {
                                const li = document.createElement('li');
                                li.style.marginBottom = '8px';

                                const link = document.createElement('a');
                                link.href = `https://comnect.desk.ms/?Ticket#ChamadosSuporte:${codigo}`;
                                link.target = '_blank';
                                link.textContent = codigo;
                                link.style.color = '#ffc107';

                                li.appendChild(link);
                                listaChamados.appendChild(li);
                            });

                            modalInstance.show();
                        }
                    }
                }
            },
            plugins: [ChartDataLabels]
        });
    }

    fetch('/dashboard/ChamadosSuporte/sla_andamento_grupos', { method: 'POST' })
        .then(res => res.json())
        .then(data => {

            if (data.status === "success") {
                criarSlaGrupoChart(
                    document.getElementById('slaGrupoChart').getContext('2d'),
                    'SLA - Atendimento',
                    data.sla1_nao_expirado,
                    data.sla1_quase_estourando || 0,
                    data.sla1_expirado,
                    data.codigos_sla1_critico || [],
                    data.codigos_sla1_expirado || []      
                );

                criarSlaGrupoChart(
                    document.getElementById('slaGrupoChart2').getContext('2d'),
                    'SLA - Resolução',
                    data.sla2_nao_expirado,
                    data.sla2_quase_estourando || 0,
                    data.sla2_expirado,
                    data.codigos_sla2_critico || [],
                    data.codigos_sla2_expirado || []      
                );

            } else {
                console.error('Erro ao carregar dados de SLA por grupo:', data.message);
            }
        })
        .catch(e => console.error('Erro na requisição SLA por grupo:', e));
});


document.addEventListener("DOMContentLoaded", () => {
    const modalElement = document.getElementById('modalChamadosExpirados');
    const listaChamados = document.getElementById('listaChamados');
    const modalInstance = new bootstrap.Modal(modalElement);
    function criarSlaChart(ctx, label, naoExpirado, quaseEstourando, expirado, codigosExpirados, codigosCriticos) {
        const total = naoExpirado + quaseEstourando + expirado;

        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Dentro do Prazo', 'Prazo Crítico', 'Expirado'],
                datasets: [{
                    label: label,
                    data: [naoExpirado, quaseEstourando, expirado],
                    backgroundColor: ['#007bffcc', '#ffc107cc', '#dc3545cc'],
                    borderRadius: 6,
                    barThickness: 30
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: false,
                    tooltip: {
                        callbacks: {
                            label: ctx => {
                                const value = ctx.raw;
                                const percent = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${value} (${percent}%)`;
                            }
                        }
                    },
                    datalabels: {
                        color: '#fff',
                        anchor: 'center',
                        align: 'top',
                        formatter: val => {
                            if (total === 0) return '0%';
                            return ((val / total) * 100).toFixed(1) + '%';
                        }
                    }
                },
                scales: {
                    x: { 
                        ticks: { color: '#fff' },
                        grid: { display: false }
                    },
                    y: { 
                        beginAtZero: true,
                        ticks: { color: '#fff' },
                        grid: { display: false }
                    }
                },

                onClick: (evt, elements) => {
                    if (elements.length > 0) {
                        const idx = elements[0].index;
                        let codigos = [];

                        if (idx === 1 && codigosCriticos.length > 0) { 
                            codigos = codigosCriticos;     
                        } 
                        else if (idx === 2 && codigosExpirados.length > 0) {  
                            codigos = codigosExpirados;    
                        }

                        if (codigos.length > 0) {
                            listaChamados.innerHTML = '';

                            codigos.forEach(codigo => {
                                const li = document.createElement('li');
                                li.style.marginBottom = '8px';

                                const link = document.createElement('a');
                                link.href = `https://comnect.desk.ms/?Ticket#ChamadosSuporte:${codigo}`;
                                link.target = '_blank';
                                link.textContent = codigo;
                                link.style.color = '#ffc107';

                                li.appendChild(link);
                                listaChamados.appendChild(li);
                            });

                            modalInstance.show();
                        }
                    }
                }
            },
            plugins: [ChartDataLabels]
        });
    }

    fetch('/dashboard/ChamadosSuporte/sla_andamento', { method: 'POST' })
        .then(res => res.json())
        .then(data => {

            if (data.status === "success") {

                criarSlaChart(
                    document.getElementById('slaChart').getContext('2d'),
                    'SLA - Atendimento',
                    data.sla1_nao_expirado,
                    data.sla1_quase_estourando || 0,
                    data.sla1_expirado,
                    data.codigos_sla1_expirado || [],   
                    data.codigos_sla1_critico || []     
                );

                criarSlaChart(
                    document.getElementById('slaChart2').getContext('2d'),
                    'SLA - Resolução',
                    data.sla2_nao_expirado,
                    data.sla2_quase_estourando || 0,
                    data.sla2_expirado,
                    data.codigos_sla2_expirado || [],   
                    data.codigos_sla2_critico || []     
                );

            } else {
                console.error('Erro no carregamento dos dados SLA:', data.message);
            }
        })
        .catch(e => console.error('Erro na requisição SLA:', e));
});


  document.addEventListener("DOMContentLoaded", function () {
    atualizarCardPesquisaSatisfacao(1);
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        const dias = parseInt(this.getAttribute('data-dias'), 10);
        atualizarCardPesquisaSatisfacao(dias);
      });
    });
  });

    const csatPercentualEl = document.getElementById("csat-percentual");
    csatPercentualEl.style.cursor = "pointer";
    csatPercentualEl.addEventListener("click", function () {
      if (comentariosPesquisa.length === 0) {
        alert("Nenhum chamado disponível.");
        return;
      }
      const lista = document.getElementById("listaComentarios");
      lista.innerHTML = "";

      comentariosPesquisa.forEach(codigoChamado => {
        const li = document.createElement("li");
        li.style.marginBottom = "8px";

        const link = document.createElement("a");
        link.href = `https://comnect.desk.ms/?Ticket#ChamadosSuporte:${codigoChamado}`;
        link.target = "_blank";
        link.textContent = codigoChamado;
        link.style.color = "#ff6384"; 
        li.appendChild(link);
        lista.appendChild(li);
      });

      const modalElement = document.getElementById("modalComentariosPesquisa");
      const modal = new bootstrap.Modal(modalElement);
      modal.show();
    });
  

  function atualizarCardPesquisaSatisfacao(dias) {
  fetch('/insights/pSatisfacao', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ dias })
  })
  .then(response => response.json())
  .then(data => {
    console.log("Dados recebidos:", data);

    const csatPercentualEl = document.getElementById("csat-percentual");
    const totalAvaliadoEl = document.getElementById("total-avaliado");

    if (!csatPercentualEl || !totalAvaliadoEl) {
      console.warn("Elementos do card de CSAT não encontrados.");
      return;
    }

    if (data.status === 'success') {
    csatPercentualEl.textContent = `${data.csat}%`;
    totalAvaliadoEl.textContent = data.total_respondidas;

    comentariosPesquisa = data.referencia_chamados || [];
    } else {
        csatPercentualEl.textContent = '-';
        totalAvaliadoEl.textContent = '-';
        comentariosPesquisa = [];
        console.error("Erro ao buscar dados da pesquisa:", data);
    }
  })
  .catch(error => {
    document.getElementById("csat-percentual").textContent = '-';
    document.getElementById("total-avaliado").textContent = '-';
    console.error("Erro de conexão com a API de pesquisa:", error);
  });
}


  document.addEventListener("DOMContentLoaded", function () {
  let diasSelecionados = 1;
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

async function carregarTmaTms(dias) {
  try {
    const res = await fetch(`/insights/tma_tms?dias=${dias}`);
    const data = await res.json();

    if (data.status === "success") {
      document.getElementById("percentual-tma").innerText = data.mediana_tma;
      document.getElementById("percentual-tms").innerText = data.mediana_tms;

      const metasRes = await fetch('/okrs/getMetas');
      const metas = await metasRes.json();

      atualizarIconeTmaTms("icone_tma", data.mediana_tma, metas.tma, "baixo"); 
      atualizarIconeTmaTms("icone_tms", data.mediana_tms, metas.tms, "baixo");
    } else {
      console.error("Erro ao carregar TMA/TMS:", data.message);
    }
  } catch (err) {
    console.error("Erro na requisição TMA/TMS:", err);
  }
}

function atualizarIconeTmaTms(idIcone, valorTexto, metaTexto, sentido = "baixo") {
  const icone = document.getElementById(idIcone);
  if (!icone) return;

  icone.className = "";

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

  if (sentido === "baixo") {
    if (valorMin <= metaMin) {
      icone.className = "bi bi-arrow-down-short text-success ms-2 fs-4";
    } else if (valorMin <= metaMin + margem) {
      icone.className = "bi bi-arrow-down-short text-warning ms-2 fs-4";
    } else {
      icone.className = "bi bi-arrow-up-short text-danger ms-2 fs-4";
    }
  } else {
    if (valorMin >= metaMin) {
      icone.className = "bi bi-arrow-up-short text-success ms-2 fs-4";
    } else if (valorMin >= metaMin - margem) {
      icone.className = "bi bi-arrow-up-short text-warning ms-2 fs-4";
    } else {
      icone.className = "bi bi-arrow-down-short text-danger ms-2 fs-4";
    }
  }
}

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

  atualizarFCR(1); 
});

async function atualizarFCR(dias, nomeOperador) {
  try {
    const res = await fetch('/insights/fcr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias })
    });

    const data = await res.json();

    const fcrSpan = document.getElementById("chamado_fcr");
    const percentualSpan = document.getElementById("percentual_fcr");

    if (data.status === "success") {
      const totalFcr = data.total_fcr || 0;
      const percentualRaw = data.percentual_fcr;
      const percentual = typeof percentualRaw === "number" ? percentualRaw.toFixed(1) + "%" : "-";
      const percentualValor = typeof percentualRaw === "number" ? percentualRaw : null;

      fcrSpan.textContent = totalFcr;
      percentualSpan.textContent = percentual;
      chamadosFcrCodigos = data.cod_chamados || [];


    } else {
      fcrSpan.textContent = "Erro";
      percentualSpan.textContent = "-";
      icone.className = "";
      chamadosFcrCodigos = [];
      console.error("Erro na resposta:", data.message);
    }
  } catch (error) {
    console.error("Erro ao buscar FCR:", error);
    document.getElementById("chamado_fcr").textContent = "Erro";
    document.getElementById("percentual_fcr").textContent = "-";
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

document.addEventListener("DOMContentLoaded", function () {
    const botoesFiltro = document.querySelectorAll(".filtro-btn");
    const campoNota = document.getElementById("ces-nota");
    const campoDescricao = document.getElementById("ces-descricao");

    async function carregarCES(dias = 1) {
        try {
            const response = await fetch('/insights/ces', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ dias: dias })
            });

            const data = await response.json();

            if (data.status === "success") {
                campoNota.textContent = data.nota;
                campoDescricao.textContent = data.descricao;

                campoDescricao.classList.remove("text-primary", "text-warning", "text-danger");

                switch (data.descricao) {
                    case 'Baixo esforço':
                        campoDescricao.classList.add('text-primary'); 
                        break;
                    case 'Esforço moderado':
                        campoDescricao.classList.add('text-warning'); 
                        break;
                    case 'Alto esforço':
                        campoDescricao.classList.add('text-danger'); 
                        break;
                    default:
                        break;
                }

            } else {
                campoNota.textContent = "Erro";
                campoDescricao.textContent = "Erro";
                campoDescricao.classList.remove("text-primary", "text-warning", "text-danger");
                console.error(data.message);
            }
        } catch (error) {
            campoNota.textContent = "Erro";
            campoDescricao.textContent = "Erro";
            campoDescricao.classList.remove("text-primary", "text-warning", "text-danger");
            console.error(error);
        }
    }

    botoesFiltro.forEach(button => {
        button.addEventListener("click", function () {
            botoesFiltro.forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");

            const dias = parseInt(this.getAttribute("data-dias"), 10);
            carregarCES(dias);
        });
    });

    carregarCES(1);
});


  document.addEventListener("DOMContentLoaded", function () {
  atualizarNps(1);

  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarNps(dias);
    });
  });
});

function atualizarNps(dias) {
  fetch('/insights/nps', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias })
  })
  .then(res => res.json())
  .then(data => {
    const npsNullEl = document.getElementById("nps-null");
    const npsRetornoEl = document.getElementById("nps-retorno");

    if (!npsNullEl || !npsRetornoEl) {
      console.warn("Elementos NPS não encontrados no DOM.");
      return;
    }

    if (data.status && data.status !== "Sem dados suficientes") {
      npsNullEl.textContent = data.status;
      npsRetornoEl.textContent = data.nps + "%";

      npsNullEl.className = 'value';       
      npsRetornoEl.className = 'value';

      switch (data.status) {
        case 'Excelente':
          npsNullEl.classList.add('text-success');
          
          break;
        case 'Muito bom':
          npsNullEl.classList.add('text-primary');
          
          break;
        case 'Razoável':
          npsNullEl.classList.add('text-warning');
          
          break;
        case 'Ruim':
          npsNullEl.classList.add('text-danger');
          
          break;
        default:
          break;
      }

    } else {
      npsNullEl.textContent = "-";
      npsRetornoEl.textContent = "0%";
      npsNullEl.className = 'value';
      npsRetornoEl.className = 'value';
    }
  })
  .catch(err => {
    console.error("Erro ao buscar dados do NPS:", err);
    const npsNullEl = document.getElementById("nps-null");
    const npsRetornoEl = document.getElementById("nps-retorno");
    npsNullEl.textContent = "-";
    npsRetornoEl.textContent = "0%";
    npsNullEl.className = 'value';
    npsRetornoEl.className = 'value';
  });
}


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

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      const nomeOperador = "{{ nome }}"; 
      atualizarReabertos(dias, nomeOperador);
    });
  });

  atualizarReabertos(1, "{{ nome }}");
});

async function atualizarReabertos(dias, nomeOperador) {
  const metas = await fetchMetas();

  fetch('/insights/reabertos', {
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
      icone.className = "";
      icone.title = "";
      chamadosReabertosCodigos = [];
      console.error("Erro na resposta:", data.message);
    }
  })
  .catch(error => {
    console.error("Erro ao buscar reabertos:", error);
    reabertosSpan.textContent = "Erro";
    percentualSpan.textContent = "-";
    icone.className = "";
    icone.title = "";
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

document.addEventListener("DOMContentLoaded", function () {
  atualizarLigacoes(1);
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      atualizarLigacoes(dias);
    });
  });
});

function atualizarLigacoes(dias) {
  fetch('/insights/ligacoesAtendidas', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias })
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === "success") {
      document.getElementById("ch_atendidas").textContent = data.total_ligacoes;
    } else {
      console.error("Erro ao buscar ligações atendidas:", data.message);
    }
  })
  .catch(error => {
    console.error("Erro na requisição de ligações atendidas:", error);
  });
}



document.addEventListener("DOMContentLoaded", function () {
  atualizarLigacoesPerdidas(1);
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = this.getAttribute('data-dias'); 
      atualizarLigacoesPerdidas(dias);
    });
  });
});

function atualizarLigacoesPerdidas(filtro) {
  fetch('/insights/ligacoesPerdidas', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias: filtro })
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === "success") {
      document.getElementById("ch_naoatendidas").textContent = data.total_ligacoes;
    } else {
      console.error("Erro ao buscar ligações não atendidas:", data.message);
    }
  })
  .catch(error => {
    console.error("Erro na requisição de ligações não atendidas:", error);
  });
}


document.addEventListener("DOMContentLoaded", function () {
  const botoesPeriodo = document.querySelectorAll(".filtro-btn");

  carregarChamadasEfetuadas(1);

  botoesPeriodo.forEach(button => {
    button.addEventListener("click", function () {
      botoesPeriodo.forEach(btn => btn.classList.remove("active"));
      this.classList.add("active");

      const dias = this.getAttribute("data-dias"); 
      carregarChamadasEfetuadas(dias);
    });
  });
});

async function carregarChamadasEfetuadas(filtro) {
  try {
    const response = await fetch('/insights/chamadasEfetuadas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias: filtro })
    });

    const data = await response.json();

    if (data.status === "success") {
      const total = data.total_ligacoes || 0;
      document.getElementById("ch-efetuadas").textContent = total;
    } else {
      console.error("Erro na resposta:", data.message);
    }
  } catch (error) {
    console.error("Erro ao buscar chamadas efetuadas:", error);
  }
}

  document.addEventListener("DOMContentLoaded", function () {
    atualizarChamadasTransferidas(1);

    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');

        const dias = parseInt(this.getAttribute('data-dias'), 10);
        atualizarChamadasTransferidas(dias);
      });
    });
  });

  function atualizarChamadasTransferidas(dias, nomeOperador) {
    fetch('/insights/chamadasTransferidas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias })
    })
    .then(response => response.json())
    .then(data => {
      const spanTransferidas = document.getElementById("ch_transferidas");

      if (data.status === "success") {
        spanTransferidas.textContent = data.total_ligacoes || 0;
      } else {
        spanTransferidas.textContent = "Erro";
        console.error("Erro na resposta:", data.message);
      }
    })
    .catch(error => {
      console.error("Erro ao buscar chamadas transferidas:", error);
      document.getElementById("ch_transferidas").textContent = "Erro";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    atualizarTminTmax(1);

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
    fetch('/insights/tmin_tmax', {
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


 

