# Codisplan NFS-e — Gestão Fiscal

**Reimplementação independente, Python 3.10+ / FastAPI / Vue 3 / Windows GUI + Service + Tray.**

> Versão-base **0.2.0**; a publicação só ocorre depois de testes, verificação dos artefatos nativos e PR conforme as regras do repositório. **A aplicação não é um serviço oficial do governo** e exige homologação com dados reais antes de uso em produção.

## Para o usuário do Windows

Extraia o pacote Windows inteiro e abra `CodisplanNFSe.exe` com dois cliques. A janela de administração permite instalar o serviço com confirmação UAC, iniciar/parar, consultar o status, escolher a porta local e abrir o painel responsivo. O serviço continua funcionando quando a janela fecha e mantém o ícone na área de notificação (*System Tray*). **Nenhum terminal/CLI é necessário para utilização.** Não mova nem renomeie o diretório `_internal` incluído no pacote.

No primeiro acesso, realize a configuração inicial com administrador local, cadastre CNPJ/CPF, importe e vincule o certificado A1 `.pfx/.p12`, e configure a URL HTTPS **oficial e verificada** do ADN Contribuinte. O Swagger fornecido não especifica `servers`; portanto **não existe endpoint de produção hardcoded ou inventado**. Sincronize por NSU e escolha relatório/período para PDF, Excel, CSV ou JSON.

A autenticação externa é **mTLS ICP-Brasil** com A1 validado na instalação local; o certificado é criptografado no armazenamento e não é publicado. O acesso por procuração e pelo mesmo CNPJ-base depende das autorizações do ADN. **A3 não foi implementado** — exige um adaptador PKCS#11/CSP e validação nativa.

## Recursos abrangidos

- `GET /DFe/{NSU}`: parâmetro `NSU`, `lote` e os filtros mutuamente exclusivos `cnpjConsulta` / `cpfConsulta`, inclusive consulta própria e por procuração quando autorizada.
- `GET /NFSe/{ChaveAcesso}/Eventos`: consulta de eventos da chave com preservação do XML e tipos de evento.
- Importação XML base64+gzip com controle de tamanho, integridade SHA-256, cursor NSU independente por empresa+certificado, persistência sem duplicação e projeção de cancelamento/substituição. Consultas avulsas **não** avançam o cursor de sincronização.
- Relatórios: **emissão mensal, competência, ISS retido e canceladas/substituídas**, com filtros de período; PDFs e Excel em formato fiscal, sem incluir notas canceladas/substituídas no faturamento vigente.
- Portal Vue 3 **compilado/vendorizado offline** com login, painel, empresas, certificados A1, sincronização, consulta por NSU, consulta por chave, documentos, relatórios, usuários, auditoria e configurações.
- API interna autenticada, logs auditáveis, interface GUI Windows e serviço nativo em segundo plano.

## Ciclo de desenvolvimento e distribuição

- `main` contém versão estável e recebe apenas PR de `develop` no título `release(patch|minor|major): ...`.
- `develop` integra trabalho validado através de PR `feat/*`, `fix/*`, `ci/*`, etc., com títulos Conventional Commits.
- Versão de referência única em `VERSION` e `pyproject.toml`: `MAJOR.MINOR.PATCH` (SemVer 2.0).
- Cada execução de pré-release no `develop` gera `MAJOR.MINOR.PATCH-dev.RUN.ATTEMPT` — sem tags reutilizadas. Após aprovação de testes e build, o workflow publica **os mesmos bytes validados** em GitHub Releases e GHCR.
- `main` publica release estável SemVer, com verificações de procedência, hashes, Windows x86/x64, serviço, UI/ícone e contêiner.
- Limpeza de caches restrita, com simulação e exclusão apenas elegível; nunca apagar tags ou artefatos para “consertar” versão.

As rotinas técnicas para **desenvolvedores e CI** estão em `scripts/` e `winbundle/`. O usuário final não as utiliza.

## Instalação de desenvolvimento

Arquivos de dependências estão fixados em `requirements-server.txt` e `winbundle/requirements-build.txt`; o frontend usa uma cópia local de Vue 3 e licença em `frontend/vendor/`. O backend é exposto apenas em `127.0.0.1` quando instalado como Windows Service. Para Docker, configure autenticação e um proxy TLS antes de expor em rede.

Documentação detalhada em `docs/arquitetura.md`, `docs/relatorios.md`, `docs/fluxo-semver.md` e `docs/qualidade.md`.

## Limitações conhecidas

O build Windows x86/x64, a integração real mTLS com ADN/ICP-Brasil, o comportamento do certificado A3 e a instalação em máquinas Windows específicas **dependem de testes nativos e homologação fiscal**. Os testes automatizados usam certificados e XMLs fictícios. As dependências diretas estão fixadas, mas ainda não há um lockfile transitive/hash completo reproduzível por plataforma; isto exige uma etapa adicional de hardening antes de uso corporativo.

Os relatórios são compatíveis **funcionalmente** com os quatro modelos enviados, mas não prometem reprodução idêntica de diagramação.
