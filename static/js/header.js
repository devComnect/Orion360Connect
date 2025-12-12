const sidebar = document.getElementById("sidebar");
    const btn = document.getElementById("menuToggle");

    // Sidebar começa fechada
    document.body.classList.add("sidebar-collapsed");

    btn.addEventListener("click", () => {

        sidebar.classList.toggle("collapsed");

        if (sidebar.classList.contains("collapsed")) {
            document.body.classList.remove("sidebar-expanded");
            document.body.classList.add("sidebar-collapsed");
        } else {
            document.body.classList.remove("sidebar-collapsed");
            document.body.classList.add("sidebar-expanded");
        }
    });

    // Submenus
    document.querySelectorAll(".submenu-toggle").forEach(toggle => {
        toggle.addEventListener("click", function () {
            this.parentElement.classList.toggle("open");
        });
    });



    document.addEventListener('DOMContentLoaded', function () {

    async function carregarOperadores() {
        try {
            const response = await fetch('/insights/get/operadores');
            const data = await response.json();

            if (data.status === "success") {

                const lista = document.getElementById('submenu-operadores');
                lista.innerHTML = "";

                const operadoresOrdenados = data.operadores.sort((a, b) => a.localeCompare(b));

                operadoresOrdenados.forEach(operador => {

                    const li = document.createElement('li');

                    const a = document.createElement('a');
                    a.href = "#";
                    a.className = "operador-submenu-link d-flex align-items-center";
                    a.dataset.operador = operador;

                    const icon = document.createElement('i');
                    icon.className = "bi bi-person-fill me-2";

                    const name = document.createElement('span');
                    name.textContent = operador;

                    a.appendChild(icon);
                    a.appendChild(name);
                    li.appendChild(a);

                    a.onclick = function (e) {
                        e.preventDefault();

                        document.querySelectorAll('.operador-submenu-link')
                                .forEach(el => el.classList.remove('active'));

                        this.classList.add('active');

                        filtrarPorOperador(operador);
                    };

                    lista.appendChild(li);
                });
            }

        } catch (error) {
            console.error('Erro ao carregar operadores:', error);
        }
    }

    function filtrarPorOperador(operador) {
        const nomesNivel2 = ['Eduardo', 'Chrysthyanne', 'Fernando', 'Luciano', 'Maria Luiza'];

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


// Script para carregar grupos no submenu lateral
document.addEventListener('DOMContentLoaded', function () {

    async function carregarGrupos() {
        try {
            const response = await fetch('/insights/get/grupos');
            const data = await response.json();

            if (data.status === "success") {

                const lista = document.getElementById('submenu-grupos');
                lista.innerHTML = ""; // limpa antes

                const gruposOrdenados = data.grupos.sort((a, b) => a.localeCompare(b));

                gruposOrdenados.forEach(grupo => {

                    const li = document.createElement('li');

                    const a = document.createElement('a');
                    a.href = "#";
                    a.className = "grupo-submenu-link d-flex align-items-center";
                    a.dataset.grupo = grupo;

                    const icon = document.createElement('i');
                    icon.className = "bi bi-people-fill me-2";

                    const name = document.createElement('span');
                    name.textContent = grupo;

                    a.appendChild(icon);
                    a.appendChild(name);
                    li.appendChild(a);

                    a.onclick = function (e) {
                        e.preventDefault();

                        // remove active de todos
                        document.querySelectorAll('.grupo-submenu-link')
                            .forEach(el => el.classList.remove('active'));

                        this.classList.add('active');

                        sessionStorage.setItem('grupoSelecionado', grupo);

                        filtrarPorGrupo(grupo);
                    };

                    lista.appendChild(li);
                });

                // Marca o primeiro grupo como ativo automaticamente
                const primeiro = lista.querySelector('.grupo-submenu-link');
                if (primeiro) primeiro.classList.add('active');
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

    window.addEventListener("beforeunload", function () {
        sessionStorage.removeItem('grupoSelecionado');
    });
});
