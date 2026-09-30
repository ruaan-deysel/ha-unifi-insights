import{$ as e,Dt as t,G as n,K as r,Q as i,_ as a,d as o,j as s,k as c,n as l,nt as u,r as d,t as f,u as p,w as m}from"./chunks/register-dashboard-card-DFoe8fM2.js";f({tag:p,editorTag:o,card:class extends l{static editorTag=o;get cardType(){return`custom:${p}`}get sourceCommand(){return t}get subscribeCommand(){return`unifi_insights/site_health/subscribe`}get defaultTitle(){return`Site Health`}get headerIcon(){return e}get headerAccent(){let e=String(this.snapshot?.health?.level??`healthy`);return e===`critical`?`var(--uit-offline)`:e===`degraded`?`var(--uit-warning)`:`var(--uit-online)`}renderHeaderBadge(){if(!this.snapshot)return c;let e=this.snapshot.health??{},t=String(e.level??`unknown`);return s`<span class="chip ${t}">
            <span class="status-dot"></span>
            <span>${t}</span>
        </span>`}renderContent(){let e=this.snapshot;if(!e)return s`<div class="state">Choose site.</div>`;let t=e.health??{},o=e.gateway??{},l=e.clients??{},d=e.devices??{},f=String(t.level??`unknown`),p=String(o.internet??`unknown`),h=Number(l.total??0),g=Number(l.wired??0),_=Number(l.wireless??0),v=h>0?Math.round(_/h*100):50,y=0,b=0;for(let e of Object.values(d))if(e&&typeof e==`object`){let t=Number(e.online??0),n=Number(e.offline??0),r=Number(e.unknown??0);y+=t,b+=t+n+r}let x=typeof o.name==`string`&&o.name?o.name:`UniFi Gateway`,S=a(o.uptime_s);return s`
            <div class="hero-banner">
                <div class="hero-left">
                    ${m(i)}
                    <div>
                        <div class="hero-title">${x}</div>
                        <div class="hero-meta">
                            Status: ${f}${S?` · Uptime ${S}`:``}
                        </div>
                    </div>
                </div>
                <span class="chip ${p===`online`?`ok`:`warning`}">
                    <span class="status-dot"></span>
                    ${p}
                </span>
            </div>

            <div class="kpi-grid">
                <div class="kpi-tile">
                    <div class="kpi-top">
                        <span>Internet</span>
                        ${m(r)}
                    </div>
                    <div class="kpi-value">${p}</div>
                    <div class="kpi-sub">WAN Health · ${f}</div>
                </div>

                <div class="kpi-tile">
                    <div class="kpi-top">
                        <span>Clients</span>
                        ${m(u)}
                    </div>
                    <div class="kpi-value">${h}</div>
                    <div class="bar-track" aria-hidden="true">
                        <div
                            class="bar-fill"
                            style=${`width: ${v}%`}
                        ></div>
                    </div>
                    <div class="kpi-sub">
                        ${_||g?`${_} Wi-Fi · ${g} Wired`:`Connected clients`}
                    </div>
                </div>

                ${b>0?s`<div class="kpi-tile">
                          <div class="kpi-top">
                              <span>Devices</span>
                              ${m(n)}
                          </div>
                          <div class="kpi-value">
                              ${y}/${b}
                          </div>
                          <div class="kpi-sub">Infrastructure online</div>
                      </div>`:c}
            </div>
        `}},editor:class extends d{constructor(){super(p,t)}},name:`UniFi Site Health`,description:`Compact site health summary with WAN, gateway, device, and client status.`});