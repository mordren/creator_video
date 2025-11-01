document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.delete-video').forEach(button => {
        button.addEventListener('click', function() {
            const videoId = this.getAttribute('data-video-id');
            if (confirm('Tem certeza que deseja excluir este vídeo? Esta ação não pode ser desfeita.')) {
                const originalText = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                this.disabled = true;

                axios.delete(`/api/videos/${videoId}/delete`)
                    .then(response => {
                        showAlert('success', response.data.message);
                        setTimeout(() => location.reload(), 1200);
                    })
                    .catch(error => {
                        showAlert('danger', 'Erro: ' + (error.response?.data?.message || error.message));
                        this.innerHTML = originalText;
                        this.disabled = false;
                    });
            }
        });
    });
});