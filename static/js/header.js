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