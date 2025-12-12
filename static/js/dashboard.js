

fetch('/dashboard/ChamadosSuporte/por_grupo_mes_atual')
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            const ctx = document.getElementById('GrupoAtendimentoChart').getContext('2d');
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.data.labels,
                    datasets: [{
                        label: "Chamados por Grupo",
                        data: data.data.datasets[0].data,
                        backgroundColor: data.data.datasets[0].backgroundColor
                    }]
                },
                options: {
                    plugins: {
                        legend: true,
                        title: {
                            display: true,
                            
                        },
                        legend: {
                            display: true,
                            position: 'right',
                            labels: {
                                generateLabels: function(chart) {
                                    const data = chart.data;
                                    if (data.labels.length && data.datasets.length) {
                                        const dataset = data.datasets[0];
                                        const total = dataset.data.reduce((a, b) => a + b, 0);

                                        return data.labels.map((label, i) => {
                                            const value = dataset.data[i];
                                            const percentage = total ? ((value / total) * 100).toFixed(1) : 0;
                                            return {
                                                text: `${label}: ${value} (${percentage}%)`,
                                                fillStyle: dataset.backgroundColor[i],
                                                strokeStyle: dataset.borderColor ? dataset.borderColor[i] : '',
                                                lineWidth: 0,
                                                hidden: isNaN(dataset.data[i]) || dataset.data[i] === null,
                                                index: i
                                            };
                                        });
                                    }
                                    return [];
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw;
                                    const total = context.chart._metasets[context.datasetIndex].total;
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    responsive: true
                }
            });
        } else {
            console.error("Erro ao carregar dados:", data.message);
        }
    })
    .catch(err => console.error("Erro de conexão:", err));



    document.addEventListener('DOMContentLoaded', function () {
        fetch('/dashboard/ChamadosSuporte/por_tipo_solicitacao_mes_atual', {
            method: 'POST'
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                const ctx = document.getElementById('TicketsCanalChart').getContext('2d');

                if (window.ticketsCanalChartInstance) {
                    window.ticketsCanalChartInstance.destroy();
                }

                // Altere aqui cada dataset para adicionar espessura personalizada
                data.data.datasets.forEach(ds => {
                    ds.barThickness = 15;              // Define a largura fixa da barra
                    ds.maxBarThickness = 40;           // Largura máxima (opcional)
                    ds.categoryPercentage = 0.8;       // Diminui o espaço entre as categorias
                    ds.barPercentage = 0.9;            // Aumenta o preenchimento dentro da categoria
                });

                window.ticketsCanalChartInstance = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.data.labels,
                        datasets: data.data.datasets
                    },
                    options: {
                        responsive: true,
                        interaction: {
                            mode: 'nearest',
                            intersect: true
                        },
                        plugins: {
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
                                title: {
                                    display: false,
                                    text: false,
                                    color: '#fff'
                                },
                                ticks: {
                                    color: '#fff'
                                },
                                grid: {
                                    color: 'rgba(255,255,255,0.1)'
                                }
                            },
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Quantidade de Chamados',
                                    color: '#fff'
                                },
                                ticks: {
                                    color: '#fff',
                                    precision: 0
                                },
                                grid: {
                                    color: 'rgba(255,255,255,0.1)'
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

                        if (idx === 1 && codigosCriticos.length > 0) {
                            codigos = codigosCriticos; // quase estourando
                        } 
                        else if (idx === 2 && codigosExpirados.length > 0) {
                            codigos = codigosExpirados; // expirado
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

    // Requisição SLA por grupo
    fetch('/dashboard/ChamadosSuporte/sla_andamento_grupos', { method: 'POST' })
        .then(res => res.json())
        .then(data => {

            if (data.status === "success") {

                // Atendimento
                criarSlaGrupoChart(
                    document.getElementById('slaGrupoChart').getContext('2d'),
                    'SLA - Atendimento',
                    data.sla1_nao_expirado,
                    data.sla1_quase_estourando || 0,
                    data.sla1_expirado,
                    data.codigos_sla1_critico || [],
                    data.codigos_sla1_expirado || []      // CORRIGIDO ✔
                );

                // Resolução
                criarSlaGrupoChart(
                    document.getElementById('slaGrupoChart2').getContext('2d'),
                    'SLA - Resolução',
                    data.sla2_nao_expirado,
                    data.sla2_quase_estourando || 0,
                    data.sla2_expirado,
                    data.codigos_sla2_critico || [],
                    data.codigos_sla2_expirado || []      // CORRIGIDO ✔
                );

            } else {
                console.error('Erro ao carregar dados de SLA por grupo:', data.message);
            }
        })
        .catch(e => console.error('Erro na requisição SLA por grupo:', e));
});


// Script que me traz os SLAs filtrados por grupo Suporte
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

                // 👇 AQUI CONTROLA O CLIQUE PARA ABRIR O MODAL
                onClick: (evt, elements) => {
                    if (elements.length > 0) {
                        const idx = elements[0].index;
                        let codigos = [];

                        if (idx === 1 && codigosCriticos.length > 0) { 
                            codigos = codigosCriticos;     // quase estourando
                        } 
                        else if (idx === 2 && codigosExpirados.length > 0) {  
                            codigos = codigosExpirados;    // expirado
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

    //  REQUISIÇÃO PARA BUSCAR DADOS
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


