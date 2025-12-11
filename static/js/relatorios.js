//Preencher operadores dinamicamente -->
    
    document.addEventListener('DOMContentLoaded', () => {
        fetch('/relatorios/getOperadores')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('operador');
                data.forEach(nome => {
                    const option = document.createElement('option');
                    option.value = nome;
                    option.textContent = nome;
                    select.appendChild(option);
                });
            })
            .catch(error => console.error('Erro ao carregar operadores:', error));
    });
    

//Bloco que traz os colaboradores para o card de controle de acesso-->
    
    document.addEventListener('DOMContentLoaded', () => {
        fetch('/relatorios/getColaboradores')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('operadorControle');
                data.forEach(nome => {
                    const option = document.createElement('option');
                    option.value = nome;
                    option.textContent = nome;
                    select.appendChild(option);
                });
            })
            .catch(error => console.error('Erro ao carregar operadores:', error));
    });
    

//Bloco que traz as leitoras-->
    
    document.addEventListener('DOMContentLoaded', () => {
    fetch('/relatorios/getLeitoras')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('leitorasSelect');
            data.forEach(leitor => {
                const option = document.createElement('option');
                option.value = leitor.id;
                option.textContent = leitor.name;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Erro ao carregar leitoras:', error));
});
    

// Gerar PDF Individual por colaborador -->
   
function gerarPDFIndividual() {
    const dataInicio = document.getElementById("data_inicio").value;
    const horaInicio = document.getElementById("hora_inicio").value;
    const dataFim = document.getElementById("data_final").value;
    const horaFim = document.getElementById("hora_final").value;
    const operador = document.getElementById("operador").value;

    if (!dataInicio || !horaInicio || !dataFim || !horaFim || !operador) {
        alert("Por favor, preencha todos os campos obrigatórios.");
        return;
    }

    const formData = new URLSearchParams();
    formData.append('data_inicio', dataInicio);
    formData.append('hora_inicio', horaInicio);
    formData.append('data_final', dataFim);
    formData.append('hora_final', horaFim);
    formData.append('operador', operador);

    fetch('/relatorios/extrairRelatorios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error("Erro ao gerar PDF");
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const operadorFormatado = operador.replace(/\s+/g, '_');
        const filename = `relatorio_${operadorFormatado}_${dataInicio}_a_${dataFim}.pdf`;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => {
        console.error("Erro ao gerar PDF:", error);
        alert("Falha ao gerar relatório em PDF.");
    });
}


// Gerar PDF Controle de Acesso -->

function gerarPDF() {
    const data = document.getElementById("data").value;
    const hora = document.getElementById("hora").value;
    const dataFinal = document.getElementById("dataFinalAcesso").value;
    const horaFinal = document.getElementById("horaFinalAcesso").value;
    const operadorControle = document.getElementById("operadorControle").value;
    const leitorasSelect = document.getElementById("leitorasSelect").value;

    // Validação de campos obrigatórios
    if (!data || !hora || !dataFinal || !horaFinal || !operadorControle || !leitorasSelect) {
        alert("Por favor, preencha todos os campos obrigatórios.");
        return;
    }

    const formData = new URLSearchParams();
    formData.append('data', data);  // data início
    formData.append('hora', hora);  // hora início
    formData.append('dataFinalAcesso', dataFinal);  // data fim
    formData.append('horaFinalAcesso', horaFinal);  // hora fim
    formData.append('operadorControle', operadorControle);
    formData.append('leitorasSelect', leitorasSelect);

    fetch('/relatorios/extrairControleAcesso', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error("Erro ao gerar PDF");
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        const operadorFormatado = operadorControle.replace(/\s+/g, '_');
        const filename = `relatorio_${operadorFormatado}_${data}_a_${dataFinal}.pdf`;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => {
        console.error("Erro ao gerar PDF:", error);
        alert("Falha ao gerar relatório em PDF.");
    });
}




 // Gerar PDF Comparativo-->
    
    function gerarComparativoPDF() {
        const data_inicio = document.getElementById("data_inicio_comp").value;
        const data_final = document.getElementById("data_final_comp").value;
        const hora_inicio = document.getElementById("hora_inicio_comp").value;
        const hora_final = document.getElementById("hora_final_comp").value;

        if (!data_inicio || !data_final || !hora_final || !hora_inicio) {
            alert("Por favor, preencha Data Início, Data Fim.");
            return;
        }

        const formData = new URLSearchParams();
        formData.append('data_inicio_comp', data_inicio);
        formData.append('data_final_comp', data_final);
        formData.append('hora_inicio_comp', hora_inicio);
        formData.append('hora_final_comp', hora_final);

        fetch('/relatorios/extrairComparativoRelatorios', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) throw new Error("Erro ao gerar PDF");
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const filename = `relatorio_comparativo_${new Date().toISOString().slice(0,10)}.pdf`;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(error => {
            console.error("Erro ao gerar PDF:", error);
            alert("Falha ao gerar relatório em PDF.");
        });
    }
    

    // Script que retorna os turnos

document.addEventListener('DOMContentLoaded', () => {
    fetch('/relatorios/getTurnos')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('turnos');

            data.forEach(turno => {
                const option = document.createElement('option');
                option.value = `${turno.tipo}_${turno.id}`;
                option.text = `${turno.tipo.charAt(0).toUpperCase() + turno.tipo.slice(1)}: ${turno.inicio} - ${turno.final}`;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Erro ao carregar turnos:', error));
});


// Script que gera o relatório de turnos

  async function gerarPDFTurnos() {
  const dataInicio = document.getElementById("data_inicio_turnos").value;
  const dataFim = document.getElementById("data_final_turnos").value;
  const turno = document.getElementById("turnos").value;

  if (!dataInicio || !dataFim || !turno) {
    alert("Por favor, preencha todos os campos obrigatórios.");
    return;
  }

  const formData = new FormData();
  formData.append("data_inicio_turnos", dataInicio);
  formData.append("data_final_turnos", dataFim);
  formData.append("turno", turno);

  try {
    const response = await fetch("/relatorios/extrairRelatorioTurnos", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      // tenta JSON, senão texto (HTML)
      let errMsg = "Erro ao gerar o PDF.";
      try {
        const erroJson = await response.json();
        errMsg = erroJson.message || JSON.stringify(erroJson);
      } catch (e) {
        // não é JSON -> pega texto (pode ser HTML)
        const text = await response.text();
        if (text && text.trim().startsWith("<")) {
          console.error("Resposta HTML do servidor:", text);
          errMsg = "Erro interno no servidor (verifique logs).";
        } else {
          errMsg = text || errMsg;
        }
      }
      alert(errMsg);
      return;
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;

    // tenta pegar filename do header Content-Disposition (opcional)
    const cd = response.headers.get("content-disposition");
    let filename = "relatorio_turno.pdf";
    if (cd) {
      const match = cd.match(/filename\*=UTF-8''(.+)|filename="(.+)"/);
      if (match) filename = decodeURIComponent(match[1] || match[2]);
    }

    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Erro ao gerar o relatório:", error);
    alert("Ocorreu um erro ao gerar o relatório. Veja o console para mais detalhes.");
  }
}

//Script que gera o relatório de satisfação 
function gerarSatisfacaoPDF() {

    const form = document.getElementById("formRelatorio3");
    const formData = new FormData(form);

    fetch("/relatorios/extrairSatisfacao", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Erro ao gerar o relatório.");
        }
        return response.blob();
    })
    .then(blob => {
        // Cria o download do PDF
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "relatorio_satisfacao.pdf";
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error("Erro:", error);
        alert("Erro ao gerar o PDF.");
    });
}

