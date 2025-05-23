$(document).ready(function() {
    // Variáveis globais
    let intervalId = null;
    let modoAutomatico = false;
    let simulacaoEmAndamento = true;
    
    // Função para atualizar o status
    function atualizarStatus() {
        $.get('/api/status/', function(response) {
            if (response.status === 'success') {
                // Atualizar contador de senhas
                $('#total-fila').text(response.total_aguardando);
                $('#total-atendidas').text(response.simulacao.senhas_atendidas);
                $('#total-desistencias').text(response.simulacao.desistencias);
                
                // Atualizar próximas senhas
                $('#proximas-senhas').empty();
                if (response.proximas_senhas.length > 0) {
                    response.proximas_senhas.forEach(function(senha, index) {
                        const tipoClasse = senha.tipo === 'N' ? 'senha-normal' : 'senha-prioritaria';
                        const tipoTexto = senha.tipo === 'N' ? 'Normal' : 'Prioritária';
                        $('#proximas-senhas').append(
                            `<div class="senha ${tipoClasse}">${senha.tipo}${senha.numero} <span class="ms-1">${index === 0 ? '(Próxima)' : ''}</span></div>`
                        );
                    });
                } else {
                    $('#proximas-senhas').html('<p>Nenhuma senha na fila</p>');
                }
                
                // Atualizar próximo posto
                $('#proximo-posto').text(response.proximo_posto || 'Nenhum disponível');
                
                // Atualizar postos
                $('#postos').empty();
                response.postos.forEach(function(posto) {
                    const ativoClasse = posto.ativo ? 'ativo' : 'inativo';
                    const ocupadoClasse = posto.ocupado ? 'ocupado' : 'livre';
                    
                    let statusClass = '';
                    let statusText = '';
                    
                    if (!posto.ativo) {
                        statusClass = 'inativo';
                        statusText = 'Inativo';
                    } else if (posto.ocupado) {
                        statusClass = 'ocupado';
                        statusText = `Ocupado (Senha: ${posto.senha_atual})`;
                    } else {
                        statusClass = 'livre';
                        statusText = 'Livre';
                    }
                    
                    const btnAlternar = posto.numero > 3 ? 
                        `<button class="btn btn-sm ${posto.ativo ? 'btn-danger' : 'btn-success'} btn-alternar" data-posto-id="${posto.id}">
                            <i class="fas ${posto.ativo ? 'fa-toggle-off' : 'fa-toggle-on'}"></i> ${posto.ativo ? 'Desativar' : 'Ativar'}
                        </button>` : '';
                    
                    const btnFinalizar = posto.ocupado ? 
                        `<button class="btn btn-sm btn-primary btn-finalizar" data-posto-id="${posto.id}">
                            <i class="fas fa-check-circle"></i> Finalizar
                        </button>` : '';
                    
                    $('#postos').append(`
                        <div class="posto ${ativoClasse} ${ocupadoClasse}">
                            <h5>Posto ${posto.numero}</h5>
                            <div class="posto-status ${statusClass}">${statusText}</div>
                            <div class="d-flex justify-content-around mt-2">${btnAlternar} ${btnFinalizar}</div>
                        </div>
                    `);
                });
            }
        });
    }
    
    // Inicializar o sistema
    function inicializarSistema() {
        atualizarStatus();
        // Atualizar a cada 2 segundos
        intervalId = setInterval(atualizarStatus, 2000);
    }
    
    // Gerar senha normal
    $('#btn-gerar-normal').click(function() {
        $.post('/api/gerar-senha/', { tipo: 'N' }, function(response) {
            if (response.status === 'success') {
                exibirAlerta(`Senha ${response.senha} gerada com sucesso!`, 'success');
                atualizarStatus();
            }
        });
    });
    
    // Gerar senha prioritária
    $('#btn-gerar-prioritaria').click(function() {
        $.post('/api/gerar-senha/', { tipo: 'P' }, function(response) {
            if (response.status === 'success') {
                exibirAlerta(`Senha ${response.senha} gerada com sucesso!`, 'success');
                atualizarStatus();
            }
        });
    });
    
    // Chamar próxima senha
    $('#btn-chamar-proxima').click(function() {
        $.post('/api/chamar-proxima/', function(response) {
            if (response.status === 'success') {
                exibirAlerta(`Senha ${response.senha} chamada para o posto ${response.posto}`, 'info');
                atualizarStatus();
            } else {
                exibirAlerta(response.message, 'warning');
            }
        });
    });
    
    // Simular desistência
    $('#btn-simular-desistencia').click(function() {
        $.post('/api/simular-desistencia/', function(response) {
            if (response.status === 'success') {
                exibirAlerta(`Senha ${response.senha} desistiu do atendimento`, 'danger');
                atualizarStatus();
            } else {
                exibirAlerta(response.message, 'warning');
            }
        });
    });
    
    // Finalizar atendimento
    $(document).on('click', '.btn-finalizar', function() {
        const postoId = $(this).data('posto-id');
        $.post('/api/finalizar-atendimento/', { posto_id: postoId }, function(response) {
            if (response.status === 'success') {
                exibirAlerta(`Atendimento finalizado no posto ${response.posto}`, 'success');
                atualizarStatus();
            } else {
                exibirAlerta(response.message, 'warning');
            }
        });
    });
    
    // Alternar posto
    $(document).on('click', '.btn-alternar', function() {
        const postoId = $(this).data('posto-id');
        $.post('/api/alternar-posto/', { posto_id: postoId }, function(response) {
            if (response.status === 'success') {
                const statusText = response.ativo ? 'ativado' : 'desativado';
                exibirAlerta(`Posto ${response.posto} ${statusText} com sucesso!`, 'info');
                atualizarStatus();
            } else {
                exibirAlerta(response.message, 'warning');
            }
        });
    });
    
    // Encerrar simulação
    $('#btn-encerrar').click(function() {
        if (!confirm('Deseja realmente encerrar a simulação?')) {
            return;
        }
        
        $.post('/api/encerrar-simulacao/', function(response) {
            if (response.status === 'success') {
                clearInterval(intervalId);
                simulacaoEmAndamento = false;
                
                // Desativar modo automático
                $('#modo-automatico').prop('checked', false);
                modoAutomatico = false;
                
                // Exibir resultados
                $('#lista-senhas-atendidas').empty();
                if (response.senhas_atendidas.length > 0) {
                    response.senhas_atendidas.forEach(function(senha) {
                        const tipoClasse = senha.charAt(0) === 'N' ? 'senha-normal' : 'senha-prioritaria';
                        $('#lista-senhas-atendidas').append(
                            `<span class="senha ${tipoClasse}">${senha}</span> `
                        );
                    });
                } else {
                    $('#lista-senhas-atendidas').html('<p>Nenhuma senha foi atendida</p>');
                }
                
                $('#resultado-total-atendidas').text(response.total_atendidas);
                $('#resultado-total-desistencias').text(response.total_desistencias);
                
                // Esconder a simulação e mostrar os resultados
                $('.dashboard, #postos, .controles, #modo-automatico-container').hide();
                $('#resultados').fadeIn();
            } else {
                exibirAlerta(response.message, 'warning');
            }
        });
    });
    
    // Iniciar nova simulação
    $('#btn-nova-simulacao').click(function() {
        location.reload();
    });
    
    // Modo automático
    $('#modo-automatico').change(function() {
        modoAutomatico = $(this).is(':checked');
        
        if (modoAutomatico) {
            exibirAlerta('Modo automático ativado! A simulação funcionará sozinha.', 'info');
            executarSimulacaoAutomatica();
        } else {
            exibirAlerta('Modo automático desativado! Você precisa controlar manualmente.', 'info');
        }
    });
    
    // Função para exibir alertas temporários
    function exibirAlerta(mensagem, tipo) {
        // Remover alertas existentes
        $('.alert-floating').remove();
        
        // Criar novo alerta
        const alerta = `
            <div class="alert alert-${tipo} alert-dismissible fade show alert-floating" role="alert">
                ${mensagem}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
            </div>
        `;
        
        // Adicionar ao corpo do documento
        $('body').append(alerta);
        
        // Posicionar o alerta
        $('.alert-floating').css({
            'position': 'fixed',
            'top': '20px',
            'right': '20px',
            'z-index': '9999',
            'min-width': '300px',
            'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.2)'
        });
        
        // Auto-fechar após 3 segundos
        setTimeout(function() {
            $('.alert-floating').alert('close');
        }, 3000);
    }
    
    // Simulação automática
    function executarSimulacaoAutomatica() {
        if (!modoAutomatico || !simulacaoEmAndamento) {
            return;
        }
        
        // Gerar senhas aleatórias periodicamente
        setTimeout(function() {
            if (modoAutomatico && simulacaoEmAndamento) {
                const tipo = Math.random() > 0.7 ? 'P' : 'N'; // 30% de chance de ser prioritária
                $.post('/api/gerar-senha/', { tipo: tipo });
                executarGeracaoAutomatica();
            }
        }, Math.random() * 3000 + 2000); // Entre 2 e 5 segundos
        
        // Chamar próxima senha periodicamente
        setTimeout(function() {
            if (modoAutomatico && simulacaoEmAndamento) {
                $.post('/api/chamar-proxima/');
                executarChamadaAutomatica();
            }
        }, Math.random() * 3000 + 5000); // Entre 5 e 8 segundos
        
        // Simular desistências ocasionalmente
        setTimeout(function() {
            if (modoAutomatico && simulacaoEmAndamento && Math.random() > 0.7) { // 30% de chance de desistência
                $.post('/api/simular-desistencia/');
            }
            executarDesistenciaAutomatica();
        }, Math.random() * 5000 + 10000); // Entre 10 e 15 segundos
        
        // Finalizar atendimentos automaticamente
        setTimeout(function() {
            if (modoAutomatico && simulacaoEmAndamento) {
                $('.btn-finalizar').each(function() {
                    if (Math.random() > 0.5) { // 50% de chance de finalizar
                        const postoId = $(this).data('posto-id');
                        $.post('/api/finalizar-atendimento/', { posto_id: postoId });
                    }
                });
            }
            executarFinalizacaoAutomatica();
        }, Math.random() * 3000 + 7000); // Entre 7 e 10 segundos
    }
    
    // Funções separadas para cada operação automática
    function executarGeracaoAutomatica() {
        if (modoAutomatico && simulacaoEmAndamento) {
            setTimeout(function() {
                const tipo = Math.random() > 0.7 ? 'P' : 'N'; // 30% de chance de ser prioritária
                $.post('/api/gerar-senha/', { tipo: tipo });
                executarGeracaoAutomatica();
            }, Math.random() * 3000 + 2000); // Entre 2 e 5 segundos
        }
    }
    
    function executarChamadaAutomatica() {
        if (modoAutomatico && simulacaoEmAndamento) {
            setTimeout(function() {
                $.post('/api/chamar-proxima/');
                executarChamadaAutomatica();
            }, Math.random() * 3000 + 5000); // Entre 5 e 8 segundos
        }
    }
    
    function executarDesistenciaAutomatica() {
        if (modoAutomatico && simulacaoEmAndamento) {
            setTimeout(function() {
                if (Math.random() > 0.7) { // 30% de chance de desistência
                    $.post('/api/simular-desistencia/');
                }
                executarDesistenciaAutomatica();
            }, Math.random() * 5000 + 10000); // Entre 10 e 15 segundos
        }
    }
    
    function executarFinalizacaoAutomatica() {
        if (modoAutomatico && simulacaoEmAndamento) {
            setTimeout(function() {
                $('.btn-finalizar').each(function() {
                    if (Math.random() > 0.5) { // 50% de chance de finalizar
                        const postoId = $(this).data('posto-id');
                        $.post('/api/finalizar-atendimento/', { posto_id: postoId });
                    }
                });
                executarFinalizacaoAutomatica();
            }, Math.random() * 3000 + 7000); // Entre 7 e 10 segundos
        }
    }
    
    // Adicionar estilo CSS para os alertas flutuantes
    $('<style>')
        .prop('type', 'text/css')
        .html(`
            .alert-floating {
                animation: slideIn 0.5s forwards;
            }
            
            @keyframes slideIn {
                0% { transform: translateX(100%); opacity: 0; }
                100% { transform: translateX(0); opacity: 1; }
            }
        `)
        .appendTo('head');
    
    // Inicializar o sistema ao carregar a página
    inicializarSistema();
});