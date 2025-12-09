//Script que traz as metas nos cards-->
document.addEventListener('DOMContentLoaded', () => {
  fetch('/okrs/getMetas')
    .then(response => {
      if (!response.ok) {
        throw new Error('Erro ao buscar metas');
      }
      return response.json();
    })
    .then(data => {
      // Preenche os campos da interface com os dados da meta
      document.getElementById('meta-csat').textContent = data.csat + ' %';
      document.getElementById('meta-sla-atendimento').textContent = data.sla_atendimento_prazo + ' %';
      document.getElementById('meta-sla-solucao').textContent = data.sla_resolucao_prazo + ' %';
      document.getElementById('meta-reabertura').textContent = data.reabertos + ' %';
      document.getElementById('meta-tma').textContent = data.tma + ' min';
      document.getElementById('meta-tms').textContent = data.tms + ' min';
      document.getElementById('meta-fcr').textContent = data.fcr + ' %';
    })
    .catch(error => {
      console.error('Erro ao carregar metas:', error);
    });
});