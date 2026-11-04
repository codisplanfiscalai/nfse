# Critérios de qualidade

- Testes com mocks da API ADN e certificados de teste; nenhum certificado/credencial real no repositório.
- Contrato de autenticação, busca XML, consulta de eventos, reprocessamento, não duplicação, cancelamento, geração PDF/XLSX/CSV e CSRF.
- Testes das rotinas de versão SemVer, promoção por PR, branch policy e cache cleanup derivados dos padrões arquiteturais de referência.
- Verificação visual automatizada do Vue em 1440px (desktop) e 390px (mobile), incluindo responsividade sem overflow.
- Build Windows nativo em x86/x64, verificação de PE GUI/service, ícone Codisplan, manifesto SHA-256 e smoke test da interface/tray.
- Teste de container e publicação apenas após todos os gates. Sem build em Linux afirmado como equivalente ao executável Windows.
- **Não homologados**: autenticação real ADN com certificado comercial, A3 PKCS#11, desempenho em lotes grandes, comportamento dos certificados em todos os drivers/versões de Windows.
