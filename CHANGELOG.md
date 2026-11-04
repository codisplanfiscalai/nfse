# Registro de alterações

Este projeto segue [Semantic Versioning 2.0.0](https://semver.org/lang/pt-BR/).

## [0.2.0] — em desenvolvimento

### Added
- Reimplementação da API ADN e dos relatórios em Python/FastAPI, com autenticação por certificado digital A1.
- Portal administrativo responsivo em Vue 3, sem CDN, e aplicativo nativo Windows com System Tray e serviço independente.
- Importação XML, NSU transacional por contribuinte/certificado, persistência, eventos e exportações fiscais.
- Pipeline SemVer baseado em `VERSION`, pré-release de `develop`, release estável de `main`, GHCR, Windows x86/x64 e verificação de hashes.

### Changed
- **Substituição integral** da arquitetura NFS-e anterior. Os projetos de referência foram usados para padrões de arquitetura e UX; não foram transplantadas regras de negócio alheias.

### Limitations
- Dispositivo A3 não implementado; integração ADN produtiva exige certificado autorizado e homologação.
