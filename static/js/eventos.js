// Script que registra o evento
function registrarEventoFalha() {
    const form = document.getElementById("formEventosFalha");
    const formData = new FormData(form);

    fetch("/eventos/eventos-falha/registrar", {
        method: "POST",
        body: formData
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            alert("Erro: " + data.error);
        } else {
            alert("Evento registrado com sucesso!");
            form.reset();
        }
    })
    .catch(err => alert("Erro inesperado: " + err));
}


// Script que traz os eventos registrados
document.addEventListener("DOMContentLoaded", function () {
    fetch("/eventos/eventos-falha/listar")
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById("eventos_registrados");
            select.innerHTML = "";

            data.forEach(ev => {
                const opt = document.createElement("option");
                opt.value = ev.id;
                opt.textContent = `ID: ${ev.id} - ${ev.texto} — SLA: ${ev.sla}`;
                select.appendChild(opt);
            });
        })
        .catch(err => {
            console.error("Erro ao carregar eventos:", err);
        });
});


// Excluir evento
function limparEvento() {
    const select = document.getElementById("eventos_registrados");
    const selecionados = Array.from(select.selectedOptions).map(opt => opt.value);

    if (selecionados.length === 0) {
        alert("Selecione ao menos um evento para limpar.");
        return;
    }

    if (!confirm("Deseja realmente limpar o(s) evento(s) selecionado(s)?")) return;

    fetch("/eventos/eventos-falha/limpar", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ ids: selecionados })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            alert("Erro: " + data.error);
        } else {
            alert("Evento(s) limpo(s) com sucesso!");

            // Remove visualmente os eventos da lista
            selecionados.forEach(id => {
                const opt = select.querySelector(`option[value="${id}"]`);
                if (opt) opt.remove();
            });
        }
    })
    .catch(err => alert("Erro inesperado: " + err));
}
