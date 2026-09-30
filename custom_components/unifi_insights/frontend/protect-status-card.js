import{F as e,c as t,j as n,k as r,l as i,n as a,r as o,t as s,v as c,w as l,z as u}from"./chunks/register-dashboard-card-DFoe8fM2.js";s({tag:t,editorTag:i,card:class extends a{static editorTag=i;get cardType(){return`custom:${t}`}get sourceCommand(){return`unifi_insights/protect/sources`}get subscribeCommand(){return`unifi_insights/protect/subscribe`}get defaultTitle(){return`Protect Status`}get headerIcon(){return u}get includeSiteInSubscribeMessage(){return!1}getBinding(){let e=this.config.entry_id;if(e)return{entry_id:e,site_id:this.config.site_id??`*`};if(this.sources.length===1)return{entry_id:this.sources[0].entry_id,site_id:this.config.site_id??`*`}}renderHeaderBadge(){if(!this.snapshot)return r;let e=Array.isArray(this.snapshot.devices)?this.snapshot.devices:[],t=e.filter(e=>e.connected===!1).length,i=e.length-t;return n`
            <span class="chip ${t>0?`warning`:`ok`}">
                <span class="status-dot"></span>
                ${i}/${e.length} Online
            </span>
        `}renderContent(){let t=this.snapshot;if(!t)return n`<div class="state">No Protect data</div>`;let i=Array.isArray(t.devices)?t.devices:[],a=i.filter(e=>e.connected===!1).length,o=i.length-a;return n`
            <div class="kpi-grid">
                <div class="kpi-tile">
                    <div class="kpi-top">
                        <span>Devices</span>
                        ${l(u)}
                    </div>
                    <div class="kpi-value">${i.length}</div>
                    <div class="kpi-sub">${o} active</div>
                </div>
                <div class="kpi-tile">
                    <div class="kpi-top">
                        <span>Offline</span>
                        ${l(e)}
                    </div>
                    <div class="kpi-value">${a}</div>
                    <div class="kpi-sub">
                        ${a===0?`All connected`:`Needs attention`}
                    </div>
                </div>
            </div>

            <div class="list">
                ${i.slice(0,6).map(e=>{let t=typeof e.camera_entity_id==`string`?e.camera_entity_id:void 0,i=String(e.name??`Device`),a=String(e.kind??`device`),o=e.connected!==!1,s=o?`online`:`offline`,u=`${i} · ${a}`;return n`
                        <div class="item-card">
                            <div class="item-icon ${s}">
                                ${l(c(a))}
                            </div>
                            <div class="item-body">
                                <div class="item-top">
                                    ${t?n`<button
                                              type="button"
                                              class="link item-name"
                                              @click=${()=>this.openMoreInfo(t)}
                                          >
                                              ${u}
                                          </button>`:n`<span class="item-name">
                                              ${u}
                                          </span>`}
                                    <span class="chip ${s}">
                                        <span class="status-dot"></span>
                                        ${s}
                                    </span>
                                </div>
                                ${e.is_recording||e.motion_active?n`<div class="item-meta">
                                          ${e.is_recording&&o?n`<span>● Recording</span>`:r}
                                          ${e.motion_active?n`<span>· Motion detected</span>`:r}
                                      </div>`:r}
                            </div>
                        </div>
                    `})}
            </div>
        `}},editor:class extends o{constructor(){super(t,`unifi_insights/protect/sources`)}},name:`UniFi Protect Status`,description:`Live UniFi Protect camera, doorbell, chime, and NVR status summary.`});