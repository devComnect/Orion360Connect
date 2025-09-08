
document.addEventListener('DOMContentLoaded', () => {
  const abas = JSON.parse(document.getElementById('dados-json').textContent);
  const abasDiv = document.getElementById('abas');
  const planilhasDiv = document.getElementById('planilhas');
  const tabelas = {};
  let abaAtual = null;

  const feriados = ["01/01","25/01","17/02","03/04","21/04","01/05","04/06","09/07","07/09","12/10","02/11","15/11","20/11","25/12"];

  function gerarDiasDoMes(mesNome) {
    const meses = {'Janeiro':0,'Fevereiro':1,'Março':2,'Abril':3,'Maio':4,'Junho':5,'Julho':6,'Agosto':7,'Setembro':8,'Outubro':9,'Novembro':10,'Dezembro':11};
    const ano = new Date().getFullYear();
    const mes = meses[mesNome] ?? 0;
    const ultimoDia = new Date(ano, mes + 1, 0).getDate();
    const dias = [];
    for (let d=1; d<=ultimoDia; d++) dias.push(`${d.toString().padStart(2,'0')}/${(mes+1).toString().padStart(2,'0')}`);
    return dias;
  }

  abas.forEach(({nome, dados}, index) => {
    const dadosFiltrados = dados.slice(16); // se necessário
    const colunasOriginais = Object.keys(dadosFiltrados[0] || []);
    const primeiraColuna = colunasOriginais[0];
    const diasDoMes = gerarDiasDoMes(nome);

    const colunasOrdenadas = [primeiraColuna, ...diasDoMes];

    const dadosReestruturados = dadosFiltrados.map(linha => {
      const novaLinha = { [primeiraColuna]: linha[primeiraColuna] ?? '' };
      diasDoMes.forEach((dia, i) => {
        novaLinha[dia] = linha[colunasOriginais[i+1]] ?? ''; // substitui NaN/None por ''
      });
      return novaLinha;
    });

    // Botão da aba
    const btn = document.createElement('button');
    btn.textContent = nome;
    btn.classList.add('btn','btn-outline-primary','me-1','aba-btn');
    if(index===0){btn.classList.add('active'); abaAtual = nome;}
    btn.addEventListener('click',()=>{
      document.querySelectorAll('.aba-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      document.querySelectorAll('.planilha-container').forEach(div=>div.classList.remove('active'));
      document.getElementById(`planilha-${nome}`).classList.add('active');
      abaAtual = nome;
    });
    abasDiv.appendChild(btn);

    // Container da planilha
    const container = document.createElement('div');
    container.id = `planilha-${nome}`;
    container.classList.add('planilha-container','mt-3');
    if(index===0) container.classList.add('active');
    planilhasDiv.appendChild(container);

    const turnos = {
      'T1':'#d4edda','T2':'#a9dfbf','T3':'#7dcea0',
      'VA':'#f8d7da','SB':'#f5c6cb','DO':'#e2e3e5',
      'E1':'#d0e2f2','E2':'#a9cce3','E3':'#7fb3d5',
      'SÁB':'#4169E1', 'HB':'#FA8072', 'SD':'#F0E68C'
    };

    const colunas = colunasOrdenadas.map(campo=>({
      title: campo, field: campo, editor:"input", headerFilter:"input",
      formatter: (cell)=>{
        const valor = cell.getValue() ?? '';
        const cor = turnos[valor];
        if(cor){
          cell.getElement().style.backgroundColor = cor;
          cell.getElement().style.color = '#000';
          cell.getElement().style.fontWeight = 'bold';
        }
        if(feriados.includes(cell.getColumn().getField())){
          cell.getElement().style.backgroundColor = '#d6b3ff';
          cell.getElement().style.color = '#000';
          cell.getElement().style.fontWeight = 'bold';
        }
        return valor;
      }
    }));

    tabelas[nome] = new Tabulator(container,{
      data: dadosReestruturados,
      columns: colunas,
      layout:"fitColumns",
      movableColumns:true,
      pagination:"local",
      paginationSize:20,
      cellEdited:(cell)=>{
        console.log(`Editado na aba ${nome}: campo=${cell.getField()}, valor=${cell.getValue()}`, cell.getRow().getData());
      }
    });
  });

  // Download aba atual
  document.getElementById('download-btn').addEventListener('click',()=>{
    if(!abaAtual) return alert("Nenhuma aba selecionada.");
    const table = tabelas[abaAtual];
    const dados = table.getData();
    if(dados.length===0) return alert("A aba está vazia.");
    const ws = XLSX.utils.json_to_sheet(dados);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb,ws,abaAtual);
    XLSX.writeFile(wb,`escala_${abaAtual}.xlsx`);
  });

  // Download planilha original
  document.getElementById('download-original-btn').addEventListener('click',()=>{window.location.href='/escala/download_original';});

  // ✅ Importar planilha atualizada
  document.getElementById('upload-file').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const resp = await fetch("/escala/importar_escala", {
        method: "POST",
        body: formData
      });

      const resultado = await resp.json();
      if (resp.ok) {
        alert(resultado.mensagem);
        location.reload(); // recarrega página p/ usar nova planilha
      } else {
        alert("Erro: " + resultado.erro);
      }
    } catch (err) {
      alert("Falha na comunicação com o servidor.");
      console.error(err);
    }
  });

});

