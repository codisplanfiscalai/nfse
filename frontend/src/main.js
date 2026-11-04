import { createApp, ref, computed, onMounted, watch } from 'vue/dist/vue.esm-bundler.js'
import './style.css'

const apiRoot = '/api'

createApp({
  setup() {
    const token = ref(''), username = ref(''), setupRequired = ref(false), authName = ref('admin'), authPassword = ref(''),
      mode = ref('loading'), tab = ref('dashboard'), feedback = ref(''), loading = ref(false),
      companies = ref([]), certificates = ref([]), jobs = ref([]), documents = ref([]), auditRows = ref([]), info = ref({}),
      selectedCompany = ref(''), companyName=ref(''), companyTaxId=ref(''), companyEnv=ref('restrita'),
      certLabel=ref(''), certPassword=ref(''), certFile=ref(null), assignedCert=ref(''),
      nsu=ref(0), lote=ref(true), importQuery=ref(true), queryTaxId=ref(''), queryCpf=ref(''), eventKey=ref(''), adnOutput=ref(null),
      periodStart=ref(new Date(new Date().getFullYear(),new Date().getMonth(),1).toISOString().slice(0,10)),
      periodEnd=ref(new Date().toISOString().slice(0,10)), basis=ref('issued'), reportKind=ref('mensal'),
      reportCustomer=ref(''), reportRows=ref([]), reportSummary=ref(null)

    const current = computed(()=>companies.value.find(c=>String(c.id)===String(selectedCompany.value)))
    const nav = [
      ['dashboard','Visão geral'],['companies','Empresas'],['certificates','Certificados A1'],
      ['reports','Relatórios fiscais'],['documents','Documentos XML'],['adn','Consultas ADN'],
      ['audit','Auditoria'],['settings','Configurações']
    ]
    const kinds = [['mensal','Emitidas - Emissão'],['competencia','Emitidas - Competência'],
      ['iss_retido','ISS retido'],['canceladas','Canceladas / substituídas']]
    const currency=(n)=>'R$ '+(n||'0,00')
    function note(message,error=false) { feedback.value=(error?'Erro: ':'')+message; setTimeout(()=>{ if(feedback.value.endsWith(message)) feedback.value=''},6500) }
    async function call(path, opts={}) {
      const headers={...(opts.headers||{})}
      if(token.value) headers.Authorization='Bearer '+token.value
      if(opts.body && !(opts.body instanceof FormData)) headers['Content-Type']='application/json'
      const resp=await fetch(apiRoot+path,{...opts,headers})
      if(opts.raw) {if(!resp.ok)throw new Error((await resp.json().catch(()=>({}))).detail||'Erro HTTP '+resp.status);return resp}
      const result=await resp.json().catch(()=>({}))
      if(!resp.ok){if(resp.status===401 && token.value){mode.value='login';token.value=''}throw new Error(result.detail||result.message||'Erro HTTP '+resp.status)}
      return result
    }
    function refreshPage(){window.location.reload()}
    async function init(){
      try{const x=await call('/bootstrap/status'); setupRequired.value=x.needs_setup;mode.value=x.needs_setup?'setup':'login'}
      catch(e){mode.value='offline';note('Serviço não está acessível: '+e.message,true)}
    }
    async function signin(){
      try{
        loading.value=true
        if(mode.value==='setup'){
          await call('/bootstrap',{method:'POST',body:JSON.stringify({username:authName.value,password:authPassword.value})})
        }
        const x=await call('/auth/login',{method:'POST',body:JSON.stringify({username:authName.value,password:authPassword.value})})
        token.value=x.token;username.value=x.user;authPassword.value='';mode.value='app';await refresh()
      }catch(e){note(e.message,true)}finally{loading.value=false}
    }
    async function signout(){try{await call('/auth/logout',{method:'POST'})}catch{}token.value='';mode.value='login'}
    async function refresh(){
      try{
        [companies.value,certificates.value,info.value]=await Promise.all([call('/companies'),call('/certificates'),call('/info')]);
        if(companies.value.length && !current.value)selectedCompany.value=String(companies.value[0].id)
      }catch(e){note(e.message,true)}
    }
    async function createCompany(){
      try{await call('/companies',{method:'POST',body:JSON.stringify({name:companyName.value,tax_id:companyTaxId.value,environment:companyEnv.value})});companyName.value='';companyTaxId.value='';note('Empresa cadastrada');await refresh()}
      catch(e){note(e.message,true)}
    }
    async function uploadCert(){
      if(!certFile.value){note('Selecione um arquivo .pfx ou .p12',true);return}
      try{
        const form=new FormData();form.append('file',certFile.value);form.append('label',certLabel.value);form.append('password',certPassword.value)
        await call('/certificates',{method:'POST',body:form});certPassword.value='';certLabel.value='';certFile.value=null;
        note('Certificado incluído com sucesso');await refresh()
      }catch(e){note(e.message,true)}
    }
    async function linkCertificate(){
      try{if(!selectedCompany.value)throw new Error('Selecione uma empresa')
        await call(`/companies/${selectedCompany.value}/certificate`,{method:'POST',body:JSON.stringify({cert_id:assignedCert.value?Number(assignedCert.value):null})})
        note('Certificado vinculado');await refresh()
      }catch(e){note(e.message,true)}
    }
    async function syncCompany(){
      try{
        if(!selectedCompany.value)throw new Error('Selecione uma empresa')
        const r=await call(`/companies/${selectedCompany.value}/sync`,{method:'POST'})
        note(r.scheduled?'Sincronização iniciada em segundo plano':r.detail);if(r.job_id)jobs.value.unshift(r.job_id)
        await refresh()
      }catch(e){note(e.message,true)}
    }
    async function updateJobs(){
      try{for(const id of jobs.value){const x=await call('/jobs/'+id);if(x.state!=='executando'){note(x.state==='ok'?`Sincronização concluída: ${x.imported} documentos`:'Falha: '+x.error,x.state!=='ok');jobs.value=jobs.value.filter(v=>v!==id);await refresh()}}}
      catch(e){note(e.message,true)}
    }
    async function loadReport(){
      try{
        if(!selectedCompany.value)throw new Error('Selecione uma empresa')
        loading.value=true;const query=new URLSearchParams({start:periodStart.value,end:periodEnd.value,basis:basis.value,kind:reportKind.value,format:'json'})
        if(reportCustomer.value)query.set('customer',reportCustomer.value)
        const r=await call(`/companies/${selectedCompany.value}/reports?${query}`)
        reportRows.value=r.items;reportSummary.value=r.summary;note('Relatório carregado')
      }catch(e){note(e.message,true)}finally{loading.value=false}
    }
    async function exportReport(format){
      try{
        if(!selectedCompany.value)throw new Error('Selecione uma empresa')
        const query=new URLSearchParams({start:periodStart.value,end:periodEnd.value,basis:basis.value,kind:reportKind.value,format})
        if(reportCustomer.value)query.set('customer',reportCustomer.value)
        const response=await call(`/companies/${selectedCompany.value}/reports?${query}`,{raw:true})
        const blob=await response.blob(),url=URL.createObjectURL(blob),a=document.createElement('a')
        a.href=url;a.download=`nfse_${reportKind.value}_${periodStart.value}_${periodEnd.value}.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1500)
      }catch(e){note(e.message,true)}
    }
    async function loadDocuments(){try{
      if(!selectedCompany.value)throw new Error('Selecione uma empresa')
      documents.value=await call(`/companies/${selectedCompany.value}/documents?limit=150`)
    }catch(e){note(e.message,true)}}
    async function downloadXml(document){try{
      const res=await call(`/companies/${selectedCompany.value}/documents/${document.id}/xml`,{raw:true})
      const url=URL.createObjectURL(await res.blob()),a=document.createElement('a');a.href=url;a.download='nfse_'+document.id+'.xml';a.click();setTimeout(()=>URL.revokeObjectURL(url),1500)
    }catch(e){note(e.message,true)}}
    async function remoteNsu(){try{
      const qs=new URLSearchParams({nsu:nsu.value,lote:lote.value,importar:importQuery.value})
      if(queryTaxId.value) qs.set('cnpjConsulta',queryTaxId.value)
      if(queryCpf.value) qs.set('cpfConsulta',queryCpf.value)
      adnOutput.value=await call(`/companies/${selectedCompany.value}/adn/nsu?${qs}`,{method:'POST'});note('Consulta NSU concluída')
    }catch(e){note(e.message,true)}}
    async function remoteEvents(){try{
      adnOutput.value=await call(`/companies/${selectedCompany.value}/adn/events/${eventKey.value}?importar=${importQuery.value}`,{method:'POST'});note('Consulta eventos concluída')
    }catch(e){note(e.message,true)}}
    async function loadAudit(){try{auditRows.value=await call('/audit')}catch(e){note(e.message,true)}}
    function switchTab(t){tab.value=t;if(t==='documents')loadDocuments();if(t==='audit')loadAudit();if(t==='dashboard')refresh()}
    watch(reportKind,(v)=>{basis.value=v==='competencia'?'competence':'issued'})
    watch(selectedCompany,()=>{assignedCert.value=current.value?.cert_id?String(current.value.cert_id):'';reportSummary.value=null;reportRows.value=[]})
    onMounted(()=>{init();setInterval(()=>{if(mode.value==='app'&&jobs.value.length)updateJobs()},4000)})
    return {mode,tab,nav,kinds,feedback,loading,setupRequired,username,authName,authPassword,
       companies,certificates,selectedCompany,current,companyName,companyTaxId,companyEnv,
       certLabel,certPassword,certFile,assignedCert,nsu,lote,importQuery,queryTaxId,queryCpf,eventKey,adnOutput,
       periodStart,periodEnd,basis,reportKind,reportCustomer,reportRows,reportSummary,documents,auditRows,info,
       signin,signout,refresh,refreshPage,createCompany,uploadCert,linkCertificate,syncCompany,loadReport,exportReport,
       loadDocuments,downloadXml,remoteNsu,remoteEvents,loadAudit,switchTab,currency}
  },
  template: `
  <div v-if="mode==='loading'" class="login-page"><div class="auth-card"><h2>Codisplan NFS-e</h2><p>Iniciando painel...</p></div></div>
  <div v-else-if="mode==='offline'" class="login-page"><div class="auth-card"><h2>Serviço indisponível</h2><p>Abra o aplicativo Codisplan pela área de notificação do Windows para iniciar ou verificar o serviço.</p><button class="primary" @click="refreshPage">Tentar novamente</button></div></div>
  <div v-else-if="mode!=='app'" class="login-page"><div class="auth-card">
    <div class="brand-icon"><img src="/logo-mark.png" alt="Logomarca Codisplan" /></div><h1>Codisplan NFS-e</h1><p>{{mode==='setup'?'Configure seu primeiro usuário administrador':'Painel administrativo e fiscal'}}</p>
    <form @submit.prevent="signin"><label>Usuário</label><input v-model="authName" autocomplete="username" required minlength="3"/>
      <label>Senha {{mode==='setup'?'(mínimo 12 caracteres)':''}}</label><input v-model="authPassword" type="password" autocomplete="current-password" required :minlength="mode==='setup'?12:1"/>
      <button class="primary full" :disabled="loading">{{mode==='setup'?'Criar administrador':'Entrar no painel'}}</button></form>
    <small>Conexão local • Certificados e XMLs protegidos</small></div></div>
  <div v-else class="shell">
    <aside class="sidebar"><div class="brand"><div class="brand-icon"><img src="/logo-mark.png" alt="Logomarca Codisplan" /></div><div><strong>CODISPLAN</strong><span>Gestão NFS-e</span></div></div>
      <div class="nav-label">ADMINISTRAÇÃO</div>
      <button v-for="item in nav" :key="item[0]" :class="['nav-item',tab===item[0]?'active':'']" @click="switchTab(item[0])">{{item[1]}}</button>
      <div class="sidebar-footer"><div class="online-dot">Serviço conectado</div><small>v0.1.0 • Python + Vue</small></div>
    </aside>
    <main class="main"><header class="topbar"><div><b>Central NFS-e</b><span>Ambiente de distribuição fiscal</span></div><div class="userbox">{{username}} <button class="quiet" @click="signout">Sair</button></div></header>
      <div class="content"><div v-if="feedback" class="toast">{{feedback}}</div>
      <div class="section-head"><div><h2>{{nav.find(n=>n[0]===tab)?.[1]}}</h2><p>Controle de empresas, documentos fiscais e sincronização nacional.</p></div>
        <button v-if="tab!=='settings'" class="outline" @click="refresh">Atualizar</button></div>

      <template v-if="tab==='dashboard'">
        <div class="metrics"><div class="metric"><small>Empresas cadastradas</small><strong>{{companies.length}}</strong><span>Documentos fiscais nacionais</span></div>
          <div class="metric"><small>Certificados A1</small><strong>{{certificates.length}}</strong><span>Armazenamento criptografado</span></div>
          <div class="metric"><small>Empresas com certificado</small><strong>{{companies.filter(c=>c.cert_id).length}}</strong><span>Habilitadas para sincronizar</span></div></div>
        <div class="card"><div class="card-title"><h3>Empresas monitoradas</h3><button class="outline small" @click="switchTab('companies')">Gerenciar empresas</button></div>
          <div class="table-wrap"><table><thead><tr><th>Empresa</th><th>CPF/CNPJ</th><th>Ambiente</th><th>Último NSU</th><th>Situação</th></tr></thead>
          <tbody><tr v-for="c in companies" :key="c.id"><td><strong>{{c.name}}</strong></td><td>{{c.tax_id}}</td><td>{{c.environment}}</td><td>{{c.nsu||0}}</td>
            <td><span class="status" :class="c.sync_status==='erro'?'bad':''">{{c.sync_status||'nunca'}}</span></td></tr><tr v-if="!companies.length"><td colspan="5">Cadastre sua primeira empresa para iniciar.</td></tr></tbody></table></div></div>
      </template>

      <template v-else-if="tab==='companies'"><div class="cols2">
        <div class="card"><h3>Cadastrar empresa</h3><form @submit.prevent="createCompany" class="stack"><label>Razão social</label><input v-model="companyName" required placeholder="Nome da empresa"/><label>CPF ou CNPJ</label><input v-model="companyTaxId" required placeholder="Somente números"/>
          <label>Ambiente ADN</label><select v-model="companyEnv"><option value="restrita">Produção restrita (testes)</option><option value="producao">Produção</option></select><button class="primary">Cadastrar empresa</button></form></div>
        <div class="card"><h3>Sincronizar documentos</h3><div class="stack"><label>Empresa</label><select v-model="selectedCompany"><option v-for="c in companies" :value="String(c.id)" :key="c.id">{{c.name}}</option></select>
          <p class="small-muted">Cursor NSU: {{current?.nsu||0}}<br/>Última consulta: {{current?.last_sync||'Nunca'}}<br/>Status: {{current?.sync_status||'nunca'}}</p>
          <label>Certificado da empresa</label><select v-model="assignedCert"><option value="">Não vinculado</option><option v-for="c in certificates" :key="c.id" :value="String(c.id)">{{c.label}} — validade {{c.expires_at?.slice(0,10)}}</option></select>
          <button class="outline" @click="linkCertificate">Vincular certificado</button><button class="primary" @click="syncCompany">Sincronizar agora</button></div></div></div>
        <div class="card"><h3>Cadastro atual</h3><div class="table-wrap"><table><thead><tr><th>Empresa</th><th>CPF/CNPJ</th><th>Certificado</th><th>NSU</th><th>Situação</th></tr></thead>
          <tbody><tr v-for="c in companies" :key="c.id"><td>{{c.name}}</td><td>{{c.tax_id}}</td><td>{{c.certificate_label||'—'}}</td><td>{{c.nsu||0}}</td><td>{{c.sync_status||'nunca'}}</td></tr></tbody></table></div></div>
      </template>

      <template v-else-if="tab==='certificates'"><div class="cols2"><div class="card"><h3>Importar certificado digital A1</h3><form class="stack" @submit.prevent="uploadCert"><label>Identificação</label><input v-model="certLabel" required placeholder="Certificado escritório / empresa"/>
        <label>Arquivo PFX/P12</label><input type="file" accept=".pfx,.p12" @change="certFile=$event.target.files[0]" required/><label>Senha do certificado</label><input type="password" v-model="certPassword" required autocomplete="off"/>
        <button class="primary">Importar certificado</button></form><p class="small-muted">Certificado e senha armazenados criptografados. Nunca são registrados nos logs.</p></div>
        <div class="card"><h3>Certificados disponíveis</h3><div v-for="c in certificates" :key="c.id" class="cert-row"><b>{{c.label}}</b><span>Validade: {{c.expires_at?.slice(0,10)}}</span><small>{{c.fingerprint?.slice(0,28)}}...</small></div><p v-if="!certificates.length">Nenhum certificado cadastrado.</p></div></div>
        <div class="advice">Certificados A3 exigem o provedor criptográfico do dispositivo (CSP/PKCS#11). Esta versão inclui importação A1 em PFX/P12; não solicita PIN de A3.</div>
      </template>

      <template v-else-if="tab==='reports'"><div class="card"><h3>Parâmetros de relatório</h3><div class="filters">
        <div><label>Empresa</label><select v-model="selectedCompany"><option v-for="c in companies" :value="String(c.id)">{{c.name}}</option></select></div>
        <div><label>Data inicial</label><input type="date" v-model="periodStart"/></div><div><label>Data final</label><input type="date" v-model="periodEnd"/></div>
        <div><label>Base de seleção</label><select v-model="basis"><option value="issued">Emissão</option><option value="competence">Competência</option></select></div>
        <div><label>Modelo</label><select v-model="reportKind"><option v-for="k in kinds" :value="k[0]">{{k[1]}}</option></select></div>
        <div><label>Tomador (opcional)</label><input v-model="reportCustomer" placeholder="CPF/CNPJ"/></div>
      </div><div class="actions"><button class="primary" @click="loadReport" :disabled="loading">Consultar</button><button class="outline" @click="exportReport('pdf')">Exportar PDF</button><button class="outline" @click="exportReport('xlsx')">Exportar Excel</button><button class="outline" @click="exportReport('csv')">Exportar CSV</button></div></div>
      <template v-if="reportSummary"><div class="metrics"><div class="metric"><small>Notas</small><strong>{{reportSummary.count}}</strong></div><div class="metric"><small>Valor dos serviços</small><strong class="money">{{currency(reportSummary.totals.amount_cents)}}</strong></div><div class="metric"><small>ISS apurado</small><strong class="money">{{currency(reportSummary.totals.iss_cents)}}</strong></div></div>
      <div class="card"><h3>Notas do período</h3><div class="table-wrap"><table><thead><tr><th>Data emissão</th><th>Competência</th><th>NFS-e</th><th>Tomador</th><th>Serviços</th><th>ISS</th><th>Situação</th></tr></thead>
      <tbody><tr v-for="r in reportRows" :key="r.access_key"><td>{{r.issued_at}}</td><td>{{r.competence}}</td><td>{{r.number}}</td><td>{{r.customer_name}}</td><td>{{currency(r.amount_cents)}}</td><td>{{currency(r.iss_cents)}}</td><td>{{r.status}}</td></tr>
      <tr v-if="!reportRows.length"><td colspan="7">Nenhuma nota encontrada para os filtros selecionados.</td></tr></tbody></table></div></div></template>
      </template>

      <template v-else-if="tab==='documents'"><div class="card"><div class="card-title"><h3>XMLs armazenados</h3><div class="actions"><select v-model="selectedCompany"><option v-for="c in companies" :value="String(c.id)">{{c.name}}</option></select><button class="outline" @click="loadDocuments">Atualizar</button></div></div>
      <div class="table-wrap"><table><thead><tr><th>NSU</th><th>Tipo</th><th>Evento</th><th>Chave de acesso</th><th>XML</th></tr></thead>
      <tbody><tr v-for="d in documents" :key="d.id"><td>{{d.nsu}}</td><td>{{d.doc_type}}</td><td>{{d.event_type||'—'}}</td><td class="mono">{{d.access_key}}</td><td><button class="outline small" @click="downloadXml(d)">Baixar</button></td></tr></tbody></table></div></div></template>

      <template v-else-if="tab==='adn'"><div class="cols2"><div class="card"><h3>Distribuição por NSU</h3><div class="stack"><label>Empresa</label><select v-model="selectedCompany"><option v-for="c in companies" :value="String(c.id)">{{c.name}}</option></select>
       <label>NSU</label><input type="number" min="0" v-model.number="nsu"/><label>CNPJ de consulta (opcional)</label><input v-model="queryTaxId" placeholder="CNPJ completo"/>
       <label>CPF de consulta (opcional)</label><input v-model="queryCpf" placeholder="CPF"/><label class="checkbox"><input type="checkbox" v-model="lote"/>Consultar em lote</label>
       <label class="checkbox"><input type="checkbox" v-model="importQuery"/>Armazenar documentos retornados</label><button class="primary" @click="remoteNsu">Consultar NSU no ADN</button></div></div>
       <div class="card"><h3>Eventos por chave de acesso</h3><div class="stack"><label>Chave NFS-e (50 dígitos)</label><input v-model="eventKey" placeholder="Chave de acesso"/>
       <button class="primary" @click="remoteEvents">Consultar eventos no ADN</button><p class="small-muted">Consulta diretamente o ambiente indicado no cadastro da empresa, via certificado digital mTLS.</p></div></div></div>
       <div v-if="adnOutput" class="card"><h3>Resposta da consulta</h3><pre class="json">{{JSON.stringify(adnOutput,null,2)}}</pre></div></template>

      <template v-else-if="tab==='audit'"><div class="card"><h3>Histórico de operações</h3><div class="table-wrap"><table><thead><tr><th>Data</th><th>Usuário</th><th>Operação</th><th>Detalhes</th></tr></thead>
       <tbody><tr v-for="(r,i) in auditRows" :key="i"><td>{{r.created_at}}</td><td>{{r.actor}}</td><td>{{r.action}}</td><td>{{r.details}}</td></tr></tbody></table></div></div></template>

      <template v-else-if="tab==='settings'"><div class="card"><h3>Informações do ambiente</h3><div class="setting-row"><span>Versão</span><b>{{info.version}}</b></div>
       <div class="setting-row"><span>Diretório de dados</span><b>{{info.data_path}}</b></div>
       <div class="setting-row"><span>API local</span><b>Protegida por usuário e sessão</b></div>
       <div class="setting-row"><span>Integração oficial</span><b>Distribuição NSU + eventos por chave</b></div>
       <div class="advice">A instalação e o controle do Serviço Windows são feitos pela janela do aplicativo e pelo ícone na bandeja do Windows. O serviço funciona independentemente deste painel.</div></div></template>
      </div>
    </main>
  </div>`
}).mount('#app')
