// Bloco que traz os dados da sessão para o template atual -->

document.addEventListener("DOMContentLoaded", function () {
    // Recupera grupo da query string (URL)
    const params = new URLSearchParams(window.location.search);
    const grupo = params.get("grupo");

    if (grupo) {
        sessionStorage.setItem("grupoSelecionado", grupo);
        console.log("✅ Grupo restaurado na sessão:", grupo);
    } else {
        console.warn("⚠️ Grupo não encontrado na URL.");
    }
});


// Bloco que traz os chamados criados para os grupos -->

document.addEventListener("DOMContentLoaded", function () {
    const botoesPeriodo = document.querySelectorAll(".filtro-btn");
    const campoTotalChamados = document.getElementById("chamados-abertos");

    async function carregarChamados(dias = 1) {
        const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
        console.log("🔎 Grupo selecionado no sessionStorage:", grupoSelecionado);

        if (!grupoSelecionado) {
            campoTotalChamados.textContent = "Grupo não definido";
            console.warn("Nenhum grupo selecionado no sessionStorage");
            return;
        }

        try {
            const response = await fetch('/grupos/chamados/grupos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dias: dias,
                    grupo: grupoSelecionado
                })
            });

            const data = await response.json();
            console.log("📦 Dados recebidos:", data);

            if (data.status === "success") {
                campoTotalChamados.textContent = data.total_chamados;
            } else {
                campoTotalChamados.textContent = "Erro ao carregar";
                console.error(data.message);
            }
        } catch (error) {
            campoTotalChamados.textContent = "Erro de conexão";
            console.error("Erro na requisição:", error);
        }
    }

    botoesPeriodo.forEach(button => {
        button.addEventListener("click", function () {
            botoesPeriodo.forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");

            const dias = parseInt(this.getAttribute("data-dias"), 10);
            carregarChamados(dias);
        });
    });

    carregarChamados(); // chamada inicial
});


// Bloco que traz os chamados finalizados para os grupos -->

document.addEventListener("DOMContentLoaded", function () {
    const botoesPeriodo = document.querySelectorAll(".filtro-btn");
    const campoChamadosFinalizados = document.getElementById("chamados-finalizados");

    async function carregarChamadosFinalizados(dias = 1) {
        const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
        console.log("Grupo selecionado para finalizados:", grupoSelecionado);

        if (!grupoSelecionado) {
            campoChamadosFinalizados.textContent = "Grupo não definido";
            console.warn("Nenhum grupo selecionado no sessionStorage para finalizados");
            return;
        }

        try {
            const response = await fetch('/grupos/chamados/grupos/finalizados', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dias: dias,
                    grupo: grupoSelecionado
                })
            });

            const data = await response.json();
            console.log("Dados recebidos finalizados:", data);

            if (data.status === "success") {
                campoChamadosFinalizados.textContent = data.total_chamados;
            } else {
                campoChamadosFinalizados.textContent = "Erro ao carregar";
                console.error(data.message);
            }
        } catch (error) {
            campoChamadosFinalizados.textContent = "Erro de conexão";
            console.error("Erro na requisição finalizados:", error);
        }
    }

    botoesPeriodo.forEach(button => {
        button.addEventListener("click", function () {
            botoesPeriodo.forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");

            const dias = parseInt(this.getAttribute("data-dias"), 10);
            carregarChamadosFinalizados(dias);
        });
    });

    carregarChamadosFinalizados(); // chamada inicial com 1 dia ou o padrão que quiser
});


// Bloco que traz os chamados em aberto com os grupos-->
 
document.addEventListener("DOMContentLoaded", function () {
    const campoTotalChamados = document.getElementById("ChamadosEmAbertoSuporte");
    let codigosEmAberto = [];

    async function carregarChamadosAbertos(dias = 1) {
        const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
        console.log(" Grupo selecionado para chamados abertos:", grupoSelecionado);

        if (!grupoSelecionado) {
            campoTotalChamados.textContent = "Grupo não definido";
            console.warn("Nenhum grupo selecionado no sessionStorage para chamados abertos");
            return;
        }

        try {
            const response = await fetch('/grupos/chamados/grupos/abertos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dias: dias,
                    grupo: grupoSelecionado
                })
            });

            const data = await response.json();
            console.log("Dados recebidos chamados abertos:", data);

            if (data.status === "success") {
                campoTotalChamados.textContent = data.total_chamados;
                codigosEmAberto = data.codigos || [];
            } else {
                campoTotalChamados.textContent = "Erro ao carregar";
                console.error(data.message);
                codigosEmAberto = [];
            }
        } catch (error) {
            campoTotalChamados.textContent = "Erro de conexão";
            console.error("Erro na requisição chamados abertos:", error);
            codigosEmAberto = [];
        }
    }

    window.mostrarCodigosChamadosAbertos = function(titulo, listaCodigos) {
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
    };

    // Se tiver filtros de período, conecte aqui como nos exemplos anteriores
    carregarChamadosAbertos(1);
});


// Bloco que traz o SLAs dos grupos -->

  let codigosAtendimento = [];
  let codigosResolucao = [];

  function mostrarCodigosSla(titulo, listaCodigos) {
    const lista = document.getElementById("listaChamados");
    const tituloModal = document.getElementById("modalChamadosExpiradosLabel");

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

    const modal = new bootstrap.Modal(document.getElementById("modalChamadosExpirados"));
    modal.show();
  }

  async function carregarSlaGrupo(dias = 1) {
    const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
    if (!grupoSelecionado) {
      document.getElementById("sla_atendimento_expirado").textContent = "Grupo não definido";
      document.getElementById("sla_atendimento_prazo").textContent = "-";
      document.getElementById("sla_resolucao_expirado").textContent = "-";
      document.getElementById("percentual_prazo_resolucao").textContent = "-";
      codigosAtendimento = [];
      codigosResolucao = [];
      return;
    }

    try {
      const response = await fetch('/grupos/sla/grupos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias: dias, grupo: grupoSelecionado })
      });

      const data = await response.json();

      if (data.status === "success") {
        document.getElementById("sla_atendimento_expirado").textContent = data.percentual_atendimento.toFixed(2) + "%";
        document.getElementById("sla_atendimento_prazo").textContent = data.percentual_prazo_atendimento.toFixed(2) + "%";
        document.getElementById("sla_resolucao_expirado").textContent = data.percentual_resolucao.toFixed(2) + "%";
        document.getElementById("percentual_prazo_resolucao").textContent = data.percentual_prazo_resolucao.toFixed(2) + "%";

        codigosAtendimento = data.codigos_atendimento || [];
        codigosResolucao = data.codigos_resolucao || [];
      } else {
        document.getElementById("sla_atendimento_expirado").textContent = "Erro";
        document.getElementById("sla_atendimento_prazo").textContent = "-";
        document.getElementById("sla_resolucao_expirado").textContent = "Erro";
        document.getElementById("percentual_prazo_resolucao").textContent = "-";

        codigosAtendimento = [];
        codigosResolucao = [];
      }
    } catch (error) {
      console.error("Erro ao carregar SLA grupo:", error);

      document.getElementById("sla_atendimento_expirado").textContent = "Erro";
      document.getElementById("sla_atendimento_prazo").textContent = "-";
      document.getElementById("sla_resolucao_expirado").textContent = "Erro";
      document.getElementById("percentual_prazo_resolucao").textContent = "-";

      codigosAtendimento = [];
      codigosResolucao = [];
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    carregarSlaGrupo(1);

    document.querySelectorAll(".filtro-btn").forEach(button => {
      button.addEventListener("click", () => {
        const dias = parseInt(button.getAttribute("data-dias"), 10);
        carregarSlaGrupo(dias);
      });
    });
  });


// Bloco que me traz a pesquisa de satisfação para grupos-->

  async function carregarPesquisaSatisfacao(dias = 1) {
    const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
    if (!grupoSelecionado) {
      document.getElementById("csat-percentual").textContent = "Grupo não definido";
      document.getElementById("total-avaliado").textContent = "-";
      return;
    }

    try {
      const response = await fetch('/grupos/pSatisfacao/grupos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias, grupo: grupoSelecionado })
      });

      const data = await response.json();

      if (data.status === "success") {
        document.getElementById("csat-percentual").textContent = `${data.csat}%`;
        document.getElementById("total-avaliado").textContent = data.total_respondidas;
      } else {
        document.getElementById("csat-percentual").textContent = "Erro";
        document.getElementById("total-avaliado").textContent = "-";
      }
    } catch (error) {
      console.error("Erro ao carregar pesquisa de satisfação:", error);
      document.getElementById("csat-percentual").textContent = "Erro";
      document.getElementById("total-avaliado").textContent = "-";
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    carregarPesquisaSatisfacao(1);
    document.querySelectorAll(".filtro-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const dias = parseInt(btn.getAttribute("data-dias"), 10);
        carregarPesquisaSatisfacao(dias);
      });
    });
  });



// Bloco que traz os abertos vs resolvidos -->


  let chartAbertosResolvidos;

  async function carregarGraficoAbertosResolvidos(dias = 7) {
    const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
    if (!grupoSelecionado) {
      console.warn("Grupo não selecionado.");
      return;
    }

    try {
      const response = await fetch('/grupos/abertos_grupos_resolvido', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias: dias, grupo: grupoSelecionado })
      });

      const data = await response.json();

      if (data.status !== "success") {
        console.error("Erro ao carregar dados do gráfico.");
        return;
      }

      // Atualiza os resumos abaixo do gráfico
      document.getElementById("adminTotalAbertos").textContent = data.resumo.abertos;
      document.getElementById("adminTotalResolvidos").textContent = data.resumo.resolvidos;
      document.getElementById("adminDiferenca").textContent = data.resumo.diferenca;

      // Renderiza ou atualiza o gráfico
      const ctx = document.getElementById("LinhaAbertosResolvidosAdminChart").getContext("2d");

      if (chartAbertosResolvidos) {
        chartAbertosResolvidos.data.labels = data.labels;
        chartAbertosResolvidos.data.datasets = data.datasets;
        chartAbertosResolvidos.update();
      } else {
        chartAbertosResolvidos = new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.labels,
            datasets: data.datasets
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  stepSize: 1
                }
              }
            }
          }
        });
      }

    } catch (error) {
      console.error("Erro na requisição:", error);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    carregarGraficoAbertosResolvidos(7); // ou o valor que quiser como padrão

    // Botões de filtro por período (se houver)
    document.querySelectorAll(".filtro-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const dias = parseInt(btn.getAttribute("data-dias"), 10);
        carregarGraficoAbertosResolvidos(dias);
      });
    });
  });


// Bloco que traz os tickets por operador-->

  let chartTicketsOperador;

  async function carregarGraficoTicketsPorOperador(dias = 30) {
    const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
    if (!grupoSelecionado) {
      console.warn("Grupo não selecionado.");
      return;
    }

    try {
      const response = await fetch('/grupos/ticketsOperador', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias: dias, grupo: grupoSelecionado })
      });

      const data = await response.json();

      if (data.status !== "success") {
        console.error("Erro ao carregar dados:", data.message);
        return;
      }

      const ctx = document.getElementById('OperadorAtendimentoChart').getContext('2d');

      if (chartTicketsOperador) {
        chartTicketsOperador.destroy();
      }

      chartTicketsOperador = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.data.labels,
          datasets: data.data.datasets
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              display: false,
              labels: { color: '#fff' }  // Legendas em branco (caso habilite depois)
            },
            title: {
              display: true,
              text: data.data_referencia,
              color: '#fff'  // Título do gráfico em branco
            },
            tooltip: {
              titleColor: '#fff',
              bodyColor: '#fff',
              backgroundColor: 'rgba(0,0,0,0.7)',
              callbacks: {
                label: function (context) {
                  return `Chamados: ${context.raw}`;
                }
              }
            }
          },
          scales: {
            x: {
              ticks: { color: '#fff' },  // Texto do eixo X em branco
              grid: { color: 'rgba(255,255,255,0.1)' }
            },
            y: {
              beginAtZero: true,
              ticks: {
                color: '#fff',  // Texto do eixo Y em branco
                precision: 0
              },
              grid: { color: 'rgba(255,255,255,0.1)' }
            }
          }
        }
      });

    } catch (error) {
      console.error("Erro na requisição:", error);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    carregarGraficoTicketsPorOperador(30);

    document.querySelectorAll(".filtro-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const dias = parseInt(btn.getAttribute("data-dias"), 10);
        carregarGraficoTicketsPorOperador(dias);
      });
    });
  });


// Bloco que traz o top 5 de tipos ocorrências-->

document.addEventListener('DOMContentLoaded', function () {
  carregarTopTipos(1); // valor padrão ao carregar a página
});

// Listener para botões de filtro (se existirem)
document.querySelectorAll('.filtro-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    const dias = parseInt(this.getAttribute('data-dias'));
    carregarTopTipos(dias);
  });
});

// Função que busca e exibe os dados
function carregarTopTipos(dias = 1) {
  const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
  if (!grupoSelecionado) {
    console.warn("Grupo não selecionado.");
    const lista = document.getElementById('top-tipo-ocorrencia');
    lista.innerHTML = '<li class="list-group-item bg-transparent text-danger">Grupo não selecionado</li>';
    return;
  }

  console.log('Carregando topTipoChamados com dias =', dias, 'e grupo =', grupoSelecionado);

  fetch('/grupos/topTipoChamadosGrupos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias, grupo: grupoSelecionado })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Erro na resposta da API');
    }
    return response.json();
  })
  .then(data => {
    console.log('Dados recebidos:', data);

    const lista = document.getElementById('top-tipo-ocorrencia');
    lista.innerHTML = '';

    const dados = data.dados;

    if (!dados || dados.length === 0) {
      lista.innerHTML = '<li class="list-group-item bg-transparent text-white">Nenhum tipo encontrado</li>';
    } else {
      dados.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item bg-transparent text-white d-flex justify-content-between';
        li.innerHTML = `<span>${item.tipo}</span><span><strong>${item.quantidade}</strong></span>`;
        lista.appendChild(li);
      });
    }
  })
  .catch(error => {
    console.error('Erro ao carregar top tipos:', error);
    const lista = document.getElementById('top-tipo-ocorrencia');
    lista.innerHTML = '<li class="list-group-item bg-transparent text-danger">Erro ao carregar</li>';
  });
}



//Script que traz os dados de Ticket por Canal-->

  function carregarTicketsPorCanal(dias = 30) {
    const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
    if (!grupoSelecionado) {
      console.warn("Grupo não selecionado.");
      return;
    }

    fetch('/grupos/tickets_grupos_canal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias: dias, grupo: grupoSelecionado })  // Envia o grupo também
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

    carregarTicketsPorCanal(30); // valor inicial padrão
  });


// Bloco que traz as categorias-->

document.addEventListener('DOMContentLoaded', function () {
  carregarTopCategorias(1); // padrão 1 dia ao carregar a página
});

// Listener para os botões de filtro (se houver)
document.querySelectorAll('.filtro-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    const dias = parseInt(this.getAttribute('data-dias'));
    carregarTopCategorias(dias);
  });
});

function carregarTopCategorias(dias = 1) {
  const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
  if (!grupoSelecionado) {
    console.warn("Grupo não selecionado.");
    const lista = document.getElementById('top-categorias');
    lista.innerHTML = '<li class="list-group-item bg-transparent text-danger">Grupo não selecionado</li>';
    return;
  }

  console.log('Carregando topCategoriaGrupos com dias =', dias, 'e grupo =', grupoSelecionado);

  fetch('/grupos/topCategoriaGrupos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias, grupo: grupoSelecionado })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Erro na resposta da API');
    }
    return response.json();
  })
  .then(data => {
    console.log('Dados recebidos:', data);

    const lista = document.getElementById('top-categorias');
    lista.innerHTML = '';

    const dados = data.dados;

    if (!dados || dados.length === 0) {
      lista.innerHTML = '<li class="list-group-item bg-transparent text-white">Nenhuma categoria encontrada</li>';
    } else {
      dados.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item bg-transparent text-white d-flex justify-content-between';
        li.innerHTML = `<span>${item.nome}</span><span><strong>${item.quantidade}</strong></span>`;
        lista.appendChild(li);
      });
    }
  })
  .catch(error => {
    console.error('Erro ao carregar top categorias:', error);
    const lista = document.getElementById('top-categorias');
    lista.innerHTML = '<li class="list-group-item bg-transparent text-danger">Erro ao carregar</li>';
  });
}


//Bloco que traz as subcategorias -->

  document.addEventListener('DOMContentLoaded', function () {
    carregarTopSubCategorias(1); // Carrega padrão 1 dia
  });

  // Botões filtro, se houver
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'), 10);
      carregarTopSubCategorias(dias);
    });
  });

  async function carregarTopSubCategorias(dias = 1) {
    const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
    if (!grupoSelecionado) {
      console.warn("Grupo não selecionado.");
      return;
    }

    try {
      const response = await fetch('/grupos/topSubCategoriaGrupos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias: dias, grupo: grupoSelecionado })
      });

      const data = await response.json();

      if (data.status !== "success") {
        console.error("Erro ao carregar top subcategorias");
        return;
      }

      const lista = document.getElementById('top-sub-categorias');
      lista.innerHTML = '';

      if (!data.dados || data.dados.length === 0) {
        lista.innerHTML = '<li class="list-group-item bg-transparent text-white">Nenhuma subcategoria encontrada</li>';
      } else {
        data.dados.forEach(item => {
          const li = document.createElement('li');
          li.className = 'list-group-item bg-transparent text-white d-flex justify-content-between';
          li.innerHTML = `<span>${item.nome}</span><span><strong>${item.quantidade}</strong></span>`;
          lista.appendChild(li);
        });
      }

    } catch (error) {
      console.error("Erro ao carregar top subcategorias:", error);
      const lista = document.getElementById('top-sub-categorias');
      lista.innerHTML = '<li class="list-group-item bg-transparent text-danger">Erro ao carregar</li>';
    }
  }


// Bloco que traz o gráfico de SLA -->

document.addEventListener("DOMContentLoaded", () => {
    const modalElement = document.getElementById('modalChamadosGrupos');
    const listaChamados = document.getElementById('listaChamadosGrupos');
    const modalInstance = new bootstrap.Modal(modalElement);
    const carousel = document.getElementById('carouselGraficos');

    let chart1 = null;
    let chart2 = null;

    const grupo = sessionStorage.getItem("grupoSelecionado") || "";

    let dadosSlaGrupo = null; // Armazena os dados para renderizar no momento certo

    fetch('/grupos/slaAndamentoGrupos', {
        method: 'POST',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ grupo: grupo })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            dadosSlaGrupo = data; // salva para uso futuro
        } else {
            console.error('Erro ao carregar dados de SLA por grupo:', data.message);
        }
    })
    .catch(e => console.error('Erro na requisição SLA por grupo:', e));

    const criarSlaGrupoChart = (ctx, label, naoExpirado, quaseEstourando, expirado, codigosCriticos, codigosExpirados) => {
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
                        } else if (idx === 2 && codigosExpirados.length > 0) {
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
    };

    // Ouça o evento de exibição do slide
    carousel.addEventListener('slid.bs.carousel', event => {
        const activeIndex = Array.from(carousel.querySelectorAll('.carousel-item')).findIndex(item => item.classList.contains('active'));

        // Slide 2 é o segundo (índice 1)
        if (activeIndex === 1 && dadosSlaGrupo) {
            if (!chart1 && !chart2) {
                const ctx1 = document.getElementById('slaGrupoChart').getContext('2d');
                const ctx2 = document.getElementById('slaGrupoChart2').getContext('2d');

                chart1 = criarSlaGrupoChart(
                    ctx1,
                    'SLA - Atendimento',
                    dadosSlaGrupo.sla1_nao_expirado,
                    dadosSlaGrupo.sla1_quase_estourando || 0,
                    dadosSlaGrupo.sla1_expirado,
                    dadosSlaGrupo.codigos_sla1_critico || [],
                    dadosSlaGrupo.codigos_sla1 || []
                );
                chart2 = criarSlaGrupoChart(
                    ctx2,
                    'SLA - Resolução',
                    dadosSlaGrupo.sla2_nao_expirado,
                    dadosSlaGrupo.sla2_quase_estourando || 0,
                    dadosSlaGrupo.sla2_expirado,
                    dadosSlaGrupo.codigos_sla2_critico || [],
                    dadosSlaGrupo.codigos_sla2 || []
                );
            }
        }
    });
});



// Bloco que traz o TMA e TMS -->

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

  async function carregarTmaTms(dias) {
    const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";

    if (!grupoSelecionado) {
      console.warn("Nenhum grupo selecionado no sessionStorage");
      document.getElementById("percentual-tma").innerText = "-";
      document.getElementById("percentual-tms").innerText = "-";
      return;
    }

    try {
      const response = await fetch('/grupos/tma_tms_grupos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          dias: dias,
          grupo: grupoSelecionado
        })
      });

      const data = await response.json();

      if (data.status === "success") {
        document.getElementById("percentual-tma").innerText = data.mediana_tma;
        document.getElementById("percentual-tms").innerText = data.mediana_tms;
      } else {
        console.error("Erro ao carregar TMA/TMS:", data.message);
        document.getElementById("percentual-tma").innerText = "-";
        document.getElementById("percentual-tms").innerText = "-";
      }
    } catch (err) {
      console.error("Erro na requisição TMA/TMS:", err);
      document.getElementById("percentual-tma").innerText = "-";
      document.getElementById("percentual-tms").innerText = "-";
    }
  }


// Script que busca os chamados FCR -->

  let chamadosFcrCodigos = [];

  document.addEventListener("DOMContentLoaded", function () {
    carregarFcrPorGrupo(1); // Carrega padrão 1 dia

    // Botões de filtro por período
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        const dias = parseInt(this.getAttribute('data-dias'), 10);
        carregarFcrPorGrupo(dias);
      });
    });
  });

  async function carregarFcrPorGrupo(dias = 1) {
    const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
    if (!grupoSelecionado) {
      console.warn("Grupo não selecionado.");
      return;
    }

    try {
      const response = await fetch('/grupos/fcrGrupos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias, grupo: grupoSelecionado })
      });

      const data = await response.json();
      const fcrSpan = document.getElementById("chamado_fcr");
      const percentualSpan = document.getElementById("percentual_fcr");

      if (data.status === "success") {
        const totalFcr = data.total_fcr || 0;
        const percentual = data.percentual_fcr ?? "-";

        fcrSpan.textContent = totalFcr;
        percentualSpan.textContent = typeof percentual === "number" ? percentual.toFixed(1) + "%" : percentual;

        chamadosFcrCodigos = data.cod_chamados || [];
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


// Script que me traz a relação de chamados reabertos-->

  let chamadosReabertosCodigos = [];

  document.addEventListener("DOMContentLoaded", function () {
    carregarChamadosReabertos(1); // Chamada inicial com 1 dia

    // Atualiza ao clicar no botão de filtro de dias
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        const dias = parseInt(this.getAttribute('data-dias'), 10);
        carregarChamadosReabertos(dias);
      });
    });
  });

  async function carregarChamadosReabertos(dias = 1) {
    const grupoSelecionado = sessionStorage.getItem('grupoSelecionado') || "";
    if (!grupoSelecionado) {
      console.warn("Grupo não selecionado.");
      return;
    }

    try {
      const response = await fetch('/grupos/reabertosGrupos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dias, grupo: grupoSelecionado })
      });

      const data = await response.json();
      const reabertosSpan = document.getElementById("chamado_reaberto");
      const percentualSpan = document.getElementById("percentual_reaberto");

      if (data.status === "success") {
        const total = data.total_chamados || 0;
        const reabertos = data.total_reabertos || 0;
        chamadosReabertosCodigos = data.cod_chamados || [];

        reabertosSpan.textContent = reabertos;

        // Cálculo do percentual
        let percentual = "-";
        if (total > 0) {
          percentual = ((reabertos / total) * 100).toFixed(1) + "%";
        }

        percentualSpan.textContent = percentual;
      } else {
        reabertosSpan.textContent = "Erro";
        percentualSpan.textContent = "-";
        chamadosReabertosCodigos = [];
        console.error("Erro na resposta:", data.message);
      }
    } catch (error) {
      console.error("Erro ao buscar reabertos:", error);
      document.getElementById("chamado_reaberto").textContent = "Erro";
      document.getElementById("percentual_reaberto").textContent = "-";
      chamadosReabertosCodigos = [];
    }
  }

  // Essa função já serve para qualquer lista de chamados (FCR, Reabertos, etc.)
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


