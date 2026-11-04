# Arquitetura funcional

- **`src/nfse/adn.py`**: cliente HTTPS/mTLS do ADN, valida domínio oficial e os dois endpoints Swagger, não segue redirecionamentos.
- **`src/nfse/certificates.py`**: PFX/P12 ICP-Brasil A1, chave local criptografada, SSLContext mTLS com materiais temporários restritos.
- **`src/nfse/xml_documents.py`**: XML seguro (defusedxml), normalização por identificador/competência/serviço/imposto/eventos; não inventa retenções fiscais.
- **`src/nfse/store.py`**: SQLite local privado, registros originais, hash, índices, transações e cursor por empresa e certificado.
- **`src/nfse/sync.py`**: distribuição em lote, tratamento de NSU, reprocessamento idempotente, cursor separado das consultas avulsas; erros oficializados preservados.
- **`src/nfse/reports.py`**: PDF/Excel/CSV, valores internos em centavos, cancelamentos segregados dos totais vigentes.
- **`src/nfse/api.py`**: rotas REST autenticadas, cookie HttpOnly com CSRF para portal, bearer para integrações, auditoria e permissões.
- **`src/nfse/portal/`**: frontend Vue 3 precompilado localmente; menus adaptáveis 1440px e 390px; identidade visual Codisplan.
- **`desktop/` + `packaging/`**: Tk GUI e ícone Win32 Tray no processo de usuário; Windows Service separado, usando 127.0.0.1.

### Segurança

A configuração inicial só pode ser realizada a partir de localhost. O serviço escuta apenas `127.0.0.1` por padrão. Não exponha esse servidor diretamente pela rede; use proxy HTTPS com autenticação/rede adequada. A senha PFX é criptografada localmente, não enviada a serviços de terceiros. Em ambientes multiusuário, configure ACL apropriadas em ProgramData para limitar o acesso a chaves/DB e usuários de serviço. Os relatórios e o banco não substituem documentos ou escrituração exigidos pela legislação.

### Referência oficial

O contrato do usuário foi preservado em `docs/swagger-adn.json`. O Swagger não contém URL `servers`; configure a URL publicada pela autoridade responsável e valide certificado/autorizações do contribuinte. Erros esperados incluem E2210–E2214 (certificado), E2220, E2230, E2240, E2241 e E2243–E2247 (distribuição/autorização).
