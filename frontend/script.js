// LOGIN
function login() {
    var usuario = document.getElementById('email').value
    var senha = document.getElementById('senha').value

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            usuario: usuario,
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
    var usuario = document.getElementById('email').value
    var senha = document.getElementById('senha').value
    var confirmar = document.getElementById('confirmar-senha').value

    if (!usuario || !senha) {
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
            usuario: usuario,
            senha: senha
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
