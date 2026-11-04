# Operação exclusivamente por interface gráfica

## Inicialização Windows

O executável `CodisplanNFSe.exe` abre a janela gráfica. O servidor Python pode ser executado como processo local temporário no primeiro acesso. O botão **Instalar** registra o Windows Service com inicialização automática (mediante UAC); ele fica independente da janela.

O ícone na área de notificação permite reabrir o painel, iniciar/reiniciar serviço ou sair da interface. Fechar a janela apenas a oculta.

## Primeiro acesso

1. Informe nome de usuário e uma senha de pelo menos 12 caracteres.
2. Em **Certificados A1**, escolha o arquivo PFX/P12 e informe a senha no formulário.
3. Em **Empresas**, cadastre razão social e CPF/CNPJ.
4. Associe o certificado na mesma tela. Para consultar terceiros, é necessária autorização/procuração oficial.
5. Clique em **Sincronizar agora**. O cursor NSU fica salvo por empresa e o serviço verifica atualizações periodicamente.
6. Em **Relatórios fiscais**, selecione empresa, intervalo, tipo de data (emissão/competência), modelo e formato de exportação.

## Menu

- **Visão geral:** situação de sincronização, NSU, certificados e empresas.
- **Empresas:** cadastro, associação de certificado e sincronização em segundo plano.
- **Certificados A1:** importação PFX/P12, validade e identificação (a chave privada não é exposta).
- **Relatórios fiscais:** quatro modelos (emitidas, competência, ISS retido e canceladas), PDF/Excel/CSV.
- **Documentos XML:** relação de documentos sincronizados e download autenticado do XML original.
- **Consultas ADN:** NSU, lote, CNPJ/CPF consultado, consulta de eventos por chave e armazenamento opcional.
- **Auditoria:** quem acionou consultas, downloads e relatórios.
- **Configurações:** versão e diretório de dados, notas de segurança.

## Importante

A autenticação oficial é com certificado A1 e mTLS. Certificados A3 não são importáveis diretamente em PFX e dependem do fornecedor CSP/PKCS#11. Não há login genérico que substitua a representação autorizada no ADN.

A geração de relatório é realizada com base nos documentos XML efetivamente sincronizados e nos eventos que mudam a situação da NFS-e. Nenhum relatório afirma ser uma conciliação completa com portais municipais sem integração adicional.
