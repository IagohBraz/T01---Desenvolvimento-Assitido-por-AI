Especificações Técnicas da Plataforma de busca de informações da Xperiun

\# Objetivo  
Stack tecnica que servirá de guia para o Agente atuar seguindo as especificações que estão logo abaixo

\# Especificações Técnicas  
Esse projeto iremos atuar com o desenvolvimento seguindo ondas de entrega. Cada onda precisa necessariamente, ser desenvolvida, testada e revisada, sendo esse último, executado pelo Agente revisor ([Revisor.md](http://Revisor.md)). As ondas do projeto segue a ordem abaixo:

1 \- Colocar a Stack de pé ( Python 3.11+, Streamlit para frontend, Langchain para arquitetura RAG e vou utilizar o Chroma como banco vetorial). Suba toda a stack em ambiente virtual controlado com um resumo do projeto antes dos próximos desenvolvimentos abaixo. Coloque todas as variáveis no .env.exemple que ai eu altero para o .env com as API 's oficiais.

2 \- Retriever \- Fazer todo tratamento dos PDF’s/documentos quebrando em chunk, colocando os overlaps, passando pelo embbeding que sera o modelo da OpenAI (text-embedding-3-small ) e salvando no banco vetorial (Chroma). Aqui, se o PDF estiver difícil de extrair o texto, podemos usar algum OCR que seja mais específico para políticas e contratos. Se não precisar, podemos seguir com os extratores de Textos normais em python (PyMuPDF, pypdf). Como Chunk pode fazer uma quebra de 350 caracteres e como overlap de 52 caracteres (15% do tamanho do chunk: 350 × 0,15 = 52,5, arredondado para baixo)

3 \- Augmented: Baseado na pergunta do usuário recebida, eu quero que ela passe pelo mesmo processo de embbedings dos documentos da empresa na onda 1, usando a mesma infraestrutura (API da OpenAI text-embedding-3-small) e me traga os 3 chunks que são similares ao que o usuário perguntou. 

4 \- Generation: Agora, pego os 3 Chunks da onda anterior, a pergunta do usuário e o system prompt que você irá gerar e enviar para o Fornecedor de IA (Claude Opus 5.5)

\# Guardrails

- Não traga nenhuma lib sem antes me perguntar  
- Não aprove nenhuma instalação sem a minha aprovação  
- Sempre que tiver dúvidas, primeiro ponto é me chamar e verificar qual melhor caminho eu quero seguir, mas me traga 2 opções