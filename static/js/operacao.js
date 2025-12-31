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
  fetch('/operacao/topGruposChamados', {
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
  fetch('/operacao/topClientesChamados', {
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

  fetch('/operacao/topStatusChamados', {
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

  fetch('/operacao/topTipoChamados', {
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
  fetch('/operacao/topCategoria', {
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

  fetch('/operacao/topSubCategoria', {
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