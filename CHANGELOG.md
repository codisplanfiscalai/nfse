# Registro de alterações

Este projeto segue [Semantic Versioning 2.0.0](https://semver.org/lang/pt-BR/).

## [0.3.0] — em desenvolvimento

### Added
- Nova identidade visual exclusiva Codisplan NFS-e (índigo/violeta/turquesa/âmbar), símbolo próprio e assets reproduzíveis SVG/ICO/PNG.
- Servidor FastAPI integrado ao executável: inicialização automática no System Tray e gerenciamento de ciclo de vida pela GUI.
- Testes de ciclo de vida HTTP, porta ocupada, reinicialização e integração Windows GUI no smoke test.

### Fixed
- Removida a exigência de instalar serviço Windows e os erros SCM 1060.
- Botões Iniciar, Interromper, Reiniciar e Abrir portal funcionam sem CLI nem UAC.
- Persistência local no perfil do usuário em LOCALAPPDATA.

## [0.2.0] — versão anterior

### Added
- Reimplementação da API ADN e dos relatórios em Python/FastAPI, com autenticação por certificado digital A1.
- Portal administrativo responsivo em Vue 3, sem CDN, e aplicativo nativo Windows com System Tray e serviço independente.
- Importação XML, NSU transacional por contribuinte/certificado, persistência, eventos e exportações fiscais.
- Pipeline SemVer baseado em `VERSION`, pré-release de `develop`, release estável de `main`, GHCR, Windows x86/x64 e verificação de hashes.

### Changed
- **Substituição integral** da arquitetura NFS-e anterior. Os projetos de referência foram usados para padrões de arquitetura e UX; não foram transplantadas regras de negócio alheias.

### Limitations
- Dispositivo A3 não implementado; integração ADN produtiva exige certificado autorizado e homologação.
