import{$ as e,Dt as t,G as n,K as r,Q as i,a,f as o,j as s,k as c,n as l,nt as u,p as d,t as f,w as p,y as m}from"./chunks/register-dashboard-card-BLc74zCS.js";f({tag:o,editorTag:d,card:class extends l{static editorTag=d;get cardType(){return`custom:${o}`}get sourceCommand(){return t}get subscribeCommand(){return`unifi_insights/site_health/subscribe`}get defaultTitle(){return`Site Health`}get headerIcon(){return e}get headerAccent(){let e=String(this.snapshot?.health?.level??`healthy`);return e===`critical`?`var(--uit-offline)`:e===`degraded`?`var(--uit-warning)`:`var(--uit-online)`}renderHeaderBadge(){if(!this.snapshot)return c;let e=this.snapshot.health??{},t=String(e.level??`unknown`);return s`<span class="chip ${t}">
            <span class="status-dot"></span>
            <span>${t}</span>
        </span>`}renderContent(){let e=this.snapshot;if(!e)return s`<div class="state">Choose site.</div>`;let t=e.health??{},a=e.gateway??{},o=e.clients??{},l=e.devices??{},d=String(t.level??`unknown`),f=String(a.internet??`unknown`),h=Number(o.total??0),g=Number(o.wired??0),_=Number(o.wireless??0),v=h>0?Math.round(_/h*100):50,y=0,b=0;for(let e of Object.values(l))if(e&&typeof e==`object`){let t=Number(e.online??0),n=Number(e.offline??0),r=Number(e.unknown??0);y+=t,b+=t+n+r}let x=typeof a.name==`string`&&a.name?a.name:`UniFi Gateway`,S=m(a.uptime_s);return s`
            <div class="hero-banner">
                <div class="hero-left">
                    ${p(i)}
                    <div>
                        <div class="hero-title">${x}</div>
                        <div class="hero-meta">
                            Status: ${d}${S?` · Uptime ${S}`:``}
                        </div>
                    </div>
                </div>
                <span class="chip ${f===`online`?`ok`:`warning`}">
                    <span class="status-dot"></span>
                    ${f}
                </span>
            </div>

            <div class="kpi-grid">
                <div class="kpi-tile">
                    <div class="kpi-top">
                        <span>Internet</span>
                        ${p(r)}
                    </div>
                    <div class="kpi-value">${f}</div>
                    <div class="kpi-sub">WAN Health · ${d}</div>
                </div>

                <div class="kpi-tile">
                    <div class="kpi-top">
                        <span>Clients</span>
                        ${p(u)}
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
                              ${p(n)}
                          </div>
                          <div class="kpi-value">
                              ${y}/${b}
                          </div>
                          <div class="kpi-sub">Infrastructure online</div>
                      </div>`:c}
            </div>
        `}},editor:class extends a{constructor(){super(o,t)}},name:`UniFi Site Health`,description:`Compact site health summary with WAN, gateway, device, and client status.`});