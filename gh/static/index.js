function mostrarCamposExtras() {
    let maisFilhosSim = document.getElementById("mais_filhos_sim").checked;
    let quantidadeFilhosDiv = document.getElementById("quantidade_filhos_div");
    
    if (maisFilhosSim) {
        quantidadeFilhosDiv.style.display = "block";
    } else {
        quantidadeFilhosDiv.style.display = "none";
        document.getElementById("mesma_sala_div").style.display = "none";
        document.getElementById("filhos_info").innerHTML = "";
    }
}

function mostrarPerguntaMesmaSala() {
    let quantidade = document.getElementById("quantidade_filhos").value;
    let mesmaSalaDiv = document.getElementById("mesma_sala_div");
    
    if (quantidade >= 1) {
        mesmaSalaDiv.style.display = "block";
    } else {
        mesmaSalaDiv.style.display = "none";
        document.getElementById("filhos_info").innerHTML = "";
    }
}

function gerarCamposFilhos() {
    let quantidade = document.getElementById("quantidade_filhos").value;
    let mesmaSala = document.querySelector('input[name="mesma_sala"]:checked')?.value;
    let filhosInfoDiv = document.getElementById("filhos_info");
    
    filhosInfoDiv.innerHTML = "";

    if (mesmaSala === "sim" && quantidade > 0) {
        for (let i = 1; i <= quantidade; i++) {
            filhosInfoDiv.innerHTML += `
                <label style="margin-top: 10px;" for="nome_filho_${i}">Nome do Filho ${i}:</label>
                <input type="text" id="nome_filho_${i}" name="nome_filho_${i}" required><br>
                <label for="idade_filho_${i}">Idade do Filho ${i}:</label>
                <input type="number" id="idade_filho_${i}" name="idade_filho_${i}" required><br>
            `;
        }
    }
}

function toggleMenu() {
    let menu = document.getElementById("dropdown-menu");
    menu.style.display = menu.style.display === "block" ? "none" : "block";
}

document.addEventListener("DOMContentLoaded", function () {
    const inputFoto = document.getElementById('foto');
    const preview = document.getElementById('preview');
    const modal = document.getElementById("modal");
    const imagemGrande = document.getElementById("imagem-grande");

    inputFoto.addEventListener("change", function () {
        if (inputFoto.files && inputFoto.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function (e) {
                preview.src = e.target.result;
                preview.style.display = 'block'; // Mostra a imagem após o upload
                preview.setAttribute("data-loaded", "true"); // Marca que a imagem foi carregada
            };

            reader.readAsDataURL(inputFoto.files[0]);
        } else {
            preview.src = "";
            preview.style.display = "none"; // Esconde o preview caso remova a imagem
            preview.removeAttribute("data-loaded");
        }
    });

    // Quando clicar na imagem, exibir em tela cheia
    preview.addEventListener("click", function () {
        if (preview.getAttribute("data-loaded") === "true") {
            imagemGrande.src = preview.src;
            modal.style.display = "flex";
        }
    });

    // Fechar o modal ao clicar nele
    modal.addEventListener("click", function () {
        this.style.display = "none";
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const flashMessages = document.getElementById("flash-messages");
    if (flashMessages) {
        setTimeout(() => {
            flashMessages.classList.add("fade-out");
            setTimeout(() => flashMessages.remove(), 1000);
        }, 1500); // Agora a mensagem some após 5 segundos
    }
});

