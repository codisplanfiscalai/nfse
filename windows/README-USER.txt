CODISPLAN NFS-e - APLICATIVO WINDOWS

1. Abra CodisplanNFSe.exe com duplo clique.
2. Na faixa superior, clique em "Instalar" para registrar o Servico Windows (confirme UAC).
3. O painel administrativo aparece na mesma janela; crie o usuario administrador na primeira abertura.
4. Na aba Certificados A1, importe um PFX/P12 e informe a senha.
5. Cadastre a empresa, associe o certificado e selecione Sincronizar agora.
6. Na aba Relatorios fiscais, escolha a empresa, o periodo e o modelo. Exporte em PDF, Excel ou CSV.
7. Fechar a janela apenas minimiza para a area de notificacao. O Windows Service funciona independentemente.
8. Para abrir novamente, clique duas vezes no icone da area de notificacao do Windows.

Nao e necessario abrir terminal, Prompt, PowerShell, executar comandos ou editar arquivos .env.

OBSERVACOES:
- O EXE e gerado pelo fluxo automatico Windows no GitHub Actions; Windows nao executa PyInstaller Linux.
- Certificado A1 suportado. Certificado A3 requer implementacao de provedor CSP/PKCS#11.
- Para empresas de terceiros, ha necessidade de representacao/procuracao autorizada no portal competente.
- Nao exponha a porta 8765 diretamente na Internet ou rede sem proxy HTTPS.
