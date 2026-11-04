# Fluxo Git, SemVer e distribuição

## Contrato

1. `feat/...` / `fix/...` / `ci/...` -> Pull Request para `develop`; validações Python 3.10/3.12/3.13, actionlint, Vue responsivo, Windows GUI x86/x64 e Docker.
2. Merge validado em `develop` -> `0.2.0-dev.<github.run_number>.<github.run_attempt>`; produção dos artefatos nativos em runners Windows, leitura de manifests, verificação SHA-256 e testes de fumaça nativos.
3. Release automatizada **somente** depois da aprovação de `tests`, `windows` e `container`. Tags imutáveis, sem sobrescrever artefatos do mesmo número.
4. PR `release(minor): ...` de `develop` para `main` -> versão `0.2.0` estável. Novo ciclo requer alteração coordenada de `VERSION` e `pyproject.toml`.
5. Docker GHCR com digest, rótulos de versão e commit idênticos aos artefatos publicados. Caches temporários podem ser limpos com workflow de simulação/aplicação restrita.

## Integridade dos artefatos

Cada ZIP Windows contém executável GUI sem console, serviço Windows separado, `manifest.json`, diretório `_internal` e marca Codisplan. Arquivos `.sha256` e manifestos são publicados ao lado dos ZIPs; na pré-release e release, o pipeline não recompila binários. Falha de compilação, teste ou checksum interrompe publicação.

## Dependências

Pacotes diretos possuem versões fixadas. O projeto ainda requer um lock de dependências indiretas por arquitetura/OS, com hashes e processo automatizado de revisão de segurança, antes da classificação de release como homologada para produção.
