import{B as e,Dt as t,R as n,X as r,f as i,g as a,j as o,k as s,n as c,p as l,r as u,t as d,tt as f,w as p}from"./chunks/register-dashboard-card-DFoe8fM2.js";d({tag:i,editorTag:l,card:class extends c{static editorTag=l;get cardType(){return`custom:${i}`}get sourceCommand(){return t}get subscribeCommand(){return`unifi_insights/timeline/subscribe`}get defaultTitle(){return`Event Timeline`}get headerIcon(){return f}renderHeaderBadge(){if(!this.snapshot)return s;let e=Array.isArray(this.snapshot.items)?this.snapshot.items:[];return o`<span class="chip ${e.length>0?`warning`:`ok`}">
            ${e.length} Events
        </span>`}renderContent(){let t=this.snapshot;if(!t)return o`<div class="state">No events</div>`;let i=Array.isArray(t.items)?t.items:[];return i.length===0?o`
                <div class="empty-hero">
                    <div class="icon-badge">
                        ${p(e)}
                    </div>
                    <div class="empty-title">All Quiet · 0 Events</div>
                    <div class="empty-sub">
                        No security or motion detections in the recent window.
                    </div>
                </div>
            `:o`
            <div class="list">
                ${i.slice(0,6).map(e=>{let t=e.source??{},i=String(e.kind??`event`),c=String(e.severity??`info`),l=a(e.timestamp);return o`
                        <div class="item-card">
                            <div
                                class="item-icon ${c===`warning`?`offline`:`online`}"
                            >
                                ${p(i===`ring`?n:r)}
                            </div>
                            <div class="item-body">
                                <div class="item-top">
                                    <span class="item-name">
                                        ${String(t.name??`Src`)}
                                    </span>
                                    <span
                                        class="chip ${c===`warning`?`warning`:`ok`}"
                                    >
                                        ${i}
                                    </span>
                                </div>
                                ${l?o`<div class="item-meta">
                                          <span>${l}</span>
                                      </div>`:s}
                            </div>
                        </div>
                    `})}
            </div>
        `}},editor:class extends u{constructor(){super(i,t)}},name:`UniFi Event Timeline`,description:`Recent UniFi Protect security and device activity timeline.`});