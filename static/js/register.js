
//Bloco que realiza o cadastro do colaborador-->

document.addEventListener('DOMContentLoaded', function () {

  const form = document.getElementById('form-cadastro');

  form.addEventListener('submit', async function (e) {
    e.preventDefault();  // impede envio tradicional

    const nome = form.nome.value.trim();
    const username = form.username.value.trim();
    const email = form.email.value.trim();
    const senha = form.senha.value;
    const confirmarSenha = form['confirmar-senha'].value;
    const nivelAcesso = form['nivel-acesso'].value;

    // Validação simples de senha
    if (senha !== confirmarSenha) {
      alert('As senhas não coincidem!');
      return;
    }

    try {
      const response = await fetch('/setColaboradores', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          nome: nome,
          username: username,
          email: email,
          senha: senha,
          nivel_acesso: nivelAcesso
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        alert(data.message);
        form.reset();
      } else {
        alert(data.message || 'Erro desconhecido.');
      }
    } catch (error) {
      console.error('Erro ao enviar:', error);
      alert('Erro no servidor. Tente novamente mais tarde.');
    }
  });

});


//Bloco que realiza o delete do colaborador-->

document.addEventListener("DOMContentLoaded", function () {
  const formDelete = document.querySelector('form[action="/deletar_usuario"]');

  formDelete.addEventListener("submit", async function (e) {
    e.preventDefault();

    const emailUsernameInput = document.getElementById("del-email-username");
    const emailUsername = emailUsernameInput.value.trim();

    if (!emailUsername) {
      alert("Por favor, informe o e-mail ou username para exclusão.");
      return;
    }

    try {
      const response = await fetch("/deleteColaboradores", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "email-username": emailUsername
        })
      });

      const data = await response.json();

      if (data.status === "success") {
        alert(data.message);
        formDelete.reset();
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error("Erro ao excluir usuário:", error);
      alert("Erro no servidor. Tente novamente mais tarde.");
    }
  });
});


//Bloco que edita as informações do colaborador-->

document.addEventListener("DOMContentLoaded", function () {
  const formEdicao = document.getElementById("form-edicao");

  formEdicao.addEventListener("submit", async function (e) {
    e.preventDefault();

    const emailOriginal = document.getElementById("email-original").value;
    const nome = document.getElementById("edit-nome").value.trim();
    const username = document.getElementById("edit-username").value.trim();
    const email = document.getElementById("edit-email").value.trim();
    const senha = document.getElementById("edit-senha").value;
    const nivelAcesso = document.getElementById("edit-nivel-acesso").value;

    const payload = {
      email_original: emailOriginal,
      nome: nome,
      username: username,
      email: email,
      senha: senha,
      nivel_acesso: nivelAcesso
    };

    try {
      const response = await fetch("/updateColaboradores", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (data.status === "success") {
        alert(data.message);
        formEdicao.reset();
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error("Erro ao atualizar usuário:", error);
      alert("Erro no servidor. Tente novamente mais tarde.");
    }
  });
});


//Bloco que realiza a alteração de senha do colaborador-->

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const username = document.getElementById('edit-username-colaborador').value.trim();
      const senha = document.getElementById('edit-senha-colaborador').value.trim();

      if (!username || !senha) {
        alert('Por favor, preencha o username e a nova senha.');
        return;
      }

      try {
        const response = await fetch('/alterar_senha_colaborador', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ username, senha })
        });

        const contentType = response.headers.get('content-type');

        if (contentType && contentType.indexOf('application/json') !== -1) {
          const result = await response.json();

          if (response.ok) {
            alert(result.message || 'Senha atualizada com sucesso!');
            form.reset();
          } else {
            alert(result.error || 'Erro ao atualizar a senha.');
          }
        } else {
          const text = await response.text();
          alert('Erro inesperado (não JSON):\n' + text);
        }
      } catch (error) {
        alert('Erro na requisição: ' + error.message);
      }
    });
  });


// Bloco responsável por realizar a troca de senha 

document.addEventListener('DOMContentLoaded', () => {
      const form = document.getElementById('form-alterar-senha');

      form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('edit-username-colaborador').value.trim();
        const senha = document.getElementById('edit-senha-colaborador').value.trim();

        if (!username || !senha) {
          alert('Por favor, preencha o username e a nova senha.');
          return;
        }

        try {
          const response = await fetch('/alterar_senha_colaborador', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, senha })
          });

          const result = await response.json();

          if (response.ok) {
            alert(result.message || 'Senha atualizada com sucesso!');
            form.reset();
          } else {
            alert(result.error || 'Erro ao atualizar a senha.');
          }
        } catch (error) {
          alert('Erro na requisição: ' + error.message);
        }
      });
    });


// Script para cadastro de turnos
document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('formCadastrarTurno');

  form.addEventListener('submit', function (e) {
    e.preventDefault(); // impede envio padrão

    // Coletar os valores do formulário
    const turnoSelecionado = document.getElementById('list_turnos').value;
    const inicioTurno = document.getElementById('inicio_turno_cadastrar').value;
    const finalTurno = document.getElementById('final_turno_cadastrar').value;

    // Montar objeto JSON
    const dados = {
      list_turnos: turnoSelecionado,
      inicio_turno_cadastrar: inicioTurno,
      final_turno_cadastrar: finalTurno
    };

    // Enviar requisição POST para a API
    fetch('/register/registerTurnos', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        alert(data.message);
        form.reset(); // limpa o formulário
      } else {
        alert(' Erro ao cadastrar turno.');
      }
    })
    .catch(error => {
      console.error('Erro ao enviar dados:', error);
      alert(' Erro na comunicação com o servidor.');
    });
  });
});


// Script get list turnos editar
document.addEventListener('DOMContentLoaded', () => {
    fetch('/register/getListID') // chama a rota correta
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('idTurnos');

            data.forEach(turno => {
                const option = document.createElement('option');
                option.value = turno.id; // o valor enviado será só o ID
                option.textContent = `${turno.periodo}/ ID ${turno.id}`;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Erro ao carregar turnos:', error));
});

// Script get list turnos excluir
document.addEventListener('DOMContentLoaded', () => {
    fetch('/register/getListID') // chama a rota correta
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('idTurnosExcluir');

            data.forEach(turno => {
                const option = document.createElement('option');
                option.value = turno.id; // o valor enviado será só o ID
                option.textContent = `${turno.periodo}/ ID ${turno.id}`;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Erro ao carregar turnos:', error));
});



// Script para editar turnos
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("formEditTurno");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    // Pega os valores do form
    const data = {
      id_turno_editar: document.getElementById("idTurnos").value,
      list_turnos_editar: document.getElementById("list_turnos").value,
      inicio_turno_editar: document.getElementById("inicio_turno_editar").value,
      final_turno_editar: document.getElementById("final_turno_editar").value
    };

    try {
      const response = await fetch("/register/editTurnos", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (result.status === "success") {
        alert(result.message);
      } else {
        alert(result.message);
      }
    } catch (error) {
      console.error("Erro na requisição:", error);
      alert(" Erro ao atualizar turno. Verifique o console.");
    }
  });
});


// Script que deleta os turnos
document.addEventListener("DOMContentLoaded", function () {
  const formDelete = document.querySelector("form[action='']"); // ou usa id se preferir

  formDelete.addEventListener("submit", async function (e) {
    e.preventDefault();

    const data = {
      id_turno_exclusao: document.getElementById("idTurnosExcluir").value
    };

    if (!data.id_turno_exclusao) {
      alert("Selecione um turno para excluir.");
      return;
    }

    if (!confirm("Tem certeza que deseja excluir este turno?")) {
      return;
    }

    try {
      const response = await fetch("/register/deleteTurnos", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();

      if (result.status === "success") {
        alert(result.message);
        // Exemplo: remover o turno excluído da lista
        const option = document.querySelector(`#idTurnosExcluir option[value='${data.id_turno_exclusao}']`);
        if (option) option.remove();
      } else {
        alert(result.message);
      }
    } catch (error) {
      console.error("Erro na requisição:", error);
      alert("Erro ao excluir turno. Verifique o console.");
    }
  });
});


