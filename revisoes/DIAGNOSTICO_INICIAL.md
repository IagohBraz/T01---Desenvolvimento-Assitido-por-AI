# Diagnóstico inicial — preparação do revisor

Data: 21/10/2026. Escopo: entendimento do projeto e criação do processo de revisão. Este documento não é aprovação de uma onda nem evidência de uma execução independente do revisor Astra.

## Estado encontrado

O projeto contém contexto institucional, três PDFs oficiais, PRD, SPEC e instruções de projeto. Não foi encontrada implementação da aplicação na raiz inspecionada. A entrega solicitada foi a criação do revisor, não o desenvolvimento da onda 1.

O produto é um chatbot RAG para consultas internas sobre contratos, comissões e fornecedores. A Xperiun atua com infraestrutura cloud e SaaS B2B, foco latino-americano, cobrança em reais e suporte local. O contexto descreve operação híbrida, squads e proteção de propriedade intelectual; não apresenta missão, visão e valores formalmente definidos.

## Atuação realizada

- Leitura de `Agents.md` e de todo `contexto/contexto.txt`.
- Extração local dos três PDFs com `pdftotext -layout`, já disponível no ambiente, seguida da leitura de PRD e SPEC. Os PDFs não foram modificados.
- Identificação de limitações da extração: texto sobreposto no aditivo de fornecedores, alinhamento ambíguo da tabela de vendas e caracteres acentuados degradados na saída do terminal. Não houve conferência visual das páginas; os valores dessas tabelas não foram adotados como gabarito.
- Consulta à documentação oficial de agentes personalizados para definir o arquivo TOML e a seleção de modelo.
- Criação de `Revisor.md`, `.codex/agents/revisor_xperiun.toml` e `revisoes/MODELO_REVISAO.md`.
- Inclusão em `Agents.md` da chamada obrigatória ao revisor após desenvolvimento e testes de cada onda.
- Conferência de existência dos arquivos. Tentativa de validação TOML com `python` não executada: pyenv não tem versão global/local selecionada. Nenhuma biblioteca foi adicionada e nenhuma instalação foi realizada.

## Pendências para o executor e o usuário

| ID | Quando resolver | Pendência | Opção A | Opção B |
| --- | --- | --- | --- | --- |
| INI-001 | Antes do chunking da onda 2 | SPEC pede 40 caracteres de overlap e também 15% de 350 (52,5). | Usar 40 caracteres fixos. | Usar 15%, definindo o arredondamento inteiro. |
| INI-002 | Antes de enviar documentos a embeddings externos | Política de vendas marcada como confidencial; o PRD também deseja responder sobre comissões. Não há política explícita de acesso/envio. | Excluir confidenciais do pipeline externo. | Definir acesso e autorização de envio externo antes de liberar conteúdo. |
| INI-003 | Na onda 2 | Extração do aditivo tem sobreposições; tabela de vendas requer validação visual. | Avaliar extrator textual aprovado com conferência das páginas. | Se insuficiente, propor OCR específico e solicitar aprovação antes de adicionar/instalar. |
| INI-004 | Antes da integração real da onda 4 | Identificador e disponibilidade de Claude Opus 5.5 não verificados neste trabalho. | Usar o modelo exigido após verificar acesso e identificador oficial. | Se indisponível, apresentar alternativa ao usuário e aguardar decisão; não substituir sozinho. |

A referência da onda 3 aos embeddings da onda 1 é inconsistente com a descrição da onda 2. O revisor registra a divergência e verifica a dependência funcional da onda 2. Não foi identificado conflito direto de stack entre PRD e SPEC.

Há divergência cadastral entre contexto institucional e contrato de trabalho. Para respostas sobre um documento, preservar sua atribuição e informar a divergência quando relevante; não fundir informações conflitantes.

## Como acionar

Ao concluir cada onda, o executor deve seguir `Agents.md` e delegar ao agente `revisor_xperiun`. Exemplo de solicitação:

> Chame o revisor_xperiun em Astra (gpt-6-astra) para revisar a onda 1. Siga Revisor.md. Considere os arquivos e testes desta entrega, registre limitações e salve o relatório em revisoes/onda-1/revisao-001.md com o plano de correções para o executor.

Informe junto os arquivos/commits da entrega, resultados dos testes e decisões aprovadas. Para reavaliar, informe o relatório anterior e as correções por ID. O relatório seguinte deve usar novo número, preservando o anterior.

A configuração fixa `model = "gpt-6-astra"`. Seu carregamento pelo cliente e uma execução real do agente não foram testados neste trabalho. As instruções de projeto exigem seleção explícita na delegação quando o cliente não carregar agentes personalizados por nome. Markdown não impõe o modelo sozinho e esta configuração não cria um serviço que monitora arquivos em segundo plano.

Referência do formato de agente: [documentação oficial de subagentes](https://learn.chatgpt.com/docs/agent-configuration/subagents).
