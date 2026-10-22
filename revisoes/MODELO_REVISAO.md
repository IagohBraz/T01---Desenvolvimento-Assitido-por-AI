# Revisão da onda <N> — <nome> — revisão <NNN>

## Identificação e parecer

- Data/hora e fuso:
- Revisor e modelo solicitado: revisor_xperiun / gpt-6.1-sol.
- Modelo efetivo: <evidência do runtime, ou não verificável; não inferir do prompt>.
- Parecer: <APROVADA | APROVADA COM RESSALVAS | REPROVADA | BLOQUEADA>.
- Justificativa e condições para avançar:
- Base/alvo: <commits + alterações locais, ou inventário e hashes>.
- Escopo acordado e critérios de aceite:
- Relatório anterior:

## Contexto e fontes consultadas

Resumir contexto relevante da Xperiun sem inventar missão, visão ou valores.
Listar fontes lidas na ordem contexto/, docs/, PRD, SPEC; indicar versão/hash, seções/páginas utilizadas, falhas de leitura e exclusões. Não copiar dados confidenciais.

## Registro de atuação

| Área/arquivo | O que inspecionei ou executei | Evidência/localizador | Resultado e limitação |
| --- | --- | --- | --- |
| <preencher> | <preencher> | <arquivo:linha, página ou comando> | <preencher> |

Incluir todos os arquivos inspecionados, comandos pertinentes, testes, ações de escrita e itens não revisados. Registrar se o alvo mudou durante a revisão.

## Matriz de requisitos

| ID/requisito e fonte | Evidência | Status | Achado/pendência |
| --- | --- | --- | --- |
| <preencher> | <preencher> | <conforme / não conforme / não verificado / não aplicável com motivo> | <preencher> |

## Testes e verificações

| Comando/cenário | Ambiente e dados | Origem da evidência | Esperado | Observado | Status |
| --- | --- | --- | --- | --- | --- |
| <preencher> | <versões; real ou mock> | <revisor ou executor> | <preencher> | <evidência sanitizada> | <passou / falhou / não executado> |

Registrar motivo dos testes não executados e efeito no parecer. Evidência de execução deve ter saída relevante/código de saída quando disponível.

## Achados

### REV-O<N>-001 — <título objetivo>

- Severidade e bloqueio:
- Requisito/fonte:
- Arquivo/linha ou documento/página:
- Evidência sanitizada e grau de certeza:
- Como reproduzir:
- Esperado versus observado:
- Impacto:
- Correção proposta:
- Critério de aceite e teste que comprova a correção:
- Dependências/decisão necessária:

Repetir para cada achado. Se não houver achados, afirmar isso sem omitir limitações.

## Conflitos e decisões do usuário

| ID | Fontes/trechos em conflito | Impacto | Opção A | Opção B | Decisão e evidência / pendente |
| --- | --- | --- | --- | --- | --- |
| <preencher ou nenhum> | <preencher> | <preencher> | <preencher> | <preencher> | <preencher> |

## Plano de correção para o executor

| Ordem | ID do achado | Ação concreta e arquivos | Dependências | Critério de aceite | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | <ID> | <preencher> | <preencher> | <teste/resultado> | Pendente |

### Mensagem pronta para o executor

Corrija os achados executáveis deste relatório na ordem indicada. Preserve docs/, contexto/, PRD e SPEC. Não instale nem acrescente bibliotecas sem aprovação. Não resolva decisões pendentes por suposição. Para cada ID, entregue arquivos alterados, comportamento corrigido e testes com resultados; solicite nova revisão GPT-6.1 Sol da mesma onda. Não declare um achado encerrado sem revalidação do revisor.

## Reavaliação e riscos restantes

| ID anterior | Situação atual | Evidência de revalidação | Ação restante |
| --- | --- | --- | --- |
| <ID ou primeira revisão> | <corrigido e verificado / parcial / pendente / não verificado / reaberto> | <preencher> | <preencher> |

Listar limitações, riscos residuais e dependências futuras sem confundir trabalho fora da onda com defeito da entrega atual.
