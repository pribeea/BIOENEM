// LOGIN
function login() {
    var email = document.getElementById('email').value;
    var senha = document.getElementById('senha').value;

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: email,
            senha: senha
        })
    })
    .then(res => res.json())
    .then(data => {

        if (data.msg == "Usuário logado") {
            alert("Bem-vindo")
        } else {
            alert(data.msg)
        }

    })
}

// CADASTRO
function cadastrar() {
    var nome = document.getElementById('nome').value;
    var email = document.getElementById('email').value;
    var senha = document.getElementById('senha').value;
    var ano_enem = document.getElementById('ano_enem').value;
    var confirmar = document.getElementById('confirmar-senha').value;

    if (!nome || !email || !senha || !ano_enem) {
        alert("Preencha todos os campos")
        return
    }

    if (senha != confirmar) {
        alert("As senhas não conferem")
        return
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
    .then(res => res.json())
    .then(data => {

        if (data.msg == "Cadastro realizado") {
            alert("Cadastro feito com sucesso!")
            window.location.href = "/"
        } else {
            alert(data.msg)
        }

    })
}
