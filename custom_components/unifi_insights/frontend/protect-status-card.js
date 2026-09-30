import{F as e,a as t,b as n,d as r,j as i,k as a,n as o,t as s,u as c,w as l,z as u}from"./chunks/register-dashboard-card-BLc74zCS.js";s({tag:c,editorTag:r,card:class extends o{static editorTag=r;get cardType(){return`custom:${c}`}get sourceCommand(){return`unifi_insights/protect/sources`}get subscribeCommand(){return`unifi_insights/protect/subscribe`}get defaultTitle(){return`Protect Status`}get headerIcon(){return u}get includeSiteInSubscribeMessage(){return!1}getBinding(){let e=this.config.entry_id;if(e)return{entry_id:e,site_id:this.config.site_id??`*`};if(this.sources.length===1)return{entry_id:this.sources[0].entry_id,site_id:this.config.site_id??`*`}}renderHeaderBadge(){if(!this.snapshot)return a;let e=Array.isArray(this.snapshot.devices)?this.snapshot.devices:[],t=e.filter(e=>e.connected===!1).length,n=e.length-t;return i`
            <span class="chip ${t>0?`warning`:`ok`}">
                <span class="status-dot"></span>
                ${n}/${e.length} Online
            </span>
        `}renderContent(){let t=this.snapshot;if(!t)return i`<div class="state">No Protect data</div>`;let r=Array.isArray(t.devices)?t.devices:[],o=r.filter(e=>e.connected===!1).length,s=r.length-o;return i`
            <div class="kpi-grid">
                <div class="kpi-tile">
                    <div class="kpi-top">
                        <span>Devices</span>
                        ${l(u)}
                    </div>
                    <div class="kpi-value">${r.length}</div>
                    <div class="kpi-sub">${s} active</div>
                </div>
                <div class="kpi-tile">
                    <div class="kpi-top">
                        <span>Offline</span>
                        ${l(e)}
                    </div>
                    <div class="kpi-value">${o}</div>
                    <div class="kpi-sub">
                        ${o===0?`All connected`:`Needs attention`}
                    </div>
                </div>
            </div>

            <div class="list">
                ${r.slice(0,6).map(e=>{let t=typeof e.camera_entity_id==`string`?e.camera_entity_id:void 0,r=String(e.name??`Device`),o=String(e.kind??`device`),s=e.connected!==!1,c=s?`online`:`offline`,u=`${r} · ${o}`;return i`
                        <div class="item-card">
                            <div class="item-icon ${c}">
                                ${l(n(o))}
                            </div>
                            <div class="item-body">
                                <div class="item-top">
                                    ${t?i`<button
                                              type="button"
                                              class="link item-name"
                                              @click=${()=>this.openMoreInfo(t)}
                                          >
                                              ${u}
                                          </button>`:i`<span class="item-name">
                                              ${u}
                                          </span>`}
                                    <span class="chip ${c}">
                                        <span class="status-dot"></span>
                                        ${c}
                                    </span>
                                </div>
                                ${e.is_recording||e.motion_active?i`<div class="item-meta">
                                          ${e.is_recording&&s?i`<span>● Recording</span>`:a}
                                          ${e.motion_active?i`<span>· Motion detected</span>`:a}
                                      </div>`:a}
                            </div>
                        </div>
                    `})}
            </div>
        `}},editor:class extends t{constructor(){super(c,`unifi_insights/protect/sources`)}},name:`UniFi Protect Status`,description:`Live UniFi Protect camera, doorbell, chime, and NVR status summary.`});