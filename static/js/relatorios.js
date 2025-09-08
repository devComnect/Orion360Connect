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
    