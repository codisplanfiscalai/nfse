# Relatórios fiscais

Modelos funcionais baseados nos quatro PDFs apresentados pelo usuário.

| Relatório | Seleção | Exportação |
|---|---|---|
| Emissão mensal (`mensal`) | Emissão entre data inicial e final | PDF, XLSX, CSV, JSON |
| Competência (`competencia`) | Competência da prestação | PDF, XLSX, CSV, JSON |
| ISS retido (`iss-retido`) | ISS retido positivo no período | PDF, XLSX, CSV, JSON |
| Canceladas (`canceladas`) | Canceladas e substituídas no período | PDF, XLSX, CSV, JSON |

Os relatórios incluem identificação da empresa/tomador, data de emissão, competência, número, serviço, valor bruto/líquido, ISS, retenções, situação e chave. O Excel inclui abas por tomador, serviço, competência e resumo. O XML integral continua disponível no banco para auditoria. Os valores de notas canceladas e substituídas **não compõem os totais vigentes**.

**Atenção:** valores fiscais são derivados exclusivamente dos campos efetivamente presentes nos XMLs; não calcular ISS retido presumido a partir da alíquota ou do ISS próprio. É necessário confirmar integralidade da sequência NSU e documentos antes do fechamento do período.
