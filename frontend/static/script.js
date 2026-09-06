// LOGIN

document.addEventListener("DOMContentLoaded", function () {

    const formularioLogin = document.getElementById("login-form");

    if (formularioLogin) {

        formularioLogin.addEventListener("submit", function (event) {

            event.preventDefault();

            login();

        });

    }

});

async function login() {

    const emailInput = document.getElementById("email");
    const senhaInput = document.getElementById("senha");
    const botaoLogin = document.getElementById("btn-login");

    const email = emailInput.value.trim();
    const senha = senhaInput.value;

    if (!email || !senha) {

        alert("Preencha todos os campos.");

        return;
    }

    botaoLogin.disabled = true;
    botaoLogin.textContent = "Entrando...";

    try {

        const response = await fetch("/login", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            credentials: "same-origin",

            body: JSON.stringify({
                email: email,
                senha: senha
            })

        });

        const data = await response.json();

        console.log("Resposta do servidor:", data);

        if (response.ok && data.status === "sucesso") {

            alert(data.msg);

            window.location.href = "/dashboard";

        } else {

            alert(data.msg || "Usuário ou senha incorretos.");

            botaoLogin.disabled = false;
            botaoLogin.textContent = "Entrar";
        }

    } catch (error) {

        console.error("Erro ao fazer login:", error);

        alert("Erro ao fazer login. Tente novamente.");

        botaoLogin.disabled = false;
        botaoLogin.textContent = "Entrar";
    }
}


// CADASTRO

async function cadastrar(event) {

    event.preventDefault();

    const nome = document.getElementById("nome").value.trim();
    const email = document.getElementById("email").value.trim();
    const senha = document.getElementById("senha").value;
    const ano_enem = document.getElementById("ano_enem").value;
    const confirmar = document.getElementById("confirmar-senha").value;
    const pergunta_secreta = document.getElementById("pergunta_secreta").value;
    const resposta_secreta = document.getElementById("resposta_secreta").value.trim();

    if (!nome || !email || !senha || !ano_enem || !pergunta_secreta || !resposta_secreta) {

        alert("Preencha todos os campos.");

        return;
    }

    if (senha !== confirmar) {

        alert("As senhas não conferem.");

        return;
    }

    if (senha.length < 5) {

        alert("A senha deve ter no mínimo 5 caracteres.");

        return;
    }

    try {

        const response = await fetch("/cadastrar", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            credentials: "same-origin",

            body: JSON.stringify({
                nome: nome,
                email: email,
                senha: senha,
                ano_enem: ano_enem,
                pergunta_secreta: pergunta_secreta,
                resposta_secreta: resposta_secreta
            })

        });

        const data = await response.json();

        console.log("Resposta do servidor:", data);

        if (response.ok && data.status === "sucesso") {

            alert(data.msg);

            window.location.href = "/login-page";

        } else {

            alert(data.msg || "Erro ao cadastrar.");

        }

    } catch (error) {

        console.error("Erro ao cadastrar:", error);

        alert("Erro ao cadastrar. Tente novamente.");
    }
}
