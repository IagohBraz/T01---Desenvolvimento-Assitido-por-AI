# Revisão da onda 1 — Stack e ambiente — revisão 001

## Identificação e parecer

- Data/hora e fuso: 21/10/2026, 20:35, America/Sao_Paulo (UTC−03:00).
- Revisor e modelo solicitado: `revisor_xperiun` / `gpt-6.1-sol`.
- Modelo efetivo: o agente obrigatório **não iniciou**. A ferramenta de delegação selecionou o papel `revisor_xperiun`, configurado em runtime com `gpt-6.1-sol` e esforço `high`, mas devolveu erro HTTP 400: `The 'gpt-6.1-sol' model is not supported when using Codex with a ChatGPT account.` A configuração TOML também exige esse modelo. Este documento foi registrado pelo agente coordenador Codex, cujo identificador exato de modelo não está comprovado nesta execução; não representa uma revisão executada por GPT-6.1 Sol nem sua substituição.
- **Parecer: BLOQUEADA.** A revisão independente obrigatória não pôde ocorrer e os testes não chegaram a iniciar. Não avançar para a próxima onda com este registro.
- Condições para avançar: disponibilizar o modelo obrigatório em ambiente compatível, permitir a execução do Python base do venv existente e realizar nova revisão completa com testes e evidências.
- Base/alvo: estado local, sem commits fornecidos e sem inicializar Git (DEC-004). Inventário SHA-256 completo em `revisoes/onda-1/inventario-coordenacao-inicial.json`. Os 23 arquivos inventariados permaneceram com os mesmos hashes na conferência final anterior à escrita deste relatório. O inventário não inclui `.env` nem `.env.exemple`; este último não foi aberto nesta tentativa.
- Escopo acordado: ONDA 1, conforme `SPEC.md`, item 1, e `revisoes/onda-1/HANDOFF.md`: Python 3.11+, venv controlado, Streamlit/LangChain/Chroma, dependências autorizadas, instalação reproduzível, exemplo de configuração sem segredos, resumo e inicialização mínima.
- Relatório anterior: nenhum. `revisoes/DIAGNOSTICO_INICIAL.md` consultado como histórico, sem considerá-lo aprovação ou prova de testes atuais.

## Contexto e fontes consultadas

O contexto descreve a Xperiun como empresa cloud SaaS/IaaS B2B voltada à América Latina e a empresas de médio porte, com cobrança em reais e suporte local. Informa 450 colaboradores em dezembro de 2025, squads, trabalho híbrido e proteção da propriedade intelectual. Não apresenta declaração formal de missão, visão ou valores. O produto pretende atender consultas internas sobre contratos, comissões e fornecedores.

A ordem completa de leitura exigida para a revisão **não foi concluída**: contexto foi lido; os três PDFs em `docs/` foram somente inventariados e tiveram hashes calculados, sem extração ou inspeção visual. Após o bloqueio do modelo, PRD e SPEC foram lidos nessa ordem apenas para delimitar este registro e as verificações preliminares. Não se declara cumprimento da etapa documental da revisão. Falhas/ilegibilidade de páginas atuais não foram avaliadas; as limitações de extração do diagnóstico são evidência histórica, não revalidação.

Fontes administrativas lidas: `Agents.md`, `Revisor.md` integral, `.codex/agents/revisor_xperiun.toml` integral, `revisoes/MODELO_REVISAO.md`, HANDOFF, DECISOES e diagnóstico inicial. Também foram consultados README, dependências diretas e código listado abaixo. Hashes das fontes constam do inventário, inclusive dos PDFs apenas inventariados.

## Registro de atuação

| Área/arquivo | O que inspecionei ou executei | Evidência/localizador | Resultado e limitação |
| --- | --- | --- | --- |
| `Agents.md`, `Revisor.md`, TOML | Regras, modelo obrigatório, limites e critérios | Revisor: Identidade e finalidade; TOML: `model` | Não substituir modelo; revisão bloqueada após erro do runtime |
| `contexto/contexto.txt` | Leitura institucional | Arquivo inventariado | Contexto resumido acima; primeira saída do terminal apresentou acentos degradados |
| Três PDFs em `docs/` | Inventário e SHA-256 somente | Inventário JSON | Conteúdo e páginas não revisados; originais preservados |
| `PRD.md`, `SPEC.md` | Leitura sequencial após o impedimento | Guardrails; SPEC itens 1–4 | Escopo identificado; não equivale à revisão documental completa |
| HANDOFF, DECISOES, diagnóstico | Critérios, alegações do executor, decisões e histórico | HANDOFF: critérios/testes; DEC-001 a DEC-008 | Evidência declarada pelo executor, sem validação independente dos resultados |
| `app.py`, `src/xperiun_rag/config.py` | Leitura para segurança dos comandos | `settings = load_settings()`; `load_dotenv(...)` | Caminho padrão abre `.env`; necessária adaptação para respeitar a restrição atual |
| `scripts/check_stack.py` | Leitura do fluxo antes da tentativa | `main()`, cliente Chroma e `load_settings()` | Usa armazenamento temporário e configuração padrão; nenhuma execução atingiu esse código |
| `tests/test_app.py`, `tests/test_config.py` | Leitura antes da tentativa | Três testes AppTest; cinco testes de configuração | AppTest também carrega configuração padrão; execução não iniciada |
| `README.md`, `requirements.txt`, `.gitignore` | Leitura preliminar | Como rodar; oito dependências; padrões de exclusão | Arquivos presentes; não comprova ambiente ou reprodução da instalação |
| `requirements.lock.txt`, `src/xperiun_rag/__init__.py` | Hash, sem inspeção de conteúdo | Inventário JSON | Não validados tecnicamente |
| `.venv/pyvenv.cfg` | Leitura após falha de lançamento | `home`, `version`, `executable` | Declara Python 3.12.5; disponibilidade não demonstrada |
| Python base | Consulta de existência/acesso | `Test-Path` no executável referenciado pelo venv | `UnauthorizedAccessException` / Acesso negado; não prova inexistência |
| Escritas | Apenas artefatos em `revisoes/onda-1/` | Inventário, `verificacao_isolada.py`, este relatório | Nenhuma fonte, configuração, dependência ou código do produto alterado |

Não houve instalação, API externa, migração, inicialização de Git ou leitura do `.env`. Foi lida a skill local de PDF para preparação, mas nenhuma operação de extração/renderização foi executada. Não houve leitura de valores do exemplo: o invólucro criado para os testes sequer iniciou.

## Matriz de requisitos

| ID/requisito e fonte | Evidência | Status | Achado/pendência |
| --- | --- | --- | --- |
| Revisão independente com GPT-6.1 Sol — Revisor/TOML | Erro 400 na chamada ao agente obrigatório | Não conforme nesta tentativa | REV-O1-001; impedimento de ambiente, não defeito do produto |
| Python 3.11+ e venv controlado — SPEC item 1 | pyvenv.cfg declara 3.12.5; launcher não inicia | Não verificado | REV-O1-002 |
| Stack instalada/operacional — SPEC item 1 | Dependências diretas listadas; teste indisponível | Não verificado | REV-O1-002 |
| Bibliotecas/instalações aprovadas — SPEC guardrails | DEC-008 registra oito bibliotecas e transitivas | Conforme documentalmente | Instalação efetiva não auditada |
| Execução reproduzível — HANDOFF critério 2 | README e arquivos de dependências presentes | Não verificado integralmente | Lock não inspecionado e nenhum ambiente reconstruído |
| `.env.exemple`, variáveis e chaves vazias — SPEC item 1 | Alegação do HANDOFF; teste não iniciado | Não verificado | Revalidar sem expor valores |
| Exclusão de segredos/dados locais — Revisor onda 1 | `.gitignore` contém `.env`, `.venv/`, `data/` | Conforme quanto aos padrões | Não se afirma verificação de índice Git; DEC-004 adia Git |
| Resumo do projeto — SPEC item 1 | README: público, arquitetura, ondas e execução | Conforme quanto à presença e conteúdo preliminar | Revisão independente permanece pendente |
| Inicialização/ausência de credenciais/segredos — Revisor onda 1 | Código e testes presentes; sem resultado próprio | Não verificado | REV-O1-002 |
| Ingestão, recuperação e geração — SPEC itens 2–4 | Fora da entrega atual | Não aplicável à onda 1 | Não exigir implementação antecipada |

## Testes e verificações

Para cumprir a proibição de ler o `.env`, os comandos foram preparados por meio de `verificacao_isolada.py`: redirecionamento de `dotenv.load_dotenv` do arquivo real para arquivo temporário vazio, preservando arquivos sintéticos dos testes, limpeza das variáveis relevantes no processo, telemetria desabilitada e audit hook de bloqueio de leitura do `.env` real, rede e subprocessos. O invólucro usa `runpy` para executar o script ou o módulo unittest. **Não foi possível comprovar essas proteções em execução porque o interpretador não iniciou.** Não se atribui equivalência irrestrita aos comandos sem adaptação.

| Comando/cenário | Ambiente e dados | Origem da evidência | Esperado | Observado | Status |
| --- | --- | --- | --- | --- | --- |
| `.venv\Scripts\python revisoes\onda-1\verificacao_isolada.py stack` → `scripts/check_stack.py` | Venv existente; planejados dados sintéticos e configuração vazia | Coordenador, tentativa local | Versões e smoke test Chroma | Exit 1 antes de iniciar Python: `No Python at` no executável base configurado | Não executado; launcher falhou |
| `.venv\Scripts\python revisoes\onda-1\verificacao_isolada.py tests` → `python -m unittest discover -s tests -v` | Mesmo venv; isolamento planejado | Coordenador, tentativa local | Oito testes passam | Mesmo exit 1 antes de iniciar Python | Não executado; launcher falhou |
| `Test-Path` no Python base | Caminho de pyvenv.cfg | Coordenador | Determinar acesso | Acesso negado; o `False` emitido não é prova de ausência | Inconclusivo quanto à existência |
| Conferência SHA-256 | 23 arquivos do inventário | Coordenador | Nenhuma alteração concorrente | Zero divergências | Passou para o conjunto inventariado |
| Stack, oito testes e HTTP health | Ambiente descrito no HANDOFF | Executor | Sucesso | HANDOFF declara STACK OK, 8/8 e HTTP 200 | Não revalidado nesta execução |

O caminho do Python base indicado é `C:\Users\Iago\AppData\Local\Programs\Python\Python312\python.exe`. Não se tentou outro Python, instalação ou alteração do venv. Os comandos exatos sem invólucro não foram executados, pois carregariam `.env` caso o interpretador estivesse acessível. Nenhuma falha funcional de teste foi observada: nenhum teste iniciou.

## Achados

### REV-O1-001 — Modelo obrigatório indisponível nesta conta

- Severidade e bloqueio: P1 de processo, bloqueante para aprovação; não é defeito de implementação.
- Requisito/fonte: `Revisor.md`, Identidade e finalidade; `.codex/agents/revisor_xperiun.toml`, `model = "gpt-6.1-sol"`.
- Local: chamada `collaboration.spawn_agent`, tarefa `/root/revisao_onda_1`, papel `revisor_xperiun`.
- Evidência sanitizada e grau de certeza: erro HTTP 400 reproduzido na identificação; confirmado pelo runtime.
- Como reproduzir: solicitar o papel configurado com esse modelo no ambiente desta conta ChatGPT.
- Esperado versus observado: início do revisor obrigatório versus rejeição antes de executar a revisão.
- Impacto: impossibilidade de emitir aprovação válida da onda.
- Correção proposta: executar a revisão em ambiente/conta compatível com o modelo obrigatório. Não substituir silenciosamente o modelo nem alterar as instruções.
- Critério de aceite: agente obrigatório inicia com evidência de seleção do modelo e conclui revisão independente conforme o modelo de relatório.
- Dependências/decisão necessária: disponibilidade externa do modelo. Opção A: executar em ambiente compatível; opção B: manter a onda bloqueada até essa disponibilidade. Nenhuma dessas opções autoriza substituição de modelo.

### REV-O1-002 — Python base do venv inacessível para esta execução

- Severidade e bloqueio: P1 de verificação, bloqueante por ausência de testes essenciais; não é defeito comprovado da entrega.
- Requisito/fonte: SPEC item 1; HANDOFF critérios 1 e 5; Revisor, testes e parecer.
- Local: `.venv/pyvenv.cfg`, campos `home` e `executable`; ambas as tentativas de comando acima.
- Evidência sanitizada e grau de certeza: launcher retornou exit 1 e `No Python at`; a consulta ao caminho base retornou acesso negado. Confirmada a impossibilidade de executar neste contexto; causa exata além da restrição de acesso não demonstrada.
- Como reproduzir: executar qualquer um dos dois comandos de verificação registrados neste mesmo contexto.
- Esperado versus observado: Python executa os testes versus interrupção antes de inicializar o interpretador.
- Impacto: stack, Chroma e inicialização Streamlit não revalidados; versões instaladas e oito testes continuam apenas declarados pelo executor.
- Correção proposta: disponibilizar acesso ao Python base do venv existente em contexto autorizado e repetir os testes com isolamento do `.env` e da rede. Não reinstalar ou recriar o ambiente por suposição.
- Critério de aceite: o venv inicia; script termina com STACK OK; oito testes terminam OK; registrar códigos de saída e confirmar que nenhum segredo real foi lido e nenhuma API externa foi chamada.
- Dependências/decisão necessária: acesso ao executável base. Opção A: realizar a verificação em contexto que tenha acesso ao mesmo venv; opção B: manter bloqueada até ajuste desse acesso. Instalação não autorizada neste pedido.

## Conflitos e decisões do usuário

| ID | Fontes/trechos em conflito | Impacto | Opção A | Opção B | Decisão e evidência / pendente |
| --- | --- | --- | --- | --- | --- |
| Histórico do modelo | Diagnóstico inicial menciona Astra; Revisor/TOML atuais exigem GPT-6.1 Sol | Não usar a instrução histórica para substituir o modelo | Seguir configuração vigente | Alteração expressa futura pelo usuário | Aplicada a configuração vigente; execução recusada |
| INI-001 | Histórico: 40 caracteres versus 15%; SPEC atual: 52, arredondado para baixo | Dependência da onda 2 | 40 fixos (histórico) | 52 com arredondamento | DEC-001 registra 52 e atualização autorizada da SPEC |
| INI-002 | PRD proíbe vazamento de confidenciais; DEC-002/007 autorizam acesso/envio na POC | Política das ondas posteriores | Excluir confidenciais | Incluir com autorização explícita | DEC-002/007 registram autorização; pedido atual proíbe APIs externas nesta revisão |
| Referência da onda 3 | SPEC onda 3 menciona embeddings dos documentos na onda 1; descritos na onda 2 | Referência inconsistente, sem exigir ingestão na onda 1 | Usar dependência funcional da onda 2 | Solicitar esclarecimento se houver impacto adicional | Revisor já orienta usar a dependência da onda 2 |

Não foi identificado conflito de stack entre PRD e SPEC na leitura preliminar. DEC-003, 004, 005, 006 e 008 também foram consideradas: PyMuPDF antes de OCR autorizado, Git adiado, revisão na OpenAI, grafia `.env.exemple` e dependências aprovadas. A restrição atual de não instalar e não chamar APIs prevaleceu nesta tentativa.

## Plano de correção para o executor

| Ordem | ID do achado | Ação concreta e arquivos | Dependências | Critério de aceite | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | REV-O1-001 | Providenciar contexto capaz de iniciar o revisor configurado; preservar TOML/Revisor | Disponibilidade do modelo | Inicialização com GPT-6.1 Sol comprovada | Pendente |
| 2 | REV-O1-002 | Providenciar acesso ao Python base do venv; preservar produto e não instalar nesta autorização | Permissões/ambiente | Stack e testes executados com isolamento e resultados registrados | Pendente |
| 3 | Ambos | Solicitar nova revisão integral, incluindo PDFs e inspeção de todos os arquivos da entrega | Itens anteriores | Novo relatório `revisao-002.md`, com matriz completa e parecer válido | Pendente |

### Mensagem pronta para o executor

A revisão da ONDA 1 está BLOQUEADA por indisponibilidade do modelo obrigatório e impossibilidade de iniciar o Python do venv neste ambiente. Não há correção de produto comprovadamente necessária neste registro. Resolva os impedimentos de execução, preserve docs/, contexto/, PRD, SPEC e produto, e não instale nada sob esta autorização. Entregue evidências por ID e solicite nova revisão GPT-6.1 Sol, preservando este relatório. A nova revisão deve seguir integralmente a ordem de leitura e reexecutar os testes sem acessar valores reais do `.env` nem APIs externas.

## Reavaliação e riscos restantes

| ID anterior | Situação atual | Evidência de revalidação | Ação restante |
| --- | --- | --- | --- |
| Primeira revisão | Bloqueada antes da revisão independente | Rejeição do modelo e falha do launcher | Executar revisão completa em contexto compatível |
| INI-001 | Decisão registrada | SPEC atual e DEC-001 | Validar implementação de chunking na onda 2 |
| INI-002 | Decisão registrada | DEC-002/007 | Verificar controles/payloads nas ondas pertinentes |
| INI-003 | Não revalidado | Nenhuma extração atual | Conferir PDFs e fidelidade na revisão completa/onda 2 |
| INI-004 | Não verificado | Nenhuma consulta externa realizada | Verificar modelo/identificador de geração na onda 4 |

Limitações restantes: nenhum teste funcional executado, nenhuma inspeção documental dos PDFs, exemplo e lock não auditados, nenhuma reprodução da instalação, nenhum health check próprio, nenhuma chamada real de provedor e nenhuma revisão pelo modelo obrigatório. As evidências fornecidas pelo executor não foram convertidas em resultados próprios. Este parecer não aprova a onda nem autoriza implantação.

