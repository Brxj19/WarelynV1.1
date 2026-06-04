# RAG + Copilot Pattern

## Knowledge base construction

- write user-question-friendly documents
- keep each document focused on one domain
- prefer short sections, bullets, and practical language
- keep source documents broad enough to answer common questions

## Chunking

- target chunk size: about 600 characters
- overlap: about 80 characters
- keep chunks semantically coherent

## Hybrid retrieval

1. tokenise the query
2. remove stop words
3. keyword search over the remaining tokens
4. embed the query
5. score candidates with lexical + semantic signals
6. sort by score and keep the top candidates
7. build context blocks
8. answer with citations

## Guardrails

- system prompt must scope the assistant to the application domain
- off-topic questions should be refused clearly
- confidence thresholds should cause abstention when evidence is weak
- answers should not expose secrets or write actions

## Live data integration

- detect report-like intent before answering
- fetch tenant-scoped live data from existing repositories
- return report data alongside the text answer
- render tabular live data inline in the chat UI where appropriate

## Reliability rules

- prefer “I don’t know” over a weak answer
- require citations for grounded responses
- keep retrieval tenant-scoped
- do not let the assistant mutate business data directly
