import{B as e,Dt as t,R as n,X as r,a as i,h as a,j as o,k as s,m as c,n as l,t as u,tt as d,v as f,w as p}from"./chunks/register-dashboard-card-BLc74zCS.js";u({tag:c,editorTag:a,card:class extends l{static editorTag=a;get cardType(){return`custom:${c}`}get sourceCommand(){return t}get subscribeCommand(){return`unifi_insights/timeline/subscribe`}get defaultTitle(){return`Event Timeline`}get headerIcon(){return d}renderHeaderBadge(){if(!this.snapshot)return s;let e=Array.isArray(this.snapshot.items)?this.snapshot.items:[];return o`<span class="chip ${e.length>0?`warning`:`ok`}">
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
                ${i.slice(0,6).map(e=>{let t=e.source??{},i=String(e.kind??`event`),a=String(e.severity??`info`),c=f(e.timestamp);return o`
                        <div class="item-card">
                            <div
                                class="item-icon ${a===`warning`?`offline`:`online`}"
                            >
                                ${p(i===`ring`?n:r)}
                            </div>
                            <div class="item-body">
                                <div class="item-top">
                                    <span class="item-name">
                                        ${String(t.name??`Src`)}
                                    </span>
                                    <span
                                        class="chip ${a===`warning`?`warning`:`ok`}"
                                    >
                                        ${i}
                                    </span>
                                </div>
                                ${c?o`<div class="item-meta">
                                          <span>${c}</span>
                                      </div>`:s}
                            </div>
                        </div>
                    `})}
            </div>
        `}},editor:class extends i{constructor(){super(c,t)}},name:`UniFi Event Timeline`,description:`Recent UniFi Protect security and device activity timeline.`});