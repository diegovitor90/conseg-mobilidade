"use strict";

// A previsão é apenas feedback. O model calcula e valida ao salvar.
document.addEventListener("DOMContentLoaded", () => {
    const menu = document.getElementById("menu-lateral");
    const overlay = document.getElementById("menu-overlay");
    const abrirMenu = document.getElementById("abrir-menu");
    const fecharMenu = document.getElementById("fechar-menu");
    const alternarMenu = (aberto) => {
        if (!menu || !overlay || !abrirMenu) return;
        menu.classList.toggle("translate-x-0", aberto);
        menu.classList.toggle("-translate-x-full", !aberto);
        overlay.classList.toggle("hidden", !aberto);
        abrirMenu.setAttribute("aria-expanded", String(aberto));
        document.body.classList.toggle("overflow-hidden", aberto);
    };
    abrirMenu?.addEventListener("click", () => alternarMenu(true));
    fecharMenu?.addEventListener("click", () => alternarMenu(false));
    overlay?.addEventListener("click", () => alternarMenu(false));
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") alternarMenu(false);
    });

    const categoria = document.getElementById("id_categoria");
    const saida = document.getElementById("capacidade-prevista");
    const dados = document.getElementById("capacidades");
    if (categoria && saida && dados) {
        const capacidades = JSON.parse(dados.textContent);
        const atualizar = () => {
            const valor = capacidades[categoria.value];
            saida.textContent = valor ? `${valor} passageiros` : "Selecione uma categoria";
        };
        categoria.addEventListener("change", atualizar);
        atualizar();
    }
});
