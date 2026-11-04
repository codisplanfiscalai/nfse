# Codisplan NFS-e — API Python + GUI Windows + painel Vue 3

Sistema próprio de consulta do **ADN NFS-e**, armazenamento de documentos e eventos e emissão de quatro demonstrativos fiscais.

**O usuário opera tudo na interface gráfica: não há procedimento por terminal para baixar notas ou gerar relatórios.**

## Aplicação Windows

Na página **Releases** do repositório GitHub, baixe `CodisplanNFSe-Windows-x64.zip`, extraia e abra `CodisplanNFSe.exe` com duplo clique. A janela tem botões para instalar, iniciar, parar, reiniciar ou remover o Serviço Windows (UAC solicita permissão administrativa). Ao fechar, o aplicativo fica na bandeja. O serviço autônomo pode continuar mesmo se o usuário sair da interface.

Fluxo inicial: definir administrador → importar certificado A1 PFX/P12 → cadastrar empresa → vincular certificado → sincronizar → escolher período → gerar PDF/Excel/CSV. O servidor local é iniciado automaticamente se o serviço não estiver instalado; após instalar o serviço, ele assume a execução.

## Painel administrativo Vue 3

Visão geral, empresas, certificados, relatórios, XMLs, consultas do ADN, auditoria e configurações. Recursos acessados diretamente na janela nativa ou em `http://127.0.0.1:8765` no computador local. A interface não depende de CDN depois de compilada.

## API oficial implementada

- `GET /DFe/{NSU}`: lote, documento único, `cnpjConsulta`, `cpfConsulta`, procuração e CNPJ base (autorização avaliada pelo ADN).
- `GET /NFSe/{ChaveAcesso}/Eventos`: eventos por chave de acesso.
- mTLS com certificado **A1** em PKCS#12/PFX, TLS 1.2+, validação da cadeia do servidor.
- GZip/Base64, XML seguro, dados originais criptografados, cursor NSU idempotente, eventos e cancelamentos.
- Documentos: NFSE, EVENTO, DPS, CNC, PEDIDO_REGISTRO_EVENTO: todos armazenados. A normalização fiscal é aplicada a NFSE.

## Relatórios disponíveis

| Nome no painel | Base padrão | Filtro |
|---|---|---|
| Emitidas - Emissão | emissão | NFS-e autorizadas de serviços prestados |
| Emitidas - Competência | competência | NFS-e autorizadas de serviços prestados |
| ISS retido | emissão | Prestadas com indicador de retenção do ISS |
| Canceladas/substituídas | emissão | Prestadas com cancelamento ou substituição efetiva |

PDF A3 horizontal (repetição de cabeçalho em cada página), Excel com abas de tomador, serviço, competência, CSV e JSON.
Os valores exibidos são extraídos dos XMLs. PIS/Cofins/CSLL retidos não são separados por inferência quando constam consolidados em `vRetCSLL`. ISS retido é informado pelo indicador documental, não calculado presumidamente sobre imposto apurado.

## Segurança

- API administrativa exige login. Primeiro acesso cria administrador local (senha com no mínimo 12 caracteres).
- PFX e senha criptografados em repouso. No Windows, chave protegida por DPAPI e pasta com ACL de SYSTEM/Administrators após instalação.
- Sem certificado de teste distribuído, sem senhas padrão; nenhuma rota pública de consulta fiscal.
- O servidor Windows escuta em `127.0.0.1`. Não exponha porta 8765 externamente sem reverse proxy TLS, controle de acesso e revisão de segurança.
- No Linux/Docker, use `CODISPLAN_MASTER_KEY` em secret manager e volume persistente. A imagem Docker é uma opção **separada** do aplicativo Windows.
- Certificado **A3 ainda não implementado**: a camada de hardware CSP/PKCS#11 exige integração específica, e não equivale a importar PFX.

## Publicação em repositório novo

Este projeto deve ser publicado em um repositório **exclusivo da API NFS-e**, sem misturar com outros sistemas fiscais. Primeiro crie o repositório vazio no GitHub; publique `main` e `develop` com o conteúdo integral deste pacote. Um push para `develop` acionará o GitHub Actions e produzirá o pacote `CodisplanNFSe-Windows-x64.zip` no ambiente Windows x64. Só declare o `.exe` pronto após o workflow terminar e o binário ser validado.

## Desenvolvimento, branches e versões

`main`: releases estáveis em tags `vMAJOR.MINOR.PATCH`. `develop`: pré-releases contínuos `vMAJOR.MINOR.PATCH-dev.RUN_NUMBER`. O arquivo `VERSION` segue SemVer. GitHub Actions compila frontend, executa testes, gera ZIP Windows e publica release automaticamente. Imagem Docker é publicada no GHCR para as branches e tags.

Este pacote contém **código-fonte com identidade visual original da Codisplan**, não um `.exe` Windows já compilado: o executável depende de PyInstaller rodando no próprio Windows (fluxo de GitHub Actions incluído).

## Estado de homologação

Testes automáticos com XML sintético e simulação de respostas ADN; comunicação real mTLS e dispositivo A3 não foram homologados com certificado de contribuinte. A distribuição do ADN depende de acesso autorizado e de ambiente com certificado válido. O caminho base de produção e restrita segue a documentação oficial e o Swagger fornecido.

Fonte: <https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual>

## Identidade visual

A logomarca original fornecida pela Codisplan foi utilizada para gerar `assets/app.ico` (Windows EXE e tray), `assets/app.png` e `frontend/public/logo-mark.png`. O projeto também inclui `assets/codisplan_logo_original.jpg` como referência. Nenhum ícone substituto genérico foi empregado.

**Importante:** este pacote não é um binário instalado ou compilado; a compilação nativa do Windows deve ocorrer em um runner Windows.
