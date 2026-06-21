// LOGIN
function login() {
    var email = document.getElementById('email').value;
    var senha = document.getElementById('senha').value;

    if (!email || !senha) {
        alert("Preencha todos os campos");
        return;
    }

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: email,
            senha: senha
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Resposta do servidor:", data); // Para debug
        
        if (data.status === 'sucesso') {
            alert(data.msg);
            // Redireciona para o dashboard
            window.location.href = "/dashboard";
        } else {
            alert(data.msg);
        }
    })
    .catch(error => {
        console.error("Erro:", error);
        alert("Erro ao fazer login. Tente novamente.");
    });
}

// CADASTRO
function cadastrar() {
    var nome = document.getElementById('nome').value;
    var email = document.getElementById('email').value;
    var senha = document.getElementById('senha').value;
    var ano_enem = document.getElementById('ano_enem').value;
    var confirmar = document.getElementById('confirmar-senha').value;

    if (!nome || !email || !senha || !ano_enem) {
        alert("Preencha todos os campos");
        return;
    }

    if (senha != confirmar) {
        alert("As senhas não conferem");
        return;
    }

    if (senha.length < 5) {
        alert("A senha deve ter no mínimo 5 caracteres");
        return;
    }

    fetch('/cadastrar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            nome: nome,      
            email: email,  
            senha: senha,
            ano_enem: ano_enem
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Resposta do servidor:", data); // Para debug
        
        if (data.status === 'sucesso') {
            alert(data.msg);
            // Redireciona para a página de login
            window.location.href = "/login-page";
        } else {
            alert(data.msg);
        }
    })
    .catch(error => {
        console.error("Erro:", error);
        alert("Erro ao cadastrar. Tente novamente.");
    });
}
