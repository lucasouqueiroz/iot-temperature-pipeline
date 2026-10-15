# Checklist de entrega e roteiro

## Evidencias obrigatorias

- [ ] Testes unitarios executados e resultado registrado.
- [ ] Container saudavel e carga confirmada no PostgreSQL.
- [ ] Reexecucao mantem a quantidade de leituras.
- [ ] Tres views com resultados consistentes.
- [ ] Tres graficos e indicadores conferidos.
- [ ] Prints reais em docs/screenshots e incorporados no README/PDF.
- [ ] PDF final: contexto, arquitetura, passos realizados, explicacao das views, prints, insights e limitacoes.
- [ ] Video de ate quatro minutos publicado e link testado em aba anonima.
- [ ] Repositorio publico acessivel e links finais enviados na plataforma.

## Estrutura sugerida do PDF (nao e o documento final)

1. Capa com nome, disciplina, turma e data.
2. Problema: consolidar e analisar leituras historicas de temperatura.
3. Arquitetura: CSV → validacao Python → PostgreSQL Docker → views → Streamlit.
4. Execucao: registrar comandos e resultados efetivamente observados.
5. Qualidade: uma duplicata exata removida, validacao estrita, source_id unico e recarga transacional.
6. Views: proposito, agrupamento e limitacoes de cada consulta.
7. Dashboard: incorporar capturas reais e comentar cada grafico.
8. Insights: medias e volumes diferentes em In/Out; nao confundir correlacao com causalidade nem grupos com sensores.
9. Aplicacao real: investigacao de extremos e apoio a limites definidos pelo negocio.
10. Limitacoes: lote historico, fuso nao informado, grupos nao sao IDs fisicos, sem IA implementada; evolucoes possiveis incluem ingestao incremental e alertas.
11. Links do repositorio, Kaggle e video.

## Pitch: alvo de 3min40s

0:00–0:25: apresentar o problema e o objetivo do pipeline.
0:25–1:00: explicar o fluxo e o papel de Python, Docker, PostgreSQL e Streamlit.
1:00–1:40: mostrar validacao, duplicata removida, transacao e tres views.
1:40–2:55: demonstrar o dashboard funcional, os indicadores e os tres graficos.
2:55–3:25: comentar diferenca das medias e limitacoes de amostragem e identificacao de sensores.
3:25–3:40: concluir com usos praticos e apontar o repositorio.

Somente grave a demonstracao apos validar localmente. Nao publique senhas, tokens nem a tela do .env no video ou nos prints. A nota depende da avaliacao do professor; este checklist nao garante nota maxima.
