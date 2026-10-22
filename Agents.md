Regras das pastas do projeto: Plataforma de busca de informações da Xperiun

\# Objetivo  
Sempre execute a leitura dos aquivos seguinto as seguintes pastas:

1 \- ‘contexto/’: Sempre leia e traga esse contexto geral da Xperiun (informações como: visão, missão, valores, nicho e momento da empresa)  
2 \- ‘docs/’: A fonte da verdade que não deve ser alterada, apenas consumida. São os documentos oficiais da empresa que serão usados para os chunks.  
3 \- Sempre leia, nessa ordem: [PRD.md](http://PRD.md) e [SPEC.md](http://SPEC.md). Se tiver dúvidas, sempre siga o que estiver na SPEC e me fale o que teve de conflito. Em um cenário que não consiga distinguir qual seguir, me pergunte.  

## Revisão obrigatória ao final de cada onda

Após desenvolver e testar cada onda da SPEC, delegue uma revisão independente ao agente `revisor_xperiun`, configurado em `.codex/agents/revisor_xperiun.toml`, e siga `Revisor.md`. O modelo obrigatório do revisor é GPT-6.1 Sol (`gpt-6.1-sol`). Esta instrução autoriza a delegação de revisão em cada onda e em suas reavaliações.

Passe ao revisor: número e objetivo da onda, arquivos/commits alterados, critérios de aceite, testes e resultados, decisões aprovadas e relatório anterior. Aguarde o relatório em `revisoes/onda-<N>/revisao-<NNN>.md` antes de declarar a onda concluída. Corrija os achados bloqueantes e solicite nova revisão. Não avance com parecer REPROVADA ou BLOQUEADA; ressalvas devem estar justificadas como não bloqueantes.

Se a ferramenta de delegação não carregar agentes por nome, selecione explicitamente `gpt-6.1-sol` e envie o caminho de `Revisor.md`, o modelo de relatório e o contexto da entrega em uma nova instância. Não use herança de conversa que impeça selecionar o modelo. Se não puder chamar GPT-6.1 Sol, informe a limitação; não substitua por outro modelo nem marque a revisão como concluída.
