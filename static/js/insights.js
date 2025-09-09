// Script que me traz os chamados abertos
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


// Script que traz os botões com os nomes dos operadores-->

document.addEventListener('DOMContentLoaded', function () {

    async function carregarOperadores() {
        try {
            const response = await fetch('/insights/get/operadores');
            const data = await response.json();

            if (data.status === "success") {
                const container = document.getElementById('botoes-operadores');

                const operadoresOrdenados = data.operadores.sort((a, b) => a.localeCompare(b));

                operadoresOrdenados.forEach(operador => {
                    const botao = document.createElement('button');
                    botao.className = 'btn btn-outline-primary operador-btn d-flex align-items-center';

                    const icone = document.createElement('i');
                    icone.className = 'bi bi-pie-chart-fill me-2';

                    const texto = document.createElement('span');
                    texto.textContent = operador;

                    botao.appendChild(icone);
                    botao.appendChild(texto);
                    botao.dataset.operador = operador;

                    botao.onclick = function () {
                        document.querySelectorAll('.operador-btn').forEach(btn => btn.classList.remove('active'));
                        this.classList.add('active');
                        filtrarPorOperador(operador);
                    };

                    container.appendChild(botao);
                });

                if (container.firstChild) {
                    container.firstChild.classList.add('active');
                }
            }

        } catch (error) {
            console.error('Erro ao carregar operadores:', error);
        }
    }

    function filtrarPorOperador(operador) {
        const nomesNivel2 = ['Eduardo', 'Chrysthyanne', 'Fernando', 'Luciano', 'Maria Luiza'];

        // Verificação com nomes case-insensitive
        const operadorNormalizado = operador.trim().toLowerCase();
        const rota = nomesNivel2.map(n => n.toLowerCase()).includes(operadorNormalizado)
            ? '/operadores/performanceColaboradoresRender/n2'
            : '/operadores/performanceColaboradoresRender';

        console.log(`Nome selecionado: ${operador}`);
        console.log(`Rota selecionada: ${rota}`);

        fetch(rota, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome: operador })
        })
        .then(res => res.json())
        .then(data => {
            if (data.redirect_url) {
                console.log('Redirecionando para:', data.redirect_url);
                window.location.href = data.redirect_url;
            } else {
                console.warn('Nenhuma URL de redirecionamento recebida.');
            }
        })
        .catch(error => {
            console.error('Erro ao enviar operador para o backend:', error);
        });
    }

    carregarOperadores();
});

// Script que traz os botões de grupos -->

document.addEventListener('DOMContentLoaded', function () {

    async function carregarGrupos() {
        try {
            const response = await fetch('/insights/get/grupos');
            const data = await response.json();

            if (data.status === "success") {
                const container = document.getElementById('botoes-grupos');

                const gruposOrdenados = data.grupos.sort((a, b) => a.localeCompare(b));

                gruposOrdenados.forEach(grupo => {
                    const botao = document.createElement('button');
                    botao.className = 'btn btn-outline-success grupos-btn d-flex align-items-center';

                    const icone = document.createElement('i');
                    icone.className = 'bi bi-people-fill me-2';

                    const texto = document.createElement('span');
                    texto.textContent = grupo;

                    botao.appendChild(icone);
                    botao.appendChild(texto);
                    botao.dataset.grupo = grupo;

                    botao.onclick = function () {
                        // Marca o botão como ativo
                        document.querySelectorAll('.grupos-btn').forEach(btn => btn.classList.remove('active'));
                        this.classList.add('active');

                        // ✅ Armazena o grupo selecionado no sessionStorage
                        sessionStorage.setItem('grupoSelecionado', grupo);

                        // Redireciona via backend
                        filtrarPorGrupo(grupo);
                    };

                    container.appendChild(botao);
                });

                // Define o primeiro como ativo
                if (container.firstChild) {
                    container.firstChild.classList.add('active');
                }
            }

        } catch (error) {
            console.error('Erro ao carregar grupos:', error);
        }
    }

    function filtrarPorGrupo(grupo) {
        console.log(`Grupo selecionado: ${grupo}`);

        fetch('/grupos/render/grupos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ grupo: grupo })
        })
        .then(res => res.json())
        .then(data => {
            if (data.redirect_url) {
                console.log('Redirecionando para:', data.redirect_url);
                window.location.href = data.redirect_url;
            } else {
                console.warn('Nenhuma URL de redirecionamento recebida.');
            }
        })
        .catch(error => {
            console.error('Erro ao enviar grupo para o backend:', error);
        });
    }

    carregarGrupos();

    // (Opcional) Limpa o sessionStorage ao sair da página
    window.addEventListener("beforeunload", function () {
        sessionStorage.removeItem('grupoSelecionado');
    });
});


// Script que traz os chamados finalizados pelo suporte-->

document.addEventListener("DOMContentLoaded", function () {
    function carregarChamadosFinalizados(dias = 7) {
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


// Atualização dinâmica dos chamados em aberto -->

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
    fetch('/insights/sla', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias: dias })
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === "success") {
        document.getElementById("sla_atendimento_expirado").textContent = data.percentual_atendimento + "%";
        document.getElementById("sla_atendimento_prazo").textContent = data.percentual_prazo_atendimento + "%";
        document.getElementById("sla_resolucao_expirado").textContent = data.percentual_resolucao + "%";
        document.getElementById("percentual_prazo_resolucao").textContent = data.percentual_prazo_resolucao + "%";

        codigosAtendimento = data.codigos_atendimento || [];
        codigosResolucao = data.codigos_resolucao || [];
      } else {
        document.getElementById("sla_atendimento_expirado").textContent = "Erro";
        document.getElementById("sla_resolucao_expirado").textContent = "Erro";
      }
    })
    .catch(() => {
      document.getElementById("sla_atendimento_expirado").textContent = "Erro";
      document.getElementById("sla_resolucao_expirado").textContent = "Erro";
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

// Script que traz o top 5 de chamados filtrado por grupos-->

let diasSelecionados = 1; // Valor padrão inicial

function atualizarDashboard(dias) {
  carregarTopGrupos(dias);
  carregarTopClientes(dias);
  carregarChamadosAbertos(dias);
  carregarChamadosFinalizados(dias);
  carregarChamadosEmAberto(dias);
  carregarSlaGlobal(dias);
  carregarChamadosCriadosResolvidos(dias);
}

// Listener dos botões de período
document.querySelectorAll('.filtro-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    diasSelecionados = parseInt(this.getAttribute('data-dias'));
    atualizarDashboard(diasSelecionados);
  });
});

// Função: Top 5 grupos
function carregarTopGrupos(dias) {
  fetch('/insights/topGruposChamados', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias })
  })
  .then(res => res.json())
  .then(dados => {
    const lista = document.getElementById('top-grupos');
    lista.innerHTML = '';

    if (dados.length === 0) {
      lista.innerHTML = '<li class="list-group-item bg-transparent text-white">Nenhum grupo encontrado</li>';
    } else {
      dados.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item bg-transparent text-white d-flex justify-content-between';
        li.innerHTML = `<span>${item.grupo}</span><span><strong>${item.total}</strong></span>`;
        lista.appendChild(li);
      });
    }
  })
  .catch(err => {
    console.error('Erro ao carregar top grupos:', err);
    document.getElementById('top-grupos').innerHTML = '<li class="list-group-item bg-transparent text-danger">Erro ao carregar</li>';
  });
}

// Função: Top 5 clientes
function carregarTopClientes(dias) {
  fetch('/insights/topClientesChamados', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias })
  })
  .then(res => res.json())
  .then(dados => {
    const lista = document.getElementById('top-clientes');
    lista.innerHTML = '';

    if (dados.length === 0) {
      lista.innerHTML = '<li class="list-group-item bg-transparent text-white">Nenhum cliente encontrado</li>';
    } else {
      dados.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item bg-transparent text-white d-flex justify-content-between';
        li.innerHTML = `<span>${item.cliente}</span><span><strong>${item.total}</strong></span>`;
        lista.appendChild(li);
      });
    }
  })
  .catch(err => {
    console.error('Erro ao carregar top clientes:', err);
    document.getElementById('top-clientes').innerHTML = '<li class="list-group-item bg-transparent text-danger">Erro ao carregar</li>';
  });
}

// Carregamento inicial da dashboard
document.addEventListener('DOMContentLoaded', function () {
  atualizarDashboard(diasSelecionados);
});

//Script que traz o top 5 chamados filtrado por status-->

document.addEventListener('DOMContentLoaded', function () {
  carregarTopStatus(1); // valor inicial padrão
});

// Listener dos botões de filtro (se quiser manter eles funcionando com esse script)
document.querySelectorAll('.filtro-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    const dias = parseInt(this.getAttribute('data-dias'));
    carregarTopStatus(dias);
  });
});

// Função isolada: Top 5 Status
function carregarTopStatus(dias = 1) {
  console.log('carregando topStatus com dias =', dias);

  fetch('/insights/topStatusChamados', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Erro na resposta da API');
    }
    return response.json();
  })
  .then(data => {
    console.log('Dados recebidos:', data);
    const lista = document.getElementById('top-status');
    lista.innerHTML = '';

    if (!data || data.length === 0) {
      lista.innerHTML = '<li class="list-group-item bg-transparent text-white">Nenhum status encontrado</li>';
    } else {
      data.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item bg-transparent text-white d-flex justify-content-between';
        li.innerHTML = `<span>${item.status}</span><span><strong>${item.total}</strong></span>`;
        lista.appendChild(li);
      });
    }
  })
  .catch(error => {
    console.error('Erro ao carregar top status:', error);
    const lista = document.getElementById('top-status');
    lista.innerHTML = '<li class="list-group-item bg-transparent text-danger">Erro ao carregar</li>';
  });
}

// Script que traz o Top 5 tipos de ocorrência -->
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
  console.log('Carregando topTipoChamados com dias =', dias);

  fetch('/insights/topTipoChamados', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Erro na resposta da API');
    }
    return response.json(); // Converte corretamente para JSON
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

// Bloco que traz a relação dos chamados abertos e resolvidos-->

document.addEventListener("DOMContentLoaded", function () {
  // Listener para botões de filtro
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = parseInt(this.getAttribute('data-dias'));
      carregarAbertosResolvidos(dias);
    });
  });

  // Gráfico instância global para poder destruir ao atualizar
  let adminChartInstance = null;

  // Função que busca e exibe os dados
  function carregarAbertosResolvidos(dias = 1) {
    console.log('Carregando abertos x resolvidos com dias =', dias);

    fetch('/insights/abertos_vs_admin_resolvido_periodo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias: dias })  // agora usa o valor dinâmico corretamente
    })
    .then(res => res.json())
    .then(data => {
      if (data.status === "success") {
        const ctx = document.getElementById('LinhaAbertosResolvidosAdminChart').getContext('2d');

        // Destroi gráfico anterior se existir
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

        // Atualiza os totais
        document.getElementById("adminTotalAbertos").textContent = data.resumo.abertos;
        document.getElementById("adminTotalResolvidos").textContent = data.resumo.resolvidos;
        document.getElementById("adminDiferenca").textContent = data.resumo.diferenca;
      } else {
        console.error("Erro ao carregar dados:", data.message);
      }
    })
    .catch(error => console.error("Erro de conexão:", error));
  }

  // Carregamento inicial com 7 dias
  carregarAbertosResolvidos(1);
});

//Script que traz os dados de Abertos vs Status-->
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

    // Inicia com 7 dias e conecta aos botões
    document.addEventListener('DOMContentLoaded', () => {
        const botoesFiltro = document.querySelectorAll('.filtro-btn');

        // Clique nos botões de filtro
        botoesFiltro.forEach(botao => {
            botao.addEventListener('click', function () {
                botoesFiltro.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                const dias = parseInt(this.getAttribute('data-dias'));
                carregarDados(dias);
            });
        });

        // Carregamento inicial com 7 dias
        carregarDados(1);

        // Atualiza o gráfico se redimensionar a tela
        window.addEventListener('resize', () => {
            if (statusChart) statusChart.update();
        });
    });

//Script que traz os dados de Ticket por Canal-->
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
        // Botões com a classe "filtro-btn" e atributo data-dias
        const botoesFiltro = document.querySelectorAll('.filtro-btn');

        botoesFiltro.forEach(botao => {
            botao.addEventListener('click', () => {
                const dias = parseInt(botao.getAttribute('data-dias'), 10);
                
                // Remove classe "active" de todos os botões
                botoesFiltro.forEach(btn => btn.classList.remove('active'));

                // Adiciona classe "active" ao botão clicado
                botao.classList.add('active');

                // Atualiza o gráfico com o novo período
                carregarTicketsPorCanal(dias);
            });
        });

        // Carrega o gráfico inicialmente com 30 dias (ou o que desejar)
        carregarTicketsPorCanal(1);
    });

// Script que traz os dados de Tickets Operador-->
function carregarTicketsPorOperador(dias = 30) {
    fetch('/admin/ChamadosSuporte/ticketsOperador', {
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


//Script que me traz os SLAs filtrados por grupo-->
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

                        if (idx === 1 && codigosCriticos.length > 0) { // Quase Estourando
                            codigos = codigosCriticos;
                        } else if (idx === 2 && codigosExpirados.length > 0) { // Expirado
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
                    data.codigos_sla1 || []
                );
                criarSlaGrupoChart(
                    document.getElementById('slaGrupoChart2').getContext('2d'),
                    'SLA - Resolução',
                    data.sla2_nao_expirado,
                    data.sla2_quase_estourando || 0,
                    data.sla2_expirado,
                    data.codigos_sla2_critico || [],
                    data.codigos_sla2 || []
                );
            } else {
                console.error('Erro ao carregar dados de SLA por grupo:', data.message);
            }
        })
        .catch(e => console.error('Erro na requisição SLA por grupo:', e));
});

//Script que me traz os SLAs filtrados por grupo Suporte-->
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

                        if (idx === 1 && codigosCriticos.length > 0) { // Quase estourando
                            codigos = codigosCriticos;
                        } else if (idx === 2 && codigosExpirados.length > 0) { // Expirado
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
                    data.codigos_sla1 || [],
                    data.codigos_sla1_critico || []
                );
                criarSlaChart(
                    document.getElementById('slaChart2').getContext('2d'),
                    'SLA - Resolução',
                    data.sla2_nao_expirado,
                    data.sla2_quase_estourando || 0,
                    data.sla2_expirado,
                    data.codigos_sla2 || [],
                    data.codigos_sla2_critico || []
                );
            } else {
                console.error('Erro no carregamento dos dados SLA:', data.message);
            }
        })
        .catch(e => console.error('Erro na requisição SLA:', e));
});

//Script que traz o top 5 Sub Categorias-->
document.addEventListener('DOMContentLoaded', function () {
  carregarTopSubCategorias(1); // valor padrão: 1 dia
});

// Opcional: se tiver botões com a classe 'filtro-btn', ele usa os mesmos para esse gráfico
document.querySelectorAll('.filtro-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    const dias = parseInt(this.getAttribute('data-dias'));
    carregarTopSubCategorias(dias);
  });
});

function carregarTopSubCategorias(dias = 1) {
  console.log('Carregando topSubCategorias com dias =', dias);

  fetch('/insights/topSubCategoria', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ dias })
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Erro ao buscar topSubCategorias');
      }
      return response.json();
    })
    .then(data => {
      const lista = document.getElementById('top-sub-categorias');
      lista.innerHTML = '';

      const subcategorias = data.dados;

      if (!subcategorias || subcategorias.length === 0) {
        lista.innerHTML = '<li class="list-group-item bg-transparent text-white">Nenhuma subcategoria encontrada</li>';
      } else {
        subcategorias.forEach(item => {
          const li = document.createElement('li');
          li.className = 'list-group-item bg-transparent text-white d-flex justify-content-between';
          li.innerHTML = `<span>${item.nome}</span><span><strong>${item.quantidade}</strong></span>`;
          lista.appendChild(li);
        });
      }
    })
    .catch(error => {
      console.error('Erro ao carregar subcategorias:', error);
      const lista = document.getElementById('top-sub-categorias');
      lista.innerHTML = '<li class="list-group-item bg-transparent text-danger">Erro ao carregar</li>';
    });
}


//Script que traz o top 5 Categorias-->
document.addEventListener('DOMContentLoaded', function () {
  carregarTopCategorias(1); // Valor padrão: últimos 1 dia
});

// Permite mudar o período via botões se desejar
document.querySelectorAll('.filtro-btn').forEach(btn => {
  btn.addEventListener('click', function () {
    const dias = parseInt(this.getAttribute('data-dias'));
    carregarTopCategorias(dias);
  });
});

function carregarTopCategorias(dias = 1) {
  fetch('/insights/topCategoria', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dias })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Erro ao buscar categorias');
    }
    return response.json();
  })
  .then(data => {
    const lista = document.getElementById('top-categorias');
    lista.innerHTML = '';

    const categorias = data.dados;

    if (!categorias || categorias.length === 0) {
      lista.innerHTML = '<li class="list-group-item bg-transparent text-white">Nenhuma categoria encontrada</li>';
    } else {
      categorias.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item bg-transparent text-white d-flex justify-content-between';
        li.innerHTML = `<span>${item.nome}</span><span><strong>${item.quantidade}</strong></span>`;
        lista.appendChild(li);
      });
    }
  })
  .catch(error => {
    console.error('Erro ao carregar categorias:', error);
    const lista = document.getElementById('top-categorias');
    lista.innerHTML = '<li class="list-group-item bg-transparent text-danger">Erro ao carregar</li>';
  });
}

//Script que traz a pesquisa de satisfação-->
  document.addEventListener("DOMContentLoaded", function () {
    // Carrega o card com o valor padrão 30 dias
    atualizarCardPesquisaSatisfacao(1);

    // Seleciona todos os botões de filtro
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function() {
        // Remove a classe active de todos os botões para estilização (opcional)
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        // Adiciona classe active no botão clicado (opcional)
        this.classList.add('active');

        // Pega o número de dias do data-attribute do botão clicado
        const dias = parseInt(this.getAttribute('data-dias'), 10);
        atualizarCardPesquisaSatisfacao(dias);
      });
    });
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
    } else {
      csatPercentualEl.textContent = '-';
      totalAvaliadoEl.textContent = '-';
      console.error("Erro ao buscar dados da pesquisa:", data);
    }
  })
  .catch(error => {
    document.getElementById("csat-percentual").textContent = '-';
    document.getElementById("total-avaliado").textContent = '-';
    console.error("Erro de conexão com a API de pesquisa:", error);
  });
}


// Script que traz o TMA eo TMS -->
  document.addEventListener("DOMContentLoaded", function () {
    // Define dias padrão
    let diasSelecionados = 30;
    carregarTmaTms(diasSelecionados);

    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        // Remove classe active
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        // Adiciona active no clicado
        this.classList.add('active');

        diasSelecionados = parseInt(this.getAttribute('data-dias'), 10);
        carregarTmaTms(diasSelecionados);
      });
    });
  });

  function carregarTmaTms(dias) {
    fetch(`/insights/tma_tms?dias=${dias}`)
      .then(response => response.json())
      .then(data => {
        if (data.status === "success") {
          document.getElementById("percentual-tma").innerText = data.mediana_tma;
          document.getElementById("percentual-tms").innerText = data.mediana_tms;
        } else {
          console.error("Erro ao carregar TMA/TMS:", data.message);
        }
      })
      .catch(err => {
        console.error("Erro na requisição TMA/TMS:", err);
      });
  }

// Script do botão mestre (não interfere nos demais scripts) -->
  document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("toggle-botoes");
    const botoesOperadores = document.getElementById("botoes-operadores");
    const botoesGrupos = document.getElementById("botoes-grupos");

    let visiveis = false; // começam visíveis

    toggleBtn.addEventListener("click", function () {
      visiveis = !visiveis;

      // Alterna apenas a visibilidade, sem mexer no layout geral
      if (visiveis) {
        botoesOperadores.classList.remove("d-none");
        botoesOperadores.classList.add("d-flex");
        botoesGrupos.classList.remove("d-none");
        botoesGrupos.classList.add("d-flex");
        this.innerHTML = '<i class="bi bi-eye-slash me-1"></i>';
      } else {
        botoesOperadores.classList.remove("d-flex");
        botoesOperadores.classList.add("d-none");
        botoesGrupos.classList.remove("d-flex");
        botoesGrupos.classList.add("d-none");
        this.innerHTML = '<i class="bi bi-eye me-1"></i>';
      }
    });
  });

// Script que busca os chamados FCR -->
  let chamadosFcrCodigos = [];

  document.addEventListener("DOMContentLoaded", function () {
    // Botões de filtro por período
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        const dias = parseInt(this.getAttribute('data-dias'), 10);
        atualizarFCR(dias);
      });
    });
  });

  function atualizarFCR(dias, nomeOperador) {
    fetch('/insights/fcr', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias })
    })
    .then(response => response.json())
    .then(data => {
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
    })
    .catch(error => {
      console.error("Erro ao buscar FCR:", error);
      document.getElementById("chamado_fcr").textContent = "Erro";
      document.getElementById("percentual_fcr").textContent = "-";
      chamadosFcrCodigos = [];
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

//Script que retorna a relação de CES-->
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

                // Limpa classes de cor anteriores
                campoDescricao.classList.remove("text-primary", "text-warning", "text-danger");

                // Adiciona a classe conforme a descrição
                switch (data.descricao) {
                    case 'Baixo esforço':
                        campoDescricao.classList.add('text-primary'); // azul
                        break;
                    case 'Esforço moderado':
                        campoDescricao.classList.add('text-warning'); // amarelo
                        break;
                    case 'Alto esforço':
                        campoDescricao.classList.add('text-danger'); // vermelho
                        break;
                    default:
                        // sem estilo extra
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


//Script que retorna a relação de NPS-->
  document.addEventListener("DOMContentLoaded", function () {
  // Carrega o card NPS com valor padrão 1 dia
  atualizarNps(1);

  // Seleciona todos os botões de filtro
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      // Remove classe active de todos os botões
      document.querySelectorAll('.filtro-btn').forEach(b => b.classList.remove('active'));
      // Adiciona classe active no botão clicado
      this.classList.add('active');

      // Pega número de dias do atributo data-dias
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
      // Atualiza texto
      npsNullEl.textContent = data.status;
      npsRetornoEl.textContent = data.nps + "%";

      // Remove classes antigas e adiciona nova classe conforme status
      npsNullEl.className = 'value';       // reseta classes
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
          // Sem estilo extra
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


// Script que me traz a relação de chamados reabertos-->
  let chamadosReabertosCodigos = [];

  document.addEventListener("DOMContentLoaded", function () {
    // Atualiza ao clicar no botão de filtro de dias
    document.querySelectorAll('.filtro-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        const dias = parseInt(this.getAttribute('data-dias'), 10);
        atualizarReabertos(dias);
      });
    });
  });

  function atualizarReabertos(dias, nomeOperador) {
    fetch('/insights/reabertos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dias })
    })
    .then(response => response.json())
    .then(data => {
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
    })
    .catch(error => {
      console.error("Erro ao buscar reabertos:", error);
      document.getElementById("chamado_reaberto").textContent = "Erro";
      document.getElementById("percentual_reaberto").textContent = "-";
      chamadosReabertosCodigos = [];
    });
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

// Script que retorna as ligações atendidas-->
document.addEventListener("DOMContentLoaded", function () {
  // Chama automaticamente com filtro padrão = 1 ao renderizar
  atualizarLigacoes(1);

  // Atualiza ao clicar nos botões de filtro de dias
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



// Script que retorna as ligações não atendidas
document.addEventListener("DOMContentLoaded", function () {
  // Chama automaticamente com filtro padrão = hoje ao renderizar
  atualizarLigacoesPerdidas(1);

  // Atualiza ao clicar nos botões de filtro de dias
  document.querySelectorAll('.filtro-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const dias = this.getAttribute('data-dias'); 
      atualizarLigacoesPerdidas(dias);
    });
  });
});

// Script que traz as ligações perdidas
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


// Script que retorna as ligações efetuadas
document.addEventListener("DOMContentLoaded", function () {
  const botoesPeriodo = document.querySelectorAll(".filtro-btn");

  // Chamada inicial: somente hoje
  carregarChamadasEfetuadas(1);

  // Clique nos botões de período
  botoesPeriodo.forEach(button => {
    button.addEventListener("click", function () {
      botoesPeriodo.forEach(btn => btn.classList.remove("active"));
      this.classList.add("active");

      const dias = this.getAttribute("data-dias"); // pode ser "7", "15" etc.
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

//Bloco que traz a relação de chamadas transferidas-->
  document.addEventListener("DOMContentLoaded", function () {

    // Chamada inicial para 7 dias (pode mudar para 1)
    atualizarChamadasTransferidas(1);

    // Atualiza ao clicar no botão de filtro de dias
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
