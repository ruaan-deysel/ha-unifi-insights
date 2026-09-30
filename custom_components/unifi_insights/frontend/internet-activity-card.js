import{Dt as e,I as t,K as n,L as r,a as i,et as a,h as o,i as s,j as c,k as l,m as u,n as d,r as f,t as p,w as m}from"./chunks/register-dashboard-card-DFoe8fM2.js";var h=class extends d{static editorTag=i;static properties={...d.properties,selectedWindow:{state:!0}};constructor(){super(),this.selectedWindow=`1d`}get cardType(){return`custom:${s}`}get sourceCommand(){return e}get subscribeCommand(){return`unifi_insights/internet_activity/subscribe`}get defaultTitle(){return`Internet Activity`}get headerIcon(){return a}resolveActiveWindow(e){let t=[`1h`,`1d`,`1w`,`1m`].filter(t=>t in e);return{keys:t,activeWindow:this.selectedWindow in e?this.selectedWindow:t[0]??`1d`}}renderHeaderBadge(){let e=this.snapshot?.windows??{},{keys:t,activeWindow:n}=this.resolveActiveWindow(e);return t.length<=1?l:c`
            <div class="pill-tabs" role="group" aria-label="Time window">
                ${t.map(e=>c`
                        <button
                            type="button"
                            class="pill-tab"
                            aria-pressed=${String(n===e)}
                            @click=${()=>{this.selectedWindow=e}}
                        >
                            ${e}
                        </button>
                    `)}
            </div>
        `}renderContent(){let e=this.snapshot;if(!e)return c`<div class="state">No data</div>`;let i=e.windows??{},{activeWindow:a}=this.resolveActiveWindow(i),s=i[a]??i[`1d`]??i[`1h`]??{},d=Number(s.download_bytes??0),f=Number(s.upload_bytes??0),p=d+f,h=`${Math.round(d/1e6)} MB`,g=`${Math.round(f/1e6)} MB`,_=`${Math.round(p/1e6)} MB`,v=p>0?Math.round(d/p*100):50,y=p>0?100-v:50,b=e.throughput??{},x=u(b.rx_bps),S=u(b.tx_bps),C=e.entity_ids??{},w=C[`download_${a}`],T=C[`upload_${a}`];return c`
            ${x||S?c`<div class="hero-banner">
                      <div class="hero-left">
                          ${m(n)}
                          <div>
                              <div class="hero-title">Live Throughput</div>
                              <div class="hero-meta">
                                  ↓ ${x??`0 bps`} · ↑ ${S??`0 bps`}
                              </div>
                          </div>
                      </div>
                      <span class="chip ok">
                          <span class="status-dot"></span>Live
                      </span>
                  </div>`:l}

            <div class="kpi-grid">
                <button
                    type="button"
                    class="kpi-tile ${w?`clickable`:``}"
                    ?disabled=${!w}
                    @click=${w?()=>this.openMoreInfo(w):l}
                >
                    <div class="kpi-top">
                        <span>Download</span>
                        ${m(t)}
                    </div>
                    <div class="kpi-value">${o(d)}</div>
                    <div class="kpi-sub">${h} · ${v}%</div>
                </button>

                <button
                    type="button"
                    class="kpi-tile ${T?`clickable`:``}"
                    ?disabled=${!T}
                    @click=${T?()=>this.openMoreInfo(T):l}
                >
                    <div class="kpi-top">
                        <span>Upload</span>
                        ${m(r)}
                    </div>
                    <div class="kpi-value">${o(f)}</div>
                    <div class="kpi-sub">${g} · ${y}%</div>
                </button>
            </div>

            <div class="kpi-tile">
                <div class="item-top">
                    <span class="kpi-top">Total Traffic (${a})</span>
                    <span class="item-value">
                        ${o(p)} (${_})
                    </span>
                </div>
                <div class="bar-track" aria-hidden="true">
                    <div
                        class="bar-fill"
                        style=${`width: ${v}%`}
                    ></div>
                    <div
                        class="bar-fill secondary"
                        style=${`width: ${y}%`}
                    ></div>
                </div>
            </div>
        `}};p({tag:s,editorTag:i,card:h,editor:class extends f{constructor(){super(s,e)}},name:`UniFi Internet Activity`,description:`Historical WAN download/upload activity and live gateway throughput.`});