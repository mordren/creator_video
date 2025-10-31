// video_edit.js - Versão Corrigida
document.addEventListener('DOMContentLoaded', function() {
    console.log('Video Edit JS carregado');

    // Prevenir submissão normal do formulário e usar AJAX
    const videoForm = document.getElementById('videoForm');
    if (videoForm) {
        videoForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            try {
                // Mostrar loading
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Salvando...';
                submitBtn.disabled = true;

                const formData = new FormData(this);
                
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                
                if (result.status === 'success') {
                    showAlert(result.message, 'success');
                    // Opcional: recarregar a página após 2 segundos para ver mudanças
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    showAlert(result.message || 'Erro ao salvar', 'danger');
                }
                
            } catch (error) {
                console.error('Erro:', error);
                showAlert('Erro de conexão ao salvar', 'danger');
            } finally {
                // Restaurar botão
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // Função para mostrar alertas
    function showAlert(message, type) {
        // Remove alertas existentes
        const existingAlerts = document.querySelectorAll('.alert-dismissible');
        existingAlerts.forEach(alert => alert.remove());
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Inserir no topo da página
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remover após 5 segundos
        setTimeout(() => {
            if (alertDiv.parentElement) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Configurar data/hora atual no modal YouTube
    const youtubeModal = document.getElementById('youtubeModal');
    if (youtubeModal) {
        youtubeModal.addEventListener('show.bs.modal', function() {
            const now = new Date();
            const horaUpload = now.toISOString().slice(0, 16);
            document.getElementById('hora_upload').value = horaUpload;
            
            // Limpar campos ao abrir
            document.getElementById('youtube_link').value = '';
            document.getElementById('visualizacoes').value = '0';
            document.getElementById('likes').value = '0';
            document.getElementById('comentarios').value = '0';
        });
    }

    // Formulário YouTube manual
    const youtubeForm = document.getElementById('youtubeForm');
    if (youtubeForm) {
        youtubeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            try {
                const formData = new FormData(this);
                const response = await fetch('/api/youtube_uploads', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    showAlert(result.message, 'success');
                    const modal = bootstrap.Modal.getInstance(youtubeModal);
                    modal.hide();
                    // Recarregar para mostrar o novo upload
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showAlert(result.message, 'danger');
                }
            } catch (error) {
                console.error('Erro:', error);
                showAlert('Erro ao salvar upload', 'danger');
            }
        });
    }

    // Botões de ação
    document.querySelectorAll('.generate-audio').forEach(btn => {
        btn.addEventListener('click', async function() {
            const videoId = this.dataset.videoId;
            const originalText = this.innerHTML;
            
            try {
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Gerando...';
                this.disabled = true;
                
                const response = await fetch(`/api/videos/${videoId}/generate_audio`, {
                    method: 'POST'
                });
                
                const result = await response.json();
                showAlert(result.message, result.status);
                
                if (result.status === 'success') {
                    setTimeout(() => window.location.reload(), 2000);
                }
            } catch (error) {
                console.error('Erro:', error);
                showAlert('Erro ao gerar áudio', 'danger');
            } finally {
                this.innerHTML = originalText;
                this.disabled = false;
            }
        });
    });

    document.querySelectorAll('.generate-video').forEach(btn => {
        btn.addEventListener('click', async function() {
            const videoId = this.dataset.videoId;
            const originalText = this.innerHTML;
            
            try {
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Gerando...';
                this.disabled = true;
                
                const response = await fetch(`/api/videos/${videoId}/generate_video`, {
                    method: 'POST'
                });
                
                const result = await response.json();
                showAlert(result.message, result.status);
                
                if (result.status === 'success') {
                    setTimeout(() => window.location.reload(), 2000);
                }
            } catch (error) {
                console.error('Erro:', error);
                showAlert('Erro ao gerar vídeo', 'danger');
            } finally {
                this.innerHTML = originalText;
                this.disabled = false;
            }
        });
    });

    document.querySelectorAll('.upload-youtube').forEach(btn => {
        btn.addEventListener('click', function() {
            const videoId = this.dataset.videoId;
            console.log('Upload YouTube para:', videoId);
            const modal = new bootstrap.Modal(document.getElementById('modalUploadConfirm'));
            modal.show();
        });
    });

    // Confirmação de upload
    const btnConfirmUpload = document.getElementById('btn-confirm-upload');
    if (btnConfirmUpload) {
        btnConfirmUpload.addEventListener('click', async function() {
            const videoId = document.querySelector('.upload-youtube').dataset.videoId;
            const publicarAgora = document.getElementById('publicar_agora').checked;
            
            try {
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Enviando...';
                this.disabled = true;
                
                const response = await fetch(`/api/videos/${videoId}/upload_youtube`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        publicar_agora: publicarAgora
                    })
                });
                
                const result = await response.json();
                showAlert(result.message, result.status);
                
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalUploadConfirm'));
                modal.hide();
                
                if (result.status === 'success') {
                    setTimeout(() => window.location.reload(), 2000);
                }
            } catch (error) {
                console.error('Erro:', error);
                showAlert('Erro ao fazer upload', 'danger');
            } finally {
                this.innerHTML = '<i class="fas fa-upload me-2"></i>Fazer Upload';
                this.disabled = false;
            }
        });
    }

    // Agendamento
    const btnSalvarAgendamento = document.getElementById('btn-salvar-agendamento');
    if (btnSalvarAgendamento) {
        btnSalvarAgendamento.addEventListener('click', function() {
            console.log('Salvar agendamento');
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalAgendamento'));
            modal.hide();
        });
    }

    // Delete video
    document.querySelectorAll('.delete-video').forEach(btn => {
        btn.addEventListener('click', async function() {
            const videoId = this.dataset.videoId;
            
            if (confirm('Tem certeza que deseja excluir este vídeo? Esta ação não pode ser desfeita!')) {
                try {
                    const response = await fetch(`/api/videos/${videoId}/delete`, {
                        method: 'POST'
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        showAlert(result.message, 'success');
                        setTimeout(() => {
                            window.location.href = '/videos';
                        }, 1500);
                    } else {
                        showAlert(result.message, 'danger');
                    }
                } catch (error) {
                    console.error('Erro:', error);
                    showAlert('Erro ao excluir vídeo', 'danger');
                }
            }
        });
    });
});