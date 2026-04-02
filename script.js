const API_BASE = "http://localhost:5000";
let allItems = [];
let currentFilters = {
    tipo: '',
    status: ''
};

// Elementos principais
const elements = {
    form: document.getElementById('item-form'),
    editForm: document.getElementById('edit-form'),
    itemsList: document.getElementById('items-list'),
    loading: document.getElementById('loading'),
    emptyState: document.getElementById('empty-state'),
    itemsContainer: document.getElementById('items-container'),
    modal: document.getElementById('edit-modal'),
    stats: {
        total: document.getElementById('total-items'),
        available: document.getElementById('available-items'),
        unavailable: document.getElementById('unavailable-items')
    }
};

// Mostrar mensagem simples
function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    // Adicionar no topo
    document.querySelector('.container').prepend(alert);
    
    // Remover após 3 segundos
    setTimeout(() => {
        alert.remove();
    }, 3000);
}

// Carregar itens
async function loadItems() {
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE}/items`);
        if (!response.ok) throw new Error('Erro na requisição');
        
        allItems = await response.json();
        
        updateStats();
        applyFilters();
        
    } catch (error) {
        console.error('Erro:', error);
        showAlert('Erro ao carregar itens. Verifique se o servidor está rodando.', 'error');
    } finally {
        showLoading(false);
    }
}

// Mostrar/ocultar loading
function showLoading(show) {
    if (show) {
        elements.loading.style.display = 'block';
        elements.emptyState.style.display = 'none';
        elements.itemsContainer.style.display = 'none';
    } else {
        elements.loading.style.display = 'none';
    }
}

// Atualizar estatísticas
function updateStats() {
    elements.stats.total.textContent = allItems.length;
    elements.stats.available.textContent = allItems.filter(item => item.status === 'disponivel').length;
    elements.stats.unavailable.textContent = allItems.filter(item => item.status === 'indisponivel').length;
}

// Aplicar filtros
function applyFilters() {
    const tipoFilter = document.getElementById('filter-tipo').value;
    const statusFilter = document.getElementById('filter-status').value;
    
    let filteredItems = [...allItems];
    
    if (tipoFilter) {
        filteredItems = filteredItems.filter(item => item.tipo === tipoFilter);
    }
    
    if (statusFilter) {
        filteredItems = filteredItems.filter(item => item.status === statusFilter);
    }
    
    renderItems(filteredItems);
}

// Limpar filtros
function clearFilters() {
    document.getElementById('filter-tipo').value = '';
    document.getElementById('filter-status').value = '';
    applyFilters();
}

// Renderizar itens na tabela
function renderItems(items) {
    if (items.length === 0) {
        elements.emptyState.style.display = 'block';
        elements.itemsContainer.style.display = 'none';
        return;
    }
    
    elements.emptyState.style.display = 'none';
    elements.itemsContainer.style.display = 'block';
    
    const tbody = elements.itemsList;
    tbody.innerHTML = '';
    
    items.forEach(item => {
        const row = document.createElement('tr');
        
        // Formatar a quantidade (se status for indisponível, mostrar 0)
        let quantidade;
        let quantidadeTexto;
        
        if (item.status === 'indisponivel') {
            quantidade = 0;
            quantidadeTexto = '<span style="color: #e74c3c; font-weight: bold;">0 cópia</span>';
        } else {
            quantidade = item.quantidade || 1;
            quantidadeTexto = `${quantidade} cópia${quantidade > 1 ? 's' : ''}`;
        }
        
        row.innerHTML = `
            <td>
                <strong>${item.titulo}</strong>
                ${item.descricao ? `<br><small>${item.descricao}</small>` : ''}
            </td>
            <td><span class="badge badge-type">${item.tipo}</span></td>
            <td>
                <span class="badge ${item.status === 'disponivel' ? 'badge-available' : 'badge-unavailable'}">
                    ${item.status === 'disponivel' ? 'Disponível' : 'Indisponível'}
                </span>
            </td>
            <td>${quantidadeTexto}</td>
            <td>
                <div class="actions">
                    <button class="btn btn-primary" onclick="editItem(${item.id})">
                        Editar
                    </button>
                    <button class="btn btn-danger" onclick="deleteItem(${item.id})">
                        Excluir
                    </button>
                </div>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Função para atualizar quantidade baseada no status
function updateQuantidadeByStatus() {
    const status = document.getElementById('status').value;
    const quantidadeInput = document.getElementById('quantidade');
    
    if (status === 'indisponivel') {
        quantidadeInput.value = '0';
        quantidadeInput.disabled = true;
        quantidadeInput.style.opacity = '0.6';
        quantidadeInput.style.backgroundColor = '#f8d7da';
    } else {
        quantidadeInput.disabled = false;
        quantidadeInput.style.opacity = '1';
        quantidadeInput.style.backgroundColor = '';
        
        // Se estiver em 0, mudar para 1 quando voltar para disponível
        if (quantidadeInput.value === '0') {
            quantidadeInput.value = '1';
        }
    }
}

// Função para atualizar quantidade no modal de edição
function updateQuantidadeModalByStatus() {
    const status = document.getElementById('edit-status').value;
    const quantidadeInput = document.getElementById('edit-quantidade');
    
    if (status === 'indisponivel') {
        quantidadeInput.value = '0';
        quantidadeInput.disabled = true;
        quantidadeInput.style.opacity = '0.6';
        quantidadeInput.style.backgroundColor = '#f8d7da';
    } else {
        quantidadeInput.disabled = false;
        quantidadeInput.style.opacity = '1';
        quantidadeInput.style.backgroundColor = '';
        
        // Se estiver em 0, mudar para 1 quando voltar para disponível
        if (quantidadeInput.value === '0') {
            quantidadeInput.value = '1';
        }
    }
}

// Cadastrar novo item
elements.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const titulo = document.getElementById('titulo').value.trim();
    const tipo = document.getElementById('tipo').value;
    const status = document.getElementById('status').value;
    const quantidade = document.getElementById('quantidade').value;
    const data = document.getElementById('data').value;
    const descricao = document.getElementById('descricao').value.trim();
    
    // Validação
    if (titulo.length < 3) {
        showAlert('Título deve ter no mínimo 3 caracteres', 'error');
        return;
    }
    
    if (!tipo || !status) {
        showAlert('Preencha todos os campos obrigatórios', 'error');
        return;
    }
    
    // Validar quantidade
    if (quantidade && parseInt(quantidade) < 0) {
        showAlert('Quantidade não pode ser negativa', 'error');
        return;
    }
    
    const novoItem = { titulo, tipo, status };
    
    // Adicionar campos opcionais
    if (descricao) novoItem.descricao = descricao;
    if (data) novoItem.data = data;
    
    // Quantidade: se status for indisponível, sempre 0
    if (status === 'indisponivel') {
        novoItem.quantidade = 0;
    } else if (quantidade) {
        novoItem.quantidade = parseInt(quantidade);
    }
    
    try {
        const response = await fetch(`${API_BASE}/items`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(novoItem)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Erro ao cadastrar');
        }
        
        showAlert('Item cadastrado com sucesso!', 'success');
        elements.form.reset();
        // Resetar quantidade para 1 e habilitar campo
        document.getElementById('quantidade').value = '1';
        document.getElementById('quantidade').disabled = false;
        document.getElementById('quantidade').style.opacity = '1';
        document.getElementById('quantidade').style.backgroundColor = '';
        loadItems();
        
    } catch (error) {
        showAlert(error.message, 'error');
    }
});

// Editar item
async function editItem(id) {
    try {
        const item = allItems.find(i => i.id === id);
        if (!item) {
            showAlert('Item não encontrado', 'error');
            return;
        }
        
        // Preencher formulário de edição
        document.getElementById('edit-id').value = id;
        document.getElementById('edit-titulo').value = item.titulo;
        document.getElementById('edit-tipo').value = item.tipo;
        document.getElementById('edit-status').value = item.status;
        document.getElementById('edit-descricao').value = item.descricao || '';
        
        // Quantidade: se status for indisponível, mostrar 0 e desabilitar
        if (item.status === 'indisponivel') {
            document.getElementById('edit-quantidade').value = '0';
            document.getElementById('edit-quantidade').disabled = true;
            document.getElementById('edit-quantidade').style.opacity = '0.6';
            document.getElementById('edit-quantidade').style.backgroundColor = '#f8d7da';
        } else {
            document.getElementById('edit-quantidade').value = item.quantidade || '';
            document.getElementById('edit-quantidade').disabled = false;
            document.getElementById('edit-quantidade').style.opacity = '1';
            document.getElementById('edit-quantidade').style.backgroundColor = '';
        }
        
        // Adicionar listener para mudança de status no modal
        document.getElementById('edit-status').addEventListener('change', updateQuantidadeModalByStatus);
        
        // Mostrar modal
        elements.modal.style.display = 'flex';
        
    } catch (error) {
        console.error('Erro:', error);
        showAlert('Erro ao carregar item para edição', 'error');
    }
}

// Salvar edição
elements.editForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const id = document.getElementById('edit-id').value;
    const titulo = document.getElementById('edit-titulo').value.trim();
    const tipo = document.getElementById('edit-tipo').value;
    const status = document.getElementById('edit-status').value;
    const quantidade = document.getElementById('edit-quantidade').value;
    const descricao = document.getElementById('edit-descricao').value.trim();
    
    if (titulo.length < 3) {
        showAlert('Título deve ter no mínimo 3 caracteres', 'error');
        return;
    }
    
    // Validar quantidade (apenas se status for disponível)
    if (status === 'disponivel' && quantidade && parseInt(quantidade) < 0) {
        showAlert('Quantidade não pode ser negativa', 'error');
        return;
    }
    
    const updatedItem = { titulo, tipo, status };
    
    // Adicionar campos opcionais
    if (descricao) updatedItem.descricao = descricao;
    
    // Quantidade: se status for indisponível, sempre 0
   if (status === 'indisponivel') {
        updatedItem.quantidade = 0;
    } else if (quantidade !== "") {
        updatedItem.quantidade = parseInt(quantidade);
    }
        
    try {
        const response = await fetch(`${API_BASE}/items/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedItem)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Erro ao atualizar');
        }
        
        showAlert('Item atualizado com sucesso!', 'success');
        closeModal();
        loadItems();
        
    } catch (error) {
        showAlert(error.message, 'error');
    }
});

// Excluir item
async function deleteItem(id) {
    if (!confirm('Tem certeza que deseja excluir este item?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/items/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Erro ao excluir item');
        }
        
        showAlert('Item excluído com sucesso!', 'success');
        loadItems();
        
    } catch (error) {
        showAlert('Erro ao excluir item', 'error');
    }
}

// Fechar modal
function closeModal() {
    elements.modal.style.display = 'none';
    elements.editForm.reset();
    
    // Remover listener do status no modal
    const editStatus = document.getElementById('edit-status');
    const newEditStatus = editStatus.cloneNode(true);
    editStatus.parentNode.replaceChild(newEditStatus, editStatus);
}

// Resetar formulário
function resetForm() {
    elements.form.reset();
    // Resetar quantidade para 1 e habilitar campo
    document.getElementById('quantidade').value = '1';
    document.getElementById('quantidade').disabled = false;
    document.getElementById('quantidade').style.opacity = '1';
    document.getElementById('quantidade').style.backgroundColor = '';
    showAlert('Formulário limpo', 'info');
}

// Fechar modal ao clicar fora
window.onclick = function(event) {
    if (event.target === elements.modal) {
        closeModal();
    }
};

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    loadItems();
    
    // Adicionar listener para mudança de status no formulário principal
    document.getElementById('status').addEventListener('change', updateQuantidadeByStatus);
    
    // Verificar status inicial
    updateQuantidadeByStatus();
});
