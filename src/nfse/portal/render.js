/* Vue 3 - template compilado offline */
var _Vue=Vue; var NFSeRender=function render(_ctx, _cache) {
  with (_ctx) {
    const { createElementVNode: _createElementVNode, createTextVNode: _createTextVNode, toDisplayString: _toDisplayString, vModelText: _vModelText, withDirectives: _withDirectives, openBlock: _openBlock, createElementBlock: _createElementBlock, createCommentVNode: _createCommentVNode, withModifiers: _withModifiers, renderList: _renderList, Fragment: _Fragment, normalizeClass: _normalizeClass, vModelSelect: _vModelSelect } = _Vue

    return (_openBlock(), _createElementBlock("div", { class: _normalizeClass(["shell", {signed:user}]) }, [(!user)
      ? (_openBlock(), _createElementBlock("div", {
          key: 0,
          class: "auth-layout"
        }, [_createElementVNode("aside", { class: "auth-side" }, [_createElementVNode("div", { class: "auth-brand" }, [_createElementVNode("img", {
          src: "/static/app.png",
          alt: "",
          class: "auth-icon"
        }), _createElementVNode("span", null, [_createElementVNode("strong", null, "NFS-e"), _createTextVNode(" Codisplan")])]), _createElementVNode("div", { class: "auth-message" }, [
          _createElementVNode("p", { class: "eyebrow light" }, "PLATAFORMA FISCAL"),
          _createElementVNode("h1", null, "Documentos e relatórios. Em um só lugar."),
          _createElementVNode("p", null, "Sincronize documentos pelo Ambiente de Dados Nacional, acompanhe eventos e transforme XMLs em relatórios confiáveis."),
          _createElementVNode("div", { class: "auth-features" }, [_createElementVNode("span", null, "◈ Integração com certificado digital"), _createElementVNode("span", null, "◈ Histórico fiscal rastreável"), _createElementVNode("span", null, "◈ Relatórios por competência")])
        ]), _createElementVNode("div", { class: "auth-bottom" }, "CODISPLAN · TECNOLOGIA PARA CONTABILIDADE")]), _createElementVNode("main", { class: "auth-main" }, [_createElementVNode("section", { class: "auth-card" }, [
          _createElementVNode("img", {
            src: "/static/brand-lockup.png",
            alt: "Codisplan NFS-e",
            class: "login-logo"
          }),
          _createElementVNode("p", { class: "eyebrow" }, "ACESSO SEGURO"),
          _createElementVNode("h2", null, _toDisplayString(configured?'Entrar no painel':'Configurar administrador'), 1),
          _createElementVNode("p", { class: "muted" }, _toDisplayString(configured?'Use suas credenciais de acesso à plataforma.':'Primeiro acesso: crie o administrador local.'), 1),
          _createElementVNode("form", {
            onSubmit: _withModifiers(submitAuth, ["prevent"]),
            class: "stack"
          }, [
            (!configured)
              ? (_openBlock(), _createElementBlock("label", {
                  key: 0,
                  class: "field"
                }, [_createTextVNode("Nome completo"), _withDirectives(_createElementVNode("input", {
                  "onUpdate:modelValue": $event => ((login.name) = $event),
                  required: "",
                  autocomplete: "name"
                }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, login.name]])]))
              : _createCommentVNode("", true),
            _createElementVNode("label", { class: "field" }, [_createTextVNode("E-mail"), _withDirectives(_createElementVNode("input", {
              "onUpdate:modelValue": $event => ((login.email) = $event),
              type: "email",
              required: "",
              autocomplete: "username"
            }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, login.email]])]),
            _createElementVNode("label", { class: "field" }, [_createTextVNode("Senha"), _withDirectives(_createElementVNode("input", {
              "onUpdate:modelValue": $event => ((login.password) = $event),
              type: "password",
              required: "",
              minlength: configured?1:12,
              autocomplete: "current-password"
            }, null, 8, ["onUpdate:modelValue", "minlength"]), [[_vModelText, login.password]])]),
            (!configured)
              ? (_openBlock(), _createElementBlock("p", {
                  key: 1,
                  class: "field-help"
                }, "Use pelo menos 12 caracteres. A senha não será registrada em texto puro."))
              : _createCommentVNode("", true),
            error
              ? (_openBlock(), _createElementBlock("div", {
                  key: 2,
                  class: "alert danger"
                }, _toDisplayString(error), 1))
              : _createCommentVNode("", true),
            _createElementVNode("button", {
              class: "btn primary wide",
              disabled: busy
            }, _toDisplayString(busy?'Processando...':configured?'Entrar':'Criar administrador'), 9, ["disabled"])
          ], 40, ["onSubmit"]),
          _createElementVNode("div", { class: "login-footer" }, "Acesso protegido · Conexão local · Credenciais criptografadas")
        ])])]))
      : (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [menuOpen
          ? (_openBlock(), _createElementBlock("div", {
              key: 0,
              class: "mobile-scrim",
              onClick: $event => (menuOpen=false)
            }, null, 8, ["onClick"]))
          : _createCommentVNode("", true), _createElementVNode("aside", { class: _normalizeClass(["sidebar", {'open':menuOpen}]) }, [
          _createElementVNode("div", { class: "sidebar-header" }, [_createElementVNode("img", {
            src: "/static/app.png",
            alt: "",
            class: "brand-icon"
          }), _createElementVNode("div", null, [_createElementVNode("strong", null, "NFS-e"), _createElementVNode("span", null, "Codisplan · Fiscal")]), _createElementVNode("button", {
            class: "mobile-close",
            onClick: $event => (menuOpen=false),
            "aria-label": "Fechar menu"
          }, "×", 8, ["onClick"])]),
          _createElementVNode("div", { class: "workspace-tag" }, [_createElementVNode("span", { class: "status-dot" }), _createTextVNode(" Ambiente administrativo "), _createElementVNode("span", { class: "workspace-version" }, _toDisplayString(version), 1)]),
          _createElementVNode("nav", {
            class: "nav",
            "aria-label": "Navegação principal"
          }, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(menuGroups, (group) => {
            return (_openBlock(), _createElementBlock("div", {
              key: group.title,
              class: "menu-section"
            }, [_createElementVNode("div", { class: "menu-title" }, _toDisplayString(group.title), 1), (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(group.items, (item) => {
              return (_openBlock(), _createElementBlock("button", {
                key: item.id,
                type: "button",
                class: _normalizeClass(["nav-item", {active:page===item.id}]),
                onClick: $event => (go(item.id))
              }, [_createElementVNode("span", { class: "nav-icon" }, _toDisplayString(item.icon), 1), _createElementVNode("span", null, _toDisplayString(item.label), 1), (page===item.id)
                ? (_openBlock(), _createElementBlock("span", {
                    key: 0,
                    class: "nav-caret"
                  }, "›"))
                : _createCommentVNode("", true)], 10, ["onClick"]))
            }), 128))]))
          }), 128))]),
          _createElementVNode("div", { class: "sidebar-bottom" }, [_createElementVNode("div", { class: "profile-bubble" }, _toDisplayString(initials), 1), _createElementVNode("div", { class: "profile-text" }, [_createElementVNode("strong", null, _toDisplayString(user.name), 1), _createElementVNode("span", null, _toDisplayString(user.role), 1)]), _createElementVNode("button", {
            title: "Sair",
            class: "logout",
            onClick: logout
          }, "⇥", 8, ["onClick"])])
        ], 2), _createElementVNode("div", { class: "app-main" }, [_createElementVNode("header", { class: "topbar" }, [_createElementVNode("button", {
          class: "hamburger",
          onClick: $event => (menuOpen=true),
          "aria-label": "Abrir menu"
        }, "☰", 8, ["onClick"]), _createElementVNode("div", { class: "breadcrumb" }, [_createTextVNode("GESTÃO FISCAL "), _createElementVNode("span", null, "/"), _createTextVNode(" " + _toDisplayString(pageLabel), 1)]), _createElementVNode("div", { class: "top-actions" }, [_createElementVNode("span", { class: "status-pill" }, [_createElementVNode("span", { class: "status-dot" }), _createTextVNode(" Sistema local")]), _createElementVNode("button", {
          class: "avatar",
          onClick: $event => (go('profile')),
          title: user.name
        }, _toDisplayString(initials), 9, ["onClick", "title"])])]), _createElementVNode("main", { class: "content" }, [
          _createElementVNode("div", { class: "page-intro" }, [_createElementVNode("div", null, [_createElementVNode("p", { class: "eyebrow" }, "CODISPLAN NFS-e"), _createElementVNode("h1", null, _toDisplayString(pageLabel), 1), _createElementVNode("p", { class: "muted" }, _toDisplayString(pageSubtitle), 1)]), _createElementVNode("div", { class: "intro-action" }, [(page==='dashboard')
            ? (_openBlock(), _createElementBlock("button", {
                key: 0,
                class: "btn primary",
                onClick: $event => (go('reports'))
              }, [_createTextVNode("Gerar relatório "), _createElementVNode("span", null, "↗")], 8, ["onClick"]))
            : _createCommentVNode("", true), (page==='companies')
            ? (_openBlock(), _createElementBlock("button", {
                key: 1,
                class: "btn primary",
                onClick: $event => (showCompany=true)
              }, "+ Nova empresa", 8, ["onClick"]))
            : _createCommentVNode("", true)])]),
          error
            ? (_openBlock(), _createElementBlock("div", {
                key: 0,
                class: "alert danger",
                role: "alert"
              }, [_createTextVNode(_toDisplayString(error) + " ", 1), _createElementVNode("button", { onClick: $event => (error='') }, "×", 8, ["onClick"])]))
            : _createCommentVNode("", true),
          notice
            ? (_openBlock(), _createElementBlock("div", {
                key: 1,
                class: "alert success"
              }, [_createTextVNode(_toDisplayString(notice) + " ", 1), _createElementVNode("button", { onClick: $event => (notice='') }, "×", 8, ["onClick"])]))
            : _createCommentVNode("", true),
          (page==='dashboard')
            ? (_openBlock(), _createElementBlock("section", { key: 2 }, [_createElementVNode("div", { class: "metrics" }, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(metrics, (metric) => {
                return (_openBlock(), _createElementBlock("div", {
                  key: metric.key,
                  class: "metric"
                }, [
                  _createElementVNode("div", { class: "metric-icon" }, _toDisplayString(metric.icon), 1),
                  _createElementVNode("div", { class: "metric-label" }, _toDisplayString(metric.label), 1),
                  _createElementVNode("div", { class: "metric-value" }, _toDisplayString(dashboard[metric.key]||0), 1),
                  _createElementVNode("div", { class: "metric-desc" }, _toDisplayString(metric.desc), 1)
                ]))
              }), 128))]), _createElementVNode("div", { class: "dashboard-grid" }, [_createElementVNode("div", { class: "panel" }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("div", null, [_createElementVNode("p", { class: "eyebrow" }, "ATIVIDADE"), _createElementVNode("h2", null, "Sincronizações recentes")]), _createElementVNode("button", {
                class: "link-button",
                onClick: $event => (go('sync'))
              }, "Ver todas →", 8, ["onClick"])]), (!dashboard.latest?.length)
                ? (_openBlock(), _createElementBlock("div", {
                    key: 0,
                    class: "empty"
                  }, "Nenhuma sincronização registrada. Cadastre uma empresa e seu certificado para começar."))
                : (_openBlock(), _createElementBlock("div", {
                    key: 1,
                    class: "table-wrap"
                  }, [_createElementVNode("table", null, [_createElementVNode("thead", null, [_createElementVNode("tr", null, [
                    _createElementVNode("th", null, "Empresa"),
                    _createElementVNode("th", null, "Início"),
                    _createElementVNode("th", null, "Documentos"),
                    _createElementVNode("th", null, "Situação")
                  ])]), _createElementVNode("tbody", null, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(dashboard.latest, (item) => {
                    return (_openBlock(), _createElementBlock("tr", { key: item.id }, [
                      _createElementVNode("td", null, _toDisplayString(item.company), 1),
                      _createElementVNode("td", null, _toDisplayString(datetime(item.started_at)), 1),
                      _createElementVNode("td", null, _toDisplayString(item.inserted) + " / " + _toDisplayString(item.fetched), 1),
                      _createElementVNode("td", null, [_createElementVNode("span", { class: _normalizeClass(["mini-badge", item.status==='CONCLUIDA'?'good':'warn']) }, _toDisplayString(item.status), 3)])
                    ]))
                  }), 128))])])]))]), _createElementVNode("div", { class: "panel tips" }, [
                _createElementVNode("div", { class: "panel-header" }, [_createElementVNode("h2", null, "Próximas etapas")]),
                _createElementVNode("div", {
                  class: "tip",
                  onClick: $event => (go('companies'))
                }, [_createElementVNode("span", { class: "tip-num" }, "01"), _createElementVNode("div", null, [_createElementVNode("strong", null, "Organize as empresas"), _createElementVNode("p", null, "Cadastre os contribuintes e seus vínculos.")]), _createElementVNode("span", null, "›")], 8, ["onClick"]),
                _createElementVNode("div", {
                  class: "tip",
                  onClick: $event => (go('certificates'))
                }, [_createElementVNode("span", { class: "tip-num" }, "02"), _createElementVNode("div", null, [_createElementVNode("strong", null, "Configure o certificado"), _createElementVNode("p", null, "Associe um certificado digital A1 autorizado.")]), _createElementVNode("span", null, "›")], 8, ["onClick"]),
                _createElementVNode("div", {
                  class: "tip",
                  onClick: $event => (go('reports'))
                }, [_createElementVNode("span", { class: "tip-num" }, "03"), _createElementVNode("div", null, [_createElementVNode("strong", null, "Emita relatórios"), _createElementVNode("p", null, "Selecione o período e exporte PDF ou Excel.")]), _createElementVNode("span", null, "›")], 8, ["onClick"])
              ])])]))
            : (page==='companies')
              ? (_openBlock(), _createElementBlock("section", {
                  key: 3,
                  class: "panel"
                }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("div", null, [_createElementVNode("h2", null, "Empresas cadastradas"), _createElementVNode("p", { class: "muted" }, "CNPJ ou CPF autorizado para a consulta de documentos fiscais.")])]), _createElementVNode("div", { class: "table-wrap" }, [_createElementVNode("table", null, [_createElementVNode("thead", null, [_createElementVNode("tr", null, [
                  _createElementVNode("th", null, "Razão social"),
                  _createElementVNode("th", null, "Inscrição"),
                  _createElementVNode("th", null, "Situação"),
                  _createElementVNode("th")
                ])]), _createElementVNode("tbody", null, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(companies, (c) => {
                  return (_openBlock(), _createElementBlock("tr", { key: c.id }, [
                    _createElementVNode("td", null, [_createElementVNode("strong", null, _toDisplayString(c.name), 1)]),
                    _createElementVNode("td", { class: "mono" }, _toDisplayString(c.identifier), 1),
                    _createElementVNode("td", null, [_createElementVNode("span", { class: "mini-badge good" }, _toDisplayString(c.active?'Ativa':'Inativa'), 1)]),
                    _createElementVNode("td", null, [_createElementVNode("button", {
                      class: "link-button",
                      onClick: $event => {report.company_id=c.id;go('reports')}
                    }, "Relatórios →", 8, ["onClick"])])
                  ]))
                }), 128))])])]), (!companies.length)
                  ? (_openBlock(), _createElementBlock("div", {
                      key: 0,
                      class: "empty"
                    }, "Nenhuma empresa cadastrada."))
                  : _createCommentVNode("", true)]))
              : (page==='certificates')
                ? (_openBlock(), _createElementBlock("section", { key: 4 }, [_createElementVNode("div", { class: "panel padded" }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("div", null, [_createElementVNode("h2", null, "Certificados digitais A1"), _createElementVNode("p", { class: "muted" }, "Utilizados no canal mTLS oficial do ADN.")])]), _createElementVNode("form", {
                    class: "form-grid",
                    onSubmit: _withModifiers(uploadCertificate, ["prevent"])
                  }, [
                    _createElementVNode("label", { class: "field" }, [_createTextVNode("Identificação"), _withDirectives(_createElementVNode("input", {
                      "onUpdate:modelValue": $event => ((certificate.label) = $event),
                      placeholder: "Contador / Empresa",
                      required: ""
                    }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, certificate.label]])]),
                    _createElementVNode("label", { class: "field" }, [_createTextVNode("Arquivo PFX/P12"), _createElementVNode("input", {
                      type: "file",
                      accept: ".pfx,.p12",
                      onChange: readCertificate,
                      required: ""
                    }, null, 40, ["onChange"])]),
                    _createElementVNode("label", { class: "field" }, [_createTextVNode("Senha do certificado"), _withDirectives(_createElementVNode("input", {
                      type: "password",
                      "onUpdate:modelValue": $event => ((certificate.password) = $event),
                      autocomplete: "off",
                      required: ""
                    }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, certificate.password]])]),
                    _createElementVNode("button", {
                      class: "btn primary",
                      disabled: busy
                    }, "Adicionar certificado", 8, ["disabled"])
                  ], 40, ["onSubmit"]), _createElementVNode("p", { class: "field-help" }, "O arquivo fica criptografado no armazenamento local. Não o envie por e-mail nem o inclua no repositório.")]), _createElementVNode("div", { class: "panel spaced" }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("h2", null, "Certificados cadastrados")]), _createElementVNode("div", { class: "table-wrap" }, [_createElementVNode("table", null, [_createElementVNode("thead", null, [_createElementVNode("tr", null, [_createElementVNode("th", null, "Nome"), _createElementVNode("th", null, "Titular"), _createElementVNode("th", null, "Validade")])]), _createElementVNode("tbody", null, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(certificates, (c) => {
                    return (_openBlock(), _createElementBlock("tr", { key: c.id }, [_createElementVNode("td", null, _toDisplayString(c.label), 1), _createElementVNode("td", null, _toDisplayString(c.identity), 1), _createElementVNode("td", null, _toDisplayString(datetime(c.expires_at)), 1)]))
                  }), 128))])])]), (!certificates.length)
                    ? (_openBlock(), _createElementBlock("div", {
                        key: 0,
                        class: "empty"
                      }, "Nenhum certificado cadastrado."))
                    : _createCommentVNode("", true)]), _createElementVNode("div", { class: "panel padded spaced" }, [_createElementVNode("h2", null, "Autorizar certificado para empresa"), _createElementVNode("form", {
                    onSubmit: _withModifiers(linkCertificate, ["prevent"]),
                    class: "form-grid"
                  }, [_createElementVNode("label", { class: "field" }, [_createTextVNode("Empresa"), _withDirectives(_createElementVNode("select", {
                    "onUpdate:modelValue": $event => ((link.company_id) = $event),
                    required: ""
                  }, [_createElementVNode("option", {
                    disabled: "",
                    value: ""
                  }, "Selecione..."), (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(companies, (c) => {
                    return (_openBlock(), _createElementBlock("option", { value: c.id }, _toDisplayString(c.name), 9, ["value"]))
                  }), 256))], 8, ["onUpdate:modelValue"]), [[
                    _vModelSelect,
                    link.company_id,
                    void 0,
                    { number: true }
                  ]])]), _createElementVNode("label", { class: "field" }, [_createTextVNode("Certificado"), _withDirectives(_createElementVNode("select", {
                    "onUpdate:modelValue": $event => ((link.certificate_id) = $event),
                    required: ""
                  }, [_createElementVNode("option", {
                    disabled: "",
                    value: ""
                  }, "Selecione..."), (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(certificates, (c) => {
                    return (_openBlock(), _createElementBlock("option", { value: c.id }, _toDisplayString(c.label), 9, ["value"]))
                  }), 256))], 8, ["onUpdate:modelValue"]), [[
                    _vModelSelect,
                    link.certificate_id,
                    void 0,
                    { number: true }
                  ]])]), _createElementVNode("button", {
                    class: "btn primary",
                    disabled: busy
                  }, "Vincular", 8, ["disabled"])], 40, ["onSubmit"])])]))
                : (page==='sync')
                  ? (_openBlock(), _createElementBlock("section", { key: 5 }, [_createElementVNode("div", { class: "panel padded" }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("div", null, [_createElementVNode("h2", null, "Distribuição de documentos"), _createElementVNode("p", { class: "muted" }, "Sincronização sequencial a partir do último NSU registrado.")])]), _createElementVNode("form", {
                      onSubmit: _withModifiers(startSync, ["prevent"]),
                      class: "form-grid"
                    }, [_createElementVNode("label", { class: "field" }, [_createTextVNode("Empresa"), _withDirectives(_createElementVNode("select", {
                      "onUpdate:modelValue": $event => ((syncForm.company_id) = $event),
                      required: ""
                    }, [_createElementVNode("option", {
                      disabled: "",
                      value: ""
                    }, "Selecione..."), (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(companies, (c) => {
                      return (_openBlock(), _createElementBlock("option", { value: c.id }, _toDisplayString(c.name), 9, ["value"]))
                    }), 256))], 8, ["onUpdate:modelValue"]), [[
                      _vModelSelect,
                      syncForm.company_id,
                      void 0,
                      { number: true }
                    ]])]), _createElementVNode("label", { class: "field" }, [_createTextVNode("Certificado autorizado"), _withDirectives(_createElementVNode("select", {
                      "onUpdate:modelValue": $event => ((syncForm.certificate_id) = $event),
                      required: ""
                    }, [_createElementVNode("option", {
                      disabled: "",
                      value: ""
                    }, "Selecione..."), (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(certificates, (c) => {
                      return (_openBlock(), _createElementBlock("option", { value: c.id }, _toDisplayString(c.label), 9, ["value"]))
                    }), 256))], 8, ["onUpdate:modelValue"]), [[
                      _vModelSelect,
                      syncForm.certificate_id,
                      void 0,
                      { number: true }
                    ]])]), _createElementVNode("button", {
                      class: "btn primary",
                      disabled: busy
                    }, "Iniciar sincronização", 8, ["disabled"])], 40, ["onSubmit"]), _createElementVNode("p", { class: "field-help" }, "O NSU é exclusivo: notas do período são filtradas após armazenamento. Nenhuma competência é presumida como integralmente conferida.")]), _createElementVNode("div", { class: "panel padded spaced" }, [
                      _createElementVNode("div", { class: "panel-header" }, [_createElementVNode("div", null, [_createElementVNode("h2", null, "Consultas diretas ao ADN"), _createElementVNode("p", { class: "muted" }, "Consulte um NSU específico, um lote ou os eventos vinculados a uma chave de acesso.")])]),
                      _createElementVNode("div", { class: "form-grid" }, [
                        _createElementVNode("label", { class: "field" }, [_createTextVNode("NSU inicial"), _withDirectives(_createElementVNode("input", {
                          type: "number",
                          min: "0",
                          "onUpdate:modelValue": $event => ((direct.nsu) = $event)
                        }, null, 8, ["onUpdate:modelValue"]), [[
                          _vModelText,
                          direct.nsu,
                          void 0,
                          { number: true }
                        ]])]),
                        _createElementVNode("label", { class: "field" }, [_createTextVNode("Modo"), _withDirectives(_createElementVNode("select", { "onUpdate:modelValue": $event => ((direct.lote) = $event) }, [_createElementVNode("option", { value: true }, "Lote a partir do NSU (exclusivo)", 8, ["value"]), _createElementVNode("option", { value: false }, "Documento específico por NSU", 8, ["value"])], 8, ["onUpdate:modelValue"]), [[_vModelSelect, direct.lote]])]),
                        _createElementVNode("label", { class: "field" }, [_createTextVNode("Chave de acesso NFS-e"), _withDirectives(_createElementVNode("input", {
                          "onUpdate:modelValue": $event => ((direct.access_key) = $event),
                          placeholder: "Informe a chave para consultar eventos"
                        }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, direct.access_key]])]),
                        _createElementVNode("label", { class: "field" }, [_createTextVNode("Persistir XMLs encontrados"), _withDirectives(_createElementVNode("select", { "onUpdate:modelValue": $event => ((direct.save) = $event) }, [_createElementVNode("option", { value: false }, "Não, somente conferir", 8, ["value"]), _createElementVNode("option", { value: true }, "Sim, sem avançar cursor", 8, ["value"])], 8, ["onUpdate:modelValue"]), [[_vModelSelect, direct.save]])])
                      ]),
                      _createElementVNode("div", { class: "actions spaced" }, [_createElementVNode("button", {
                        class: "btn secondary",
                        onClick: $event => (directQuery('nsu')),
                        disabled: busy
                      }, "Consultar por NSU", 8, ["onClick", "disabled"]), _createElementVNode("button", {
                        class: "btn secondary",
                        onClick: $event => (directQuery('events')),
                        disabled: busy
                      }, "Consultar eventos da chave", 8, ["onClick", "disabled"])]),
                      directResult
                        ? (_openBlock(), _createElementBlock("div", {
                            key: 0,
                            class: "spaced"
                          }, [_createElementVNode("p", null, [_createElementVNode("strong", null, "Resultado:"), _createTextVNode(" " + _toDisplayString(directResult.StatusProcessamento||directResult.status||'Localizado') + " • " + _toDisplayString(directResult.documentos?.length||0) + " documentos • " + _toDisplayString(directResult.salvos||0) + " novos armazenados", 1)]), _createElementVNode("div", { class: "table-wrap" }, [_createElementVNode("table", null, [_createElementVNode("thead", null, [_createElementVNode("tr", null, [
                            _createElementVNode("th", null, "NSU"),
                            _createElementVNode("th", null, "Chave de acesso"),
                            _createElementVNode("th", null, "Documento"),
                            _createElementVNode("th", null, "Evento")
                          ])]), _createElementVNode("tbody", null, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(directResult.documentos, (d, i) => {
                            return (_openBlock(), _createElementBlock("tr", { key: i }, [
                              _createElementVNode("td", null, _toDisplayString(d.NSU), 1),
                              _createElementVNode("td", { class: "mono" }, _toDisplayString(d.ChaveAcesso), 1),
                              _createElementVNode("td", null, _toDisplayString(d.TipoDocumento), 1),
                              _createElementVNode("td", null, _toDisplayString(d.TipoEvento||'—'), 1)
                            ]))
                          }), 128))])])])]))
                        : _createCommentVNode("", true)
                    ]), _createElementVNode("div", { class: "panel spaced" }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("h2", null, "Execuções"), _createElementVNode("button", {
                      class: "btn secondary small",
                      onClick: $event => (load('sync'))
                    }, "Atualizar", 8, ["onClick"])]), _createElementVNode("div", { class: "table-wrap" }, [_createElementVNode("table", null, [_createElementVNode("thead", null, [_createElementVNode("tr", null, [
                      _createElementVNode("th", null, "ID"),
                      _createElementVNode("th", null, "Início"),
                      _createElementVNode("th", null, "Localizados"),
                      _createElementVNode("th", null, "Novos"),
                      _createElementVNode("th", null, "Resultado"),
                      _createElementVNode("th", null, "Diagnóstico")
                    ])]), _createElementVNode("tbody", null, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(runs, (x) => {
                      return (_openBlock(), _createElementBlock("tr", { key: x.id }, [
                        _createElementVNode("td", null, _toDisplayString(x.id), 1),
                        _createElementVNode("td", null, _toDisplayString(datetime(x.started_at)), 1),
                        _createElementVNode("td", null, _toDisplayString(x.fetched), 1),
                        _createElementVNode("td", null, _toDisplayString(x.inserted), 1),
                        _createElementVNode("td", null, _toDisplayString(x.status), 1),
                        _createElementVNode("td", null, _toDisplayString(x.diagnostic||'—'), 1)
                      ]))
                    }), 128))])])])])]))
                  : (page==='documents')
                    ? (_openBlock(), _createElementBlock("section", { key: 6 }, [_createElementVNode("div", { class: "panel padded" }, [
                        _createElementVNode("div", { class: "panel-header" }, [_createElementVNode("h2", null, "Documentos e eventos")]),
                        _createElementVNode("div", { class: "filters" }, [_createElementVNode("label", { class: "field" }, [_createTextVNode("Empresa"), _withDirectives(_createElementVNode("select", { "onUpdate:modelValue": $event => ((filter.company_id) = $event) }, [_createElementVNode("option", {
                          disabled: "",
                          value: ""
                        }, "Selecione..."), (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(companies, (c) => {
                          return (_openBlock(), _createElementBlock("option", { value: c.id }, _toDisplayString(c.name), 9, ["value"]))
                        }), 256))], 8, ["onUpdate:modelValue"]), [[
                          _vModelSelect,
                          filter.company_id,
                          void 0,
                          { number: true }
                        ]])]), _createElementVNode("label", { class: "field" }, [_createTextVNode("Tipo"), _withDirectives(_createElementVNode("select", { "onUpdate:modelValue": $event => ((filter.document_type) = $event) }, [
                          _createElementVNode("option", { value: "" }, "Todos"),
                          _createElementVNode("option", null, "NFSE"),
                          _createElementVNode("option", null, "EVENTO"),
                          _createElementVNode("option", null, "DPS"),
                          _createElementVNode("option", null, "CNC")
                        ], 8, ["onUpdate:modelValue"]), [[_vModelSelect, filter.document_type]])]), _createElementVNode("button", {
                          class: "btn primary",
                          onClick: loadDocuments
                        }, "Consultar", 8, ["onClick"])]),
                        _createElementVNode("div", { class: "table-wrap" }, [_createElementVNode("table", null, [_createElementVNode("thead", null, [_createElementVNode("tr", null, [
                          _createElementVNode("th", null, "NSU"),
                          _createElementVNode("th", null, "Nota"),
                          _createElementVNode("th", null, "Data"),
                          _createElementVNode("th", null, "Tomador"),
                          _createElementVNode("th", null, "Tipo"),
                          _createElementVNode("th", null, "Situação"),
                          _createElementVNode("th", null, "XML")
                        ])]), _createElementVNode("tbody", null, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(documents, (d) => {
                          return (_openBlock(), _createElementBlock("tr", { key: d.id }, [
                            _createElementVNode("td", { class: "mono" }, _toDisplayString(d.nsu), 1),
                            _createElementVNode("td", null, _toDisplayString(d.invoice_number||'—'), 1),
                            _createElementVNode("td", null, _toDisplayString(d.issued_on||'—'), 1),
                            _createElementVNode("td", null, _toDisplayString(d.recipient_name||'—'), 1),
                            _createElementVNode("td", null, _toDisplayString(d.document_type), 1),
                            _createElementVNode("td", null, _toDisplayString(d.status), 1),
                            _createElementVNode("td", null, [_createElementVNode("a", {
                              href: '/api/v1/documents/'+d.id+'/xml',
                              target: "_blank"
                            }, "Baixar", 8, ["href"])])
                          ]))
                        }), 128))])])]),
                        (!documents.length)
                          ? (_openBlock(), _createElementBlock("div", {
                              key: 0,
                              class: "empty"
                            }, "Selecione a empresa e clique em Consultar."))
                          : _createCommentVNode("", true)
                      ])]))
                    : (page==='reports')
                      ? (_openBlock(), _createElementBlock("section", { key: 7 }, [_createElementVNode("div", { class: "panel padded" }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("div", null, [_createElementVNode("h2", null, "Gerar demonstrativo fiscal"), _createElementVNode("p", { class: "muted" }, "Valores provenientes dos XMLs recebidos e armazenados.")])]), _createElementVNode("form", {
                          class: "report-controls",
                          onSubmit: _withModifiers(previewReport, ["prevent"])
                        }, [
                          _createElementVNode("label", { class: "field" }, [_createTextVNode("Empresa"), _withDirectives(_createElementVNode("select", {
                            "onUpdate:modelValue": $event => ((report.company_id) = $event),
                            required: ""
                          }, [_createElementVNode("option", {
                            disabled: "",
                            value: ""
                          }, "Selecione uma empresa"), (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(companies, (c) => {
                            return (_openBlock(), _createElementBlock("option", { value: c.id }, _toDisplayString(c.name), 9, ["value"]))
                          }), 256))], 8, ["onUpdate:modelValue"]), [[
                            _vModelSelect,
                            report.company_id,
                            void 0,
                            { number: true }
                          ]])]),
                          _createElementVNode("label", { class: "field" }, [_createTextVNode("Tipo de relatório"), _withDirectives(_createElementVNode("select", { "onUpdate:modelValue": $event => ((report.kind) = $event) }, [
                            _createElementVNode("option", { value: "mensal" }, "Serviços prestados — emissão"),
                            _createElementVNode("option", { value: "competencia" }, "Serviços prestados — competência"),
                            _createElementVNode("option", { value: "iss-retido" }, "ISS retido"),
                            _createElementVNode("option", { value: "canceladas" }, "Canceladas e substituídas")
                          ], 8, ["onUpdate:modelValue"]), [[_vModelSelect, report.kind]])]),
                          _createElementVNode("label", { class: "field" }, [_createTextVNode("Data inicial"), _withDirectives(_createElementVNode("input", {
                            "onUpdate:modelValue": $event => ((report.inicio) = $event),
                            type: "date",
                            required: ""
                          }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, report.inicio]])]),
                          _createElementVNode("label", { class: "field" }, [_createTextVNode("Data final"), _withDirectives(_createElementVNode("input", {
                            "onUpdate:modelValue": $event => ((report.fim) = $event),
                            type: "date",
                            required: ""
                          }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, report.fim]])]),
                          _createElementVNode("button", {
                            class: "btn primary",
                            disabled: busy
                          }, "Visualizar", 8, ["disabled"])
                        ], 40, ["onSubmit"]), reportResult
                          ? (_openBlock(), _createElementBlock("div", { key: 0 }, [
                              _createElementVNode("div", { class: "summary-row" }, [
                                _createElementVNode("div", null, [_createElementVNode("span", null, "Notas no período"), _createElementVNode("strong", null, _toDisplayString(reportResult.count), 1)]),
                                _createElementVNode("div", null, [_createElementVNode("span", null, "Serviços vigentes"), _createElementVNode("strong", null, _toDisplayString(currency(reportResult.totals.service_cents)), 1)]),
                                _createElementVNode("div", null, [_createElementVNode("span", null, "ISS retido"), _createElementVNode("strong", null, _toDisplayString(currency(reportResult.totals.iss_withheld_cents)), 1)]),
                                _createElementVNode("div", null, [_createElementVNode("span", null, "Canceladas"), _createElementVNode("strong", null, _toDisplayString(reportResult.by_status.CANCELADA), 1)])
                              ]),
                              _createElementVNode("div", { class: "actions spaced" }, [_createElementVNode("button", {
                                class: "btn primary",
                                onClick: $event => (download('pdf'))
                              }, "↓ PDF", 8, ["onClick"]), _createElementVNode("button", {
                                class: "btn secondary",
                                onClick: $event => (download('xlsx'))
                              }, "↓ Excel", 8, ["onClick"]), _createElementVNode("button", {
                                class: "btn secondary",
                                onClick: $event => (download('csv'))
                              }, "↓ CSV", 8, ["onClick"])]),
                              _createElementVNode("div", { class: "table-wrap" }, [_createElementVNode("table", null, [_createElementVNode("thead", null, [_createElementVNode("tr", null, [
                                _createElementVNode("th", null, "Nota"),
                                _createElementVNode("th", null, "Emissão"),
                                _createElementVNode("th", null, "Competência"),
                                _createElementVNode("th", null, "Tomador"),
                                _createElementVNode("th", null, "Serviços"),
                                _createElementVNode("th", null, "ISS retido"),
                                _createElementVNode("th", null, "Situação")
                              ])]), _createElementVNode("tbody", null, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(reportResult.rows.slice(0,150), (d, i) => {
                                return (_openBlock(), _createElementBlock("tr", { key: i }, [
                                  _createElementVNode("td", null, _toDisplayString(d.invoice_number), 1),
                                  _createElementVNode("td", null, _toDisplayString(d.issued_on), 1),
                                  _createElementVNode("td", null, _toDisplayString(d.competence_on), 1),
                                  _createElementVNode("td", null, _toDisplayString(d.recipient_name), 1),
                                  _createElementVNode("td", null, _toDisplayString(currency(d.service_cents)), 1),
                                  _createElementVNode("td", null, _toDisplayString(currency(d.iss_withheld_cents)), 1),
                                  _createElementVNode("td", null, _toDisplayString(d.status), 1)
                                ]))
                              }), 128))])])]),
                              _createElementVNode("p", { class: "field-help" }, _toDisplayString(reportResult.warning) + " A visualização mostra até 150 linhas; a exportação inclui todas.", 1)
                            ]))
                          : _createCommentVNode("", true)])]))
                      : (page==='settings')
                        ? (_openBlock(), _createElementBlock("section", {
                            key: 8,
                            class: "panel padded"
                          }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("h2", null, "Integração com o ADN")]), _createElementVNode("form", {
                            onSubmit: _withModifiers(saveSettings, ["prevent"]),
                            class: "stack"
                          }, [_createElementVNode("label", { class: "field" }, [_createTextVNode("URL HTTPS oficial"), _withDirectives(_createElementVNode("input", {
                            "onUpdate:modelValue": $event => ((settings.adn_url) = $event),
                            type: "url",
                            placeholder: "https://...nfse.gov.br/...",
                            required: ""
                          }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, settings.adn_url]])]), _createElementVNode("p", { class: "field-help" }, "O endereço de produção deve ser fornecido pela documentação oficial. A aplicação não aceita endereços HTTP ou domínios de terceiros."), _createElementVNode("button", {
                            class: "btn primary",
                            disabled: busy
                          }, "Salvar configuração", 8, ["disabled"])], 40, ["onSubmit"])]))
                        : (page==='users')
                          ? (_openBlock(), _createElementBlock("section", {
                              key: 9,
                              class: "panel padded"
                            }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("h2", null, "Usuários e acessos")]), _createElementVNode("form", {
                              class: "form-grid",
                              onSubmit: _withModifiers(createUser, ["prevent"])
                            }, [
                              _createElementVNode("label", { class: "field" }, [_createTextVNode("Nome"), _withDirectives(_createElementVNode("input", {
                                "onUpdate:modelValue": $event => ((userForm.name) = $event),
                                required: ""
                              }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, userForm.name]])]),
                              _createElementVNode("label", { class: "field" }, [_createTextVNode("E-mail"), _withDirectives(_createElementVNode("input", {
                                type: "email",
                                "onUpdate:modelValue": $event => ((userForm.email) = $event),
                                required: ""
                              }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, userForm.email]])]),
                              _createElementVNode("label", { class: "field" }, [_createTextVNode("Perfil"), _withDirectives(_createElementVNode("select", { "onUpdate:modelValue": $event => ((userForm.role) = $event) }, [_createElementVNode("option", { value: "admin" }, "Administrador"), _createElementVNode("option", { value: "operador" }, "Operador"), _createElementVNode("option", { value: "leitor" }, "Leitor")], 8, ["onUpdate:modelValue"]), [[_vModelSelect, userForm.role]])]),
                              _createElementVNode("label", { class: "field" }, [_createTextVNode("Senha inicial"), _withDirectives(_createElementVNode("input", {
                                type: "password",
                                minlength: "12",
                                "onUpdate:modelValue": $event => ((userForm.password) = $event),
                                required: ""
                              }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, userForm.password]])]),
                              _createElementVNode("button", {
                                class: "btn primary",
                                disabled: busy
                              }, "Cadastrar usuário", 8, ["disabled"])
                            ], 40, ["onSubmit"]), _createElementVNode("div", { class: "table-wrap spaced" }, [_createElementVNode("table", null, [_createElementVNode("thead", null, [_createElementVNode("tr", null, [_createElementVNode("th", null, "Nome"), _createElementVNode("th", null, "E-mail"), _createElementVNode("th", null, "Perfil")])]), _createElementVNode("tbody", null, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(users, (x) => {
                              return (_openBlock(), _createElementBlock("tr", { key: x.id }, [_createElementVNode("td", null, _toDisplayString(x.name), 1), _createElementVNode("td", null, _toDisplayString(x.email), 1), _createElementVNode("td", null, _toDisplayString(x.role), 1)]))
                            }), 128))])])])]))
                          : (page==='audit')
                            ? (_openBlock(), _createElementBlock("section", {
                                key: 10,
                                class: "panel padded"
                              }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("h2", null, "Histórico de ações")]), _createElementVNode("div", { class: "table-wrap" }, [_createElementVNode("table", null, [_createElementVNode("thead", null, [_createElementVNode("tr", null, [
                                _createElementVNode("th", null, "Data"),
                                _createElementVNode("th", null, "Ator"),
                                _createElementVNode("th", null, "Ação"),
                                _createElementVNode("th", null, "Objeto")
                              ])]), _createElementVNode("tbody", null, [(_openBlock(true), _createElementBlock(_Fragment, null, _renderList(audit, (x) => {
                                return (_openBlock(), _createElementBlock("tr", { key: x.id }, [
                                  _createElementVNode("td", null, _toDisplayString(datetime(x.at)), 1),
                                  _createElementVNode("td", null, _toDisplayString(x.actor), 1),
                                  _createElementVNode("td", null, _toDisplayString(x.action), 1),
                                  _createElementVNode("td", null, _toDisplayString(x.target), 1)
                                ]))
                              }), 128))])])])]))
                            : (page==='profile')
                              ? (_openBlock(), _createElementBlock("section", {
                                  key: 11,
                                  class: "panel padded"
                                }, [
                                  _createElementVNode("h2", null, "Minha conta"),
                                  _createElementVNode("p", null, [_createElementVNode("strong", null, _toDisplayString(user.name), 1)]),
                                  _createElementVNode("p", null, _toDisplayString(user.email), 1),
                                  _createElementVNode("p", null, "Perfil: " + _toDisplayString(user.role), 1),
                                  _createElementVNode("p", { class: "muted" }, "Sessão local com cookie HttpOnly e proteção CSRF."),
                                  _createElementVNode("button", {
                                    class: "btn secondary",
                                    onClick: logout
                                  }, "Encerrar sessão", 8, ["onClick"])
                                ]))
                              : _createCommentVNode("", true),
          _createElementVNode("footer", { class: "footer" }, [_createElementVNode("span", null, "Codisplan Contabilidade · Plataforma NFS-e"), _createElementVNode("span", null, _toDisplayString(version) + " · " + _toDisplayString(user.role), 1)])
        ])])], 64)), showCompany
      ? (_openBlock(), _createElementBlock("div", {
          key: 2,
          class: "modal-shade",
          onClick: _withModifiers($event => (showCompany=false), ["self"])
        }, [_createElementVNode("section", {
          class: "modal",
          role: "dialog",
          "aria-modal": "true"
        }, [_createElementVNode("div", { class: "panel-header" }, [_createElementVNode("h2", null, "Nova empresa"), _createElementVNode("button", {
          class: "close",
          onClick: $event => (showCompany=false),
          "aria-label": "Fechar"
        }, "×", 8, ["onClick"])]), _createElementVNode("form", {
          onSubmit: _withModifiers(addCompany, ["prevent"]),
          class: "stack padded"
        }, [_createElementVNode("label", { class: "field" }, [_createTextVNode("Razão social"), _withDirectives(_createElementVNode("input", {
          "onUpdate:modelValue": $event => ((companyForm.name) = $event),
          required: ""
        }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, companyForm.name]])]), _createElementVNode("label", { class: "field" }, [_createTextVNode("CNPJ ou CPF"), _withDirectives(_createElementVNode("input", {
          "onUpdate:modelValue": $event => ((companyForm.identifier) = $event),
          required: "",
          placeholder: "Somente números"
        }, null, 8, ["onUpdate:modelValue"]), [[_vModelText, companyForm.identifier]])]), _createElementVNode("button", {
          class: "btn primary",
          disabled: busy
        }, "Cadastrar empresa", 8, ["disabled"])], 40, ["onSubmit"])])], 8, ["onClick"]))
      : _createCommentVNode("", true)], 2))
  }
};
