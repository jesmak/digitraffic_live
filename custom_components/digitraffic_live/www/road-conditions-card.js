/*! road-conditions-card 1.5.0 | MIT License | Includes Weather Icons by Erik Flowers, SIL OFL 1.1, see https://github.com/jesmak/digitraffic_live/blob/main/LICENSE-weather-icons */
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __decorateClass = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc(target, key) : target;
  for (var i5 = decorators.length - 1, decorator; i5 >= 0; i5--)
    if (decorator = decorators[i5])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp(target, key, result);
  return result;
};

// node_modules/@lit/reactive-element/css-tag.js
var t = globalThis;
var e = t.ShadowRoot && (void 0 === t.ShadyCSS || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype;
var s = /* @__PURE__ */ Symbol();
var o = /* @__PURE__ */ new WeakMap();
var n = class {
  constructor(t3, e5, o6) {
    if (this._$cssResult$ = true, o6 !== s) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t3, this.t = e5;
  }
  get styleSheet() {
    let t3 = this.o;
    const s4 = this.t;
    if (e && void 0 === t3) {
      const e5 = void 0 !== s4 && 1 === s4.length;
      e5 && (t3 = o.get(s4)), void 0 === t3 && ((this.o = t3 = new CSSStyleSheet()).replaceSync(this.cssText), e5 && o.set(s4, t3));
    }
    return t3;
  }
  toString() {
    return this.cssText;
  }
};
var r = (t3) => new n("string" == typeof t3 ? t3 : t3 + "", void 0, s);
var i = (t3, ...e5) => {
  const o6 = 1 === t3.length ? t3[0] : e5.reduce((e6, s4, o7) => e6 + ((t4) => {
    if (true === t4._$cssResult$) return t4.cssText;
    if ("number" == typeof t4) return t4;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t4 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s4) + t3[o7 + 1], t3[0]);
  return new n(o6, t3, s);
};
var S = (s4, o6) => {
  if (e) s4.adoptedStyleSheets = o6.map((t3) => t3 instanceof CSSStyleSheet ? t3 : t3.styleSheet);
  else for (const e5 of o6) {
    const o7 = document.createElement("style"), n5 = t.litNonce;
    void 0 !== n5 && o7.setAttribute("nonce", n5), o7.textContent = e5.cssText, s4.appendChild(o7);
  }
};
var c = e ? (t3) => t3 : (t3) => t3 instanceof CSSStyleSheet ? ((t4) => {
  let e5 = "";
  for (const s4 of t4.cssRules) e5 += s4.cssText;
  return r(e5);
})(t3) : t3;

// node_modules/@lit/reactive-element/reactive-element.js
var { is: i2, defineProperty: e2, getOwnPropertyDescriptor: h, getOwnPropertyNames: r2, getOwnPropertySymbols: o2, getPrototypeOf: n2 } = Object;
var a = globalThis;
var c2 = a.trustedTypes;
var l = c2 ? c2.emptyScript : "";
var p = a.reactiveElementPolyfillSupport;
var d = (t3, s4) => t3;
var u = { toAttribute(t3, s4) {
  switch (s4) {
    case Boolean:
      t3 = t3 ? l : null;
      break;
    case Object:
    case Array:
      t3 = null == t3 ? t3 : JSON.stringify(t3);
  }
  return t3;
}, fromAttribute(t3, s4) {
  let i5 = t3;
  switch (s4) {
    case Boolean:
      i5 = null !== t3;
      break;
    case Number:
      i5 = null === t3 ? null : Number(t3);
      break;
    case Object:
    case Array:
      try {
        i5 = JSON.parse(t3);
      } catch (t4) {
        i5 = null;
      }
  }
  return i5;
} };
var f = (t3, s4) => !i2(t3, s4);
var b = { attribute: true, type: String, converter: u, reflect: false, useDefault: false, hasChanged: f };
Symbol.metadata ?? (Symbol.metadata = /* @__PURE__ */ Symbol("metadata")), a.litPropertyMetadata ?? (a.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
var y = class extends HTMLElement {
  static addInitializer(t3) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t3);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t3, s4 = b) {
    if (s4.state && (s4.attribute = false), this._$Ei(), this.prototype.hasOwnProperty(t3) && ((s4 = Object.create(s4)).wrapped = true), this.elementProperties.set(t3, s4), !s4.noAccessor) {
      const i5 = /* @__PURE__ */ Symbol(), h3 = this.getPropertyDescriptor(t3, i5, s4);
      void 0 !== h3 && e2(this.prototype, t3, h3);
    }
  }
  static getPropertyDescriptor(t3, s4, i5) {
    const { get: e5, set: r6 } = h(this.prototype, t3) ?? { get() {
      return this[s4];
    }, set(t4) {
      this[s4] = t4;
    } };
    return { get: e5, set(s5) {
      const h3 = e5?.call(this);
      r6?.call(this, s5), this.requestUpdate(t3, h3, i5);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t3) {
    return this.elementProperties.get(t3) ?? b;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d("elementProperties"))) return;
    const t3 = n2(this);
    t3.finalize(), void 0 !== t3.l && (this.l = [...t3.l]), this.elementProperties = new Map(t3.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d("finalized"))) return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d("properties"))) {
      const t4 = this.properties, s4 = [...r2(t4), ...o2(t4)];
      for (const i5 of s4) this.createProperty(i5, t4[i5]);
    }
    const t3 = this[Symbol.metadata];
    if (null !== t3) {
      const s4 = litPropertyMetadata.get(t3);
      if (void 0 !== s4) for (const [t4, i5] of s4) this.elementProperties.set(t4, i5);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t4, s4] of this.elementProperties) {
      const i5 = this._$Eu(t4, s4);
      void 0 !== i5 && this._$Eh.set(i5, t4);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s4) {
    const i5 = [];
    if (Array.isArray(s4)) {
      const e5 = new Set(s4.flat(1 / 0).reverse());
      for (const s5 of e5) i5.unshift(c(s5));
    } else void 0 !== s4 && i5.push(c(s4));
    return i5;
  }
  static _$Eu(t3, s4) {
    const i5 = s4.attribute;
    return false === i5 ? void 0 : "string" == typeof i5 ? i5 : "string" == typeof t3 ? t3.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t3) => this.enableUpdating = t3), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t3) => t3(this));
  }
  addController(t3) {
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t3), void 0 !== this.renderRoot && this.isConnected && t3.hostConnected?.();
  }
  removeController(t3) {
    this._$EO?.delete(t3);
  }
  _$E_() {
    const t3 = /* @__PURE__ */ new Map(), s4 = this.constructor.elementProperties;
    for (const i5 of s4.keys()) this.hasOwnProperty(i5) && (t3.set(i5, this[i5]), delete this[i5]);
    t3.size > 0 && (this._$Ep = t3);
  }
  createRenderRoot() {
    const t3 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S(t3, this.constructor.elementStyles), t3;
  }
  connectedCallback() {
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(true), this._$EO?.forEach((t3) => t3.hostConnected?.());
  }
  enableUpdating(t3) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t3) => t3.hostDisconnected?.());
  }
  attributeChangedCallback(t3, s4, i5) {
    this._$AK(t3, i5);
  }
  _$ET(t3, s4) {
    const i5 = this.constructor.elementProperties.get(t3), e5 = this.constructor._$Eu(t3, i5);
    if (void 0 !== e5 && true === i5.reflect) {
      const h3 = (void 0 !== i5.converter?.toAttribute ? i5.converter : u).toAttribute(s4, i5.type);
      this._$Em = t3, null == h3 ? this.removeAttribute(e5) : this.setAttribute(e5, h3), this._$Em = null;
    }
  }
  _$AK(t3, s4) {
    const i5 = this.constructor, e5 = i5._$Eh.get(t3);
    if (void 0 !== e5 && this._$Em !== e5) {
      const t4 = i5.getPropertyOptions(e5), h3 = "function" == typeof t4.converter ? { fromAttribute: t4.converter } : void 0 !== t4.converter?.fromAttribute ? t4.converter : u;
      this._$Em = e5;
      const r6 = h3.fromAttribute(s4, t4.type);
      this[e5] = r6 ?? this._$Ej?.get(e5) ?? r6, this._$Em = null;
    }
  }
  requestUpdate(t3, s4, i5, e5 = false, h3) {
    if (void 0 !== t3) {
      const r6 = this.constructor;
      if (false === e5 && (h3 = this[t3]), i5 ?? (i5 = r6.getPropertyOptions(t3)), !((i5.hasChanged ?? f)(h3, s4) || i5.useDefault && i5.reflect && h3 === this._$Ej?.get(t3) && !this.hasAttribute(r6._$Eu(t3, i5)))) return;
      this.C(t3, s4, i5);
    }
    false === this.isUpdatePending && (this._$ES = this._$EP());
  }
  C(t3, s4, { useDefault: i5, reflect: e5, wrapped: h3 }, r6) {
    i5 && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t3) && (this._$Ej.set(t3, r6 ?? s4 ?? this[t3]), true !== h3 || void 0 !== r6) || (this._$AL.has(t3) || (this.hasUpdated || i5 || (s4 = void 0), this._$AL.set(t3, s4)), true === e5 && this._$Em !== t3 && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t3));
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t4) {
      Promise.reject(t4);
    }
    const t3 = this.scheduleUpdate();
    return null != t3 && await t3, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [t5, s5] of this._$Ep) this[t5] = s5;
        this._$Ep = void 0;
      }
      const t4 = this.constructor.elementProperties;
      if (t4.size > 0) for (const [s5, i5] of t4) {
        const { wrapped: t5 } = i5, e5 = this[s5];
        true !== t5 || this._$AL.has(s5) || void 0 === e5 || this.C(s5, void 0, i5, e5);
      }
    }
    let t3 = false;
    const s4 = this._$AL;
    try {
      t3 = this.shouldUpdate(s4), t3 ? (this.willUpdate(s4), this._$EO?.forEach((t4) => t4.hostUpdate?.()), this.update(s4)) : this._$EM();
    } catch (s5) {
      throw t3 = false, this._$EM(), s5;
    }
    t3 && this._$AE(s4);
  }
  willUpdate(t3) {
  }
  _$AE(t3) {
    this._$EO?.forEach((t4) => t4.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t3)), this.updated(t3);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = false;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t3) {
    return true;
  }
  update(t3) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t4) => this._$ET(t4, this[t4]))), this._$EM();
  }
  updated(t3) {
  }
  firstUpdated(t3) {
  }
};
y.elementStyles = [], y.shadowRootOptions = { mode: "open" }, y[d("elementProperties")] = /* @__PURE__ */ new Map(), y[d("finalized")] = /* @__PURE__ */ new Map(), p?.({ ReactiveElement: y }), (a.reactiveElementVersions ?? (a.reactiveElementVersions = [])).push("2.1.2");

// node_modules/lit-html/lit-html.js
var t2 = globalThis;
var i3 = (t3) => t3;
var s2 = t2.trustedTypes;
var e3 = s2 ? s2.createPolicy("lit-html", { createHTML: (t3) => t3 }) : void 0;
var h2 = "$lit$";
var o3 = `lit$${Math.random().toFixed(9).slice(2)}$`;
var n3 = "?" + o3;
var r3 = `<${n3}>`;
var l2 = document;
var c3 = () => l2.createComment("");
var a2 = (t3) => null === t3 || "object" != typeof t3 && "function" != typeof t3;
var u2 = Array.isArray;
var d2 = (t3) => u2(t3) || "function" == typeof t3?.[Symbol.iterator];
var f2 = "[ 	\n\f\r]";
var v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g;
var _ = /-->/g;
var m = />/g;
var p2 = RegExp(`>|${f2}(?:([^\\s"'>=/]+)(${f2}*=${f2}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g");
var g = /'/g;
var $ = /"/g;
var y2 = /^(?:script|style|textarea|title)$/i;
var x = (t3) => (i5, ...s4) => ({ _$litType$: t3, strings: i5, values: s4 });
var b2 = x(1);
var w = x(2);
var T = x(3);
var E = /* @__PURE__ */ Symbol.for("lit-noChange");
var A = /* @__PURE__ */ Symbol.for("lit-nothing");
var C = /* @__PURE__ */ new WeakMap();
var P = l2.createTreeWalker(l2, 129);
function V(t3, i5) {
  if (!u2(t3) || !t3.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return void 0 !== e3 ? e3.createHTML(i5) : i5;
}
var N = (t3, i5) => {
  const s4 = t3.length - 1, e5 = [];
  let n5, l3 = 2 === i5 ? "<svg>" : 3 === i5 ? "<math>" : "", c4 = v;
  for (let i6 = 0; i6 < s4; i6++) {
    const s5 = t3[i6];
    let a3, u3, d3 = -1, f3 = 0;
    for (; f3 < s5.length && (c4.lastIndex = f3, u3 = c4.exec(s5), null !== u3); ) f3 = c4.lastIndex, c4 === v ? "!--" === u3[1] ? c4 = _ : void 0 !== u3[1] ? c4 = m : void 0 !== u3[2] ? (y2.test(u3[2]) && (n5 = RegExp("</" + u3[2], "g")), c4 = p2) : void 0 !== u3[3] && (c4 = p2) : c4 === p2 ? ">" === u3[0] ? (c4 = n5 ?? v, d3 = -1) : void 0 === u3[1] ? d3 = -2 : (d3 = c4.lastIndex - u3[2].length, a3 = u3[1], c4 = void 0 === u3[3] ? p2 : '"' === u3[3] ? $ : g) : c4 === $ || c4 === g ? c4 = p2 : c4 === _ || c4 === m ? c4 = v : (c4 = p2, n5 = void 0);
    const x2 = c4 === p2 && t3[i6 + 1].startsWith("/>") ? " " : "";
    l3 += c4 === v ? s5 + r3 : d3 >= 0 ? (e5.push(a3), s5.slice(0, d3) + h2 + s5.slice(d3) + o3 + x2) : s5 + o3 + (-2 === d3 ? i6 : x2);
  }
  return [V(t3, l3 + (t3[s4] || "<?>") + (2 === i5 ? "</svg>" : 3 === i5 ? "</math>" : "")), e5];
};
var S2 = class _S {
  constructor({ strings: t3, _$litType$: i5 }, e5) {
    let r6;
    this.parts = [];
    let l3 = 0, a3 = 0;
    const u3 = t3.length - 1, d3 = this.parts, [f3, v2] = N(t3, i5);
    if (this.el = _S.createElement(f3, e5), P.currentNode = this.el.content, 2 === i5 || 3 === i5) {
      const t4 = this.el.content.firstChild;
      t4.replaceWith(...t4.childNodes);
    }
    for (; null !== (r6 = P.nextNode()) && d3.length < u3; ) {
      if (1 === r6.nodeType) {
        if (r6.hasAttributes()) for (const t4 of r6.getAttributeNames()) if (t4.endsWith(h2)) {
          const i6 = v2[a3++], s4 = r6.getAttribute(t4).split(o3), e6 = /([.?@])?(.*)/.exec(i6);
          d3.push({ type: 1, index: l3, name: e6[2], strings: s4, ctor: "." === e6[1] ? I : "?" === e6[1] ? L : "@" === e6[1] ? z : H }), r6.removeAttribute(t4);
        } else t4.startsWith(o3) && (d3.push({ type: 6, index: l3 }), r6.removeAttribute(t4));
        if (y2.test(r6.tagName)) {
          const t4 = r6.textContent.split(o3), i6 = t4.length - 1;
          if (i6 > 0) {
            r6.textContent = s2 ? s2.emptyScript : "";
            for (let s4 = 0; s4 < i6; s4++) r6.append(t4[s4], c3()), P.nextNode(), d3.push({ type: 2, index: ++l3 });
            r6.append(t4[i6], c3());
          }
        }
      } else if (8 === r6.nodeType) if (r6.data === n3) d3.push({ type: 2, index: l3 });
      else {
        let t4 = -1;
        for (; -1 !== (t4 = r6.data.indexOf(o3, t4 + 1)); ) d3.push({ type: 7, index: l3 }), t4 += o3.length - 1;
      }
      l3++;
    }
  }
  static createElement(t3, i5) {
    const s4 = l2.createElement("template");
    return s4.innerHTML = t3, s4;
  }
};
function M(t3, i5, s4 = t3, e5) {
  if (i5 === E) return i5;
  let h3 = void 0 !== e5 ? s4._$Co?.[e5] : s4._$Cl;
  const o6 = a2(i5) ? void 0 : i5._$litDirective$;
  return h3?.constructor !== o6 && (h3?._$AO?.(false), void 0 === o6 ? h3 = void 0 : (h3 = new o6(t3), h3._$AT(t3, s4, e5)), void 0 !== e5 ? (s4._$Co ?? (s4._$Co = []))[e5] = h3 : s4._$Cl = h3), void 0 !== h3 && (i5 = M(t3, h3._$AS(t3, i5.values), h3, e5)), i5;
}
var R = class {
  constructor(t3, i5) {
    this._$AV = [], this._$AN = void 0, this._$AD = t3, this._$AM = i5;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t3) {
    const { el: { content: i5 }, parts: s4 } = this._$AD, e5 = (t3?.creationScope ?? l2).importNode(i5, true);
    P.currentNode = e5;
    let h3 = P.nextNode(), o6 = 0, n5 = 0, r6 = s4[0];
    for (; void 0 !== r6; ) {
      if (o6 === r6.index) {
        let i6;
        2 === r6.type ? i6 = new k(h3, h3.nextSibling, this, t3) : 1 === r6.type ? i6 = new r6.ctor(h3, r6.name, r6.strings, this, t3) : 6 === r6.type && (i6 = new Z(h3, this, t3)), this._$AV.push(i6), r6 = s4[++n5];
      }
      o6 !== r6?.index && (h3 = P.nextNode(), o6++);
    }
    return P.currentNode = l2, e5;
  }
  p(t3) {
    let i5 = 0;
    for (const s4 of this._$AV) void 0 !== s4 && (void 0 !== s4.strings ? (s4._$AI(t3, s4, i5), i5 += s4.strings.length - 2) : s4._$AI(t3[i5])), i5++;
  }
};
var k = class _k {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t3, i5, s4, e5) {
    this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t3, this._$AB = i5, this._$AM = s4, this.options = e5, this._$Cv = e5?.isConnected ?? true;
  }
  get parentNode() {
    let t3 = this._$AA.parentNode;
    const i5 = this._$AM;
    return void 0 !== i5 && 11 === t3?.nodeType && (t3 = i5.parentNode), t3;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t3, i5 = this) {
    t3 = M(this, t3, i5), a2(t3) ? t3 === A || null == t3 || "" === t3 ? (this._$AH !== A && this._$AR(), this._$AH = A) : t3 !== this._$AH && t3 !== E && this._(t3) : void 0 !== t3._$litType$ ? this.$(t3) : void 0 !== t3.nodeType ? this.T(t3) : d2(t3) ? this.k(t3) : this._(t3);
  }
  O(t3) {
    return this._$AA.parentNode.insertBefore(t3, this._$AB);
  }
  T(t3) {
    this._$AH !== t3 && (this._$AR(), this._$AH = this.O(t3));
  }
  _(t3) {
    this._$AH !== A && a2(this._$AH) ? this._$AA.nextSibling.data = t3 : this.T(l2.createTextNode(t3)), this._$AH = t3;
  }
  $(t3) {
    const { values: i5, _$litType$: s4 } = t3, e5 = "number" == typeof s4 ? this._$AC(t3) : (void 0 === s4.el && (s4.el = S2.createElement(V(s4.h, s4.h[0]), this.options)), s4);
    if (this._$AH?._$AD === e5) this._$AH.p(i5);
    else {
      const t4 = new R(e5, this), s5 = t4.u(this.options);
      t4.p(i5), this.T(s5), this._$AH = t4;
    }
  }
  _$AC(t3) {
    let i5 = C.get(t3.strings);
    return void 0 === i5 && C.set(t3.strings, i5 = new S2(t3)), i5;
  }
  k(t3) {
    u2(this._$AH) || (this._$AH = [], this._$AR());
    const i5 = this._$AH;
    let s4, e5 = 0;
    for (const h3 of t3) e5 === i5.length ? i5.push(s4 = new _k(this.O(c3()), this.O(c3()), this, this.options)) : s4 = i5[e5], s4._$AI(h3), e5++;
    e5 < i5.length && (this._$AR(s4 && s4._$AB.nextSibling, e5), i5.length = e5);
  }
  _$AR(t3 = this._$AA.nextSibling, s4) {
    for (this._$AP?.(false, true, s4); t3 !== this._$AB; ) {
      const s5 = i3(t3).nextSibling;
      i3(t3).remove(), t3 = s5;
    }
  }
  setConnected(t3) {
    void 0 === this._$AM && (this._$Cv = t3, this._$AP?.(t3));
  }
};
var H = class {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t3, i5, s4, e5, h3) {
    this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t3, this.name = i5, this._$AM = e5, this.options = h3, s4.length > 2 || "" !== s4[0] || "" !== s4[1] ? (this._$AH = Array(s4.length - 1).fill(new String()), this.strings = s4) : this._$AH = A;
  }
  _$AI(t3, i5 = this, s4, e5) {
    const h3 = this.strings;
    let o6 = false;
    if (void 0 === h3) t3 = M(this, t3, i5, 0), o6 = !a2(t3) || t3 !== this._$AH && t3 !== E, o6 && (this._$AH = t3);
    else {
      const e6 = t3;
      let n5, r6;
      for (t3 = h3[0], n5 = 0; n5 < h3.length - 1; n5++) r6 = M(this, e6[s4 + n5], i5, n5), r6 === E && (r6 = this._$AH[n5]), o6 || (o6 = !a2(r6) || r6 !== this._$AH[n5]), r6 === A ? t3 = A : t3 !== A && (t3 += (r6 ?? "") + h3[n5 + 1]), this._$AH[n5] = r6;
    }
    o6 && !e5 && this.j(t3);
  }
  j(t3) {
    t3 === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t3 ?? "");
  }
};
var I = class extends H {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t3) {
    this.element[this.name] = t3 === A ? void 0 : t3;
  }
};
var L = class extends H {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t3) {
    this.element.toggleAttribute(this.name, !!t3 && t3 !== A);
  }
};
var z = class extends H {
  constructor(t3, i5, s4, e5, h3) {
    super(t3, i5, s4, e5, h3), this.type = 5;
  }
  _$AI(t3, i5 = this) {
    if ((t3 = M(this, t3, i5, 0) ?? A) === E) return;
    const s4 = this._$AH, e5 = t3 === A && s4 !== A || t3.capture !== s4.capture || t3.once !== s4.once || t3.passive !== s4.passive, h3 = t3 !== A && (s4 === A || e5);
    e5 && this.element.removeEventListener(this.name, this, s4), h3 && this.element.addEventListener(this.name, this, t3), this._$AH = t3;
  }
  handleEvent(t3) {
    "function" == typeof this._$AH ? this._$AH.call(this.options?.host ?? this.element, t3) : this._$AH.handleEvent(t3);
  }
};
var Z = class {
  constructor(t3, i5, s4) {
    this.element = t3, this.type = 6, this._$AN = void 0, this._$AM = i5, this.options = s4;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t3) {
    M(this, t3);
  }
};
var B = t2.litHtmlPolyfillSupport;
B?.(S2, k), (t2.litHtmlVersions ?? (t2.litHtmlVersions = [])).push("3.3.3");
var D = (t3, i5, s4) => {
  const e5 = s4?.renderBefore ?? i5;
  let h3 = e5._$litPart$;
  if (void 0 === h3) {
    const t4 = s4?.renderBefore ?? null;
    e5._$litPart$ = h3 = new k(i5.insertBefore(c3(), t4), t4, void 0, s4 ?? {});
  }
  return h3._$AI(t3), h3;
};

// node_modules/lit-element/lit-element.js
var s3 = globalThis;
var i4 = class extends y {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var _a;
    const t3 = super.createRenderRoot();
    return (_a = this.renderOptions).renderBefore ?? (_a.renderBefore = t3.firstChild), t3;
  }
  update(t3) {
    const r6 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t3), this._$Do = D(r6, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(true);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(false);
  }
  render() {
    return E;
  }
};
i4._$litElement$ = true, i4["finalized"] = true, s3.litElementHydrateSupport?.({ LitElement: i4 });
var o4 = s3.litElementPolyfillSupport;
o4?.({ LitElement: i4 });
(s3.litElementVersions ?? (s3.litElementVersions = [])).push("4.2.2");

// node_modules/@lit/reactive-element/decorators/property.js
var o5 = { attribute: true, type: String, converter: u, reflect: false, hasChanged: f };
var r4 = (t3 = o5, e5, r6) => {
  const { kind: n5, metadata: i5 } = r6;
  let s4 = globalThis.litPropertyMetadata.get(i5);
  if (void 0 === s4 && globalThis.litPropertyMetadata.set(i5, s4 = /* @__PURE__ */ new Map()), "setter" === n5 && ((t3 = Object.create(t3)).wrapped = true), s4.set(r6.name, t3), "accessor" === n5) {
    const { name: o6 } = r6;
    return { set(r7) {
      const n6 = e5.get.call(this);
      e5.set.call(this, r7), this.requestUpdate(o6, n6, t3, true, r7);
    }, init(e6) {
      return void 0 !== e6 && this.C(o6, void 0, t3, e6), e6;
    } };
  }
  if ("setter" === n5) {
    const { name: o6 } = r6;
    return function(r7) {
      const n6 = this[o6];
      e5.call(this, r7), this.requestUpdate(o6, n6, t3, true, r7);
    };
  }
  throw Error("Unsupported decorator location: " + n5);
};
function n4(t3) {
  return (e5, o6) => "object" == typeof o6 ? r4(t3, e5, o6) : ((t4, e6, o7) => {
    const r6 = e6.hasOwnProperty(o7);
    return e6.constructor.createProperty(o7, t4), r6 ? Object.getOwnPropertyDescriptor(e6, o7) : void 0;
  })(t3, e5, o6);
}

// node_modules/@lit/reactive-element/decorators/state.js
function r5(r6) {
  return n4({ ...r6, state: true, attribute: false });
}

// src/const.ts
var CARD_VERSION = "1.5.0";
var PLATFORM = "digitraffic_live";
var SENSORS = [
  "road_temperature",
  "air_temperature",
  "road_surface",
  "grip",
  "grip_condition",
  "road_warning",
  "wind_speed",
  "wind_gusts",
  "precipitation",
  "precipitation_type",
  "rain_intensity",
  "visibility"
];
var GRIP_SCALE = ["very_slippery", "slippery", "fair_winter", "good_winter", "fair", "good"];
var GUST_MARGIN = 3;
var WIND_UNITS = {
  "m/s": 1,
  "km/h": 1 / 3.6,
  mph: 0.44704,
  kn: 0.514444,
  "ft/s": 0.3048
};
var ICONS = {
  road_temperature: "mdi:road-variant",
  air_temperature: "wi:thermometer",
  road_surface: "mdi:layers-outline",
  wind: "wi:strong-wind",
  visibility: "wi:fog",
  road_warning: "mdi:alert-outline"
};
var PRECIPITATION_TYPE_ICONS = {
  none: "wi:cloud",
  very_light: "wi:sprinkle",
  drizzle: "wi:sprinkle",
  rain: "wi:rain",
  snow: "wi:snow",
  wet_sleet: "wi:sleet",
  sleet: "wi:sleet",
  hail: "wi:hail",
  ice_crystals: "wi:snowflake-cold",
  snow_grains: "wi:snowflake-cold",
  graupel: "wi:hail",
  freezing_drizzle: "wi:rain-mix",
  freezing_rain: "wi:rain-mix"
};
var FREEZING = ["freezing_drizzle", "freezing_rain"];
var HEAVY = ["heavy", "heavy_snow"];
var HEAVY_TEXTS = {
  very_light: "heavy_rain",
  drizzle: "heavy_rain",
  rain: "heavy_rain",
  snow: "heavy_snow",
  snow_grains: "heavy_snow",
  wet_sleet: "heavy_sleet",
  sleet: "heavy_sleet"
};
var PRECIPITATION_ICONS = {
  none: ["wi:cloud", "none"],
  light: ["wi:sprinkle", "rain"],
  moderate: ["wi:showers", "rain"],
  heavy: ["wi:rain", "heavy_rain"],
  light_snow: ["wi:sleet", "snow_or_sleet"],
  moderate_snow: ["wi:snow", "snow_or_sleet"],
  heavy_snow: ["wi:snow", "heavy_snow_or_sleet"]
};

// src/height.ts
var HEIGHT_MODES = ["auto", "fixed", "max"];
var pixels = (value) => value == null || typeof value === "number" && Number.isFinite(value) && value > 0;
function validHeight(config) {
  return (config.height_mode == null || HEIGHT_MODES.includes(config.height_mode)) && pixels(config.height) && pixels(config.max_height);
}
function heightMode(config) {
  return config.height_mode ?? (config.height ? "fixed" : config.max_height ? "max" : "auto");
}
var ROW_HEIGHT = 56;
var ROW_GAP = 8;
function heightStyle(config, layout, minimum = 0) {
  const rows = config.grid_options ? config.grid_options.rows : config.layout_options?.grid_rows;
  if (layout === "grid" && typeof rows === "number") {
    return "height: 100%";
  }
  const mode = heightMode(config);
  if (mode === "fixed" && config.height) {
    return `height: ${Math.max(config.height, minimum)}px`;
  }
  return mode === "max" && config.max_height ? `max-height: ${Math.max(config.max_height, minimum)}px` : "";
}
function gridMinRows(minimum) {
  return Math.max(1, Math.ceil((minimum + ROW_GAP) / (ROW_HEIGHT + ROW_GAP)));
}
function heightCardSize(config, content, minimum = 0) {
  const mode = heightMode(config);
  if (mode === "fixed" && config.height) {
    return Math.max(1, Math.round(Math.max(config.height, minimum) / 50));
  }
  return mode === "max" && config.max_height ? Math.max(1, Math.min(content, Math.round(Math.max(config.max_height, minimum) / 50))) : content;
}
function heightSchema(config, text) {
  const mode = heightMode(config);
  const field = (name) => ({
    name,
    selector: { number: { min: 100, max: 2e3, step: 10, unit_of_measurement: "px", mode: "box" } }
  });
  return [
    {
      name: "height_mode",
      selector: {
        select: { mode: "dropdown", options: HEIGHT_MODES.map((value) => ({ value, label: text(`editor.height_mode_${value}`) })) }
      }
    },
    ...mode === "fixed" ? [field("height")] : mode === "max" ? [field("max_height")] : []
  ];
}
function heightData(config) {
  return { ...config, height_mode: heightMode(config) };
}
function tidyHeight(config) {
  const tidied = { ...config };
  for (const key of ["height", "max_height"]) {
    if (!tidied[key]) {
      delete tidied[key];
    }
  }
  if (!tidied.height_mode || heightMode({ ...tidied, height_mode: void 0 }) === tidied.height_mode) {
    delete tidied.height_mode;
  }
  return tidied;
}

// src/localize/languages/en.json
var en_default = {
  common: {
    name: "Road conditions",
    description: "Grip, temperatures, road surface, wind, rain and visibility from road weather stations",
    invalid_configuration: "Invalid configuration. Add at least one road weather station.",
    invalid_height: "Invalid height. height and max_height must be positive numbers of pixels, and height_mode auto, fixed or max.",
    station_without_device: "Invalid configuration. Every station needs its device.",
    no_station: "No sensors found for this station",
    no_readings: "No readings from this station right now"
  },
  labels: {
    road_temperature: "Road temperature",
    air_temperature: "Air temperature",
    road_surface: "Road surface",
    wind: "Wind",
    precipitation: "Precipitation",
    visibility: "Visibility",
    road_warning: "Road weather warning"
  },
  scale: {
    very_slippery: "Very slippery",
    winter: "Winter road",
    good: "Good grip"
  },
  precipitation: {
    none: "No rain",
    very_light: "Light",
    drizzle: "Drizzle",
    rain: "Rain",
    snow: "Snow",
    wet_sleet: "Wet sleet",
    sleet: "Sleet",
    hail: "Hail",
    ice_crystals: "Ice crystals",
    snow_grains: "Snow grains",
    graupel: "Graupel",
    freezing_drizzle: "Freezing drizzle",
    freezing_rain: "Freezing rain",
    snow_or_sleet: "Snow/sleet",
    heavy_rain: "Heavy rain",
    heavy_snow: "Heavy snow",
    heavy_sleet: "Heavy sleet",
    heavy_snow_or_sleet: "Heavy snow/sleet"
  },
  editor: {
    title: "Title",
    stations: "Stations",
    stations_helper: "Road weather stations of Digitraffic Live. The card has two modes. With a single station, it shows full details in a roomier layout. With several stations, it shows the details condensed, one row per station.",
    device: "Road weather station",
    name: "Name",
    name_helper: "Replaces the station's own name",
    height_mode: "Height",
    height_mode_helper: "A height set in the layout tab of a sections view is used instead.",
    height_mode_auto: "Fits the content",
    height_mode_fixed: "Fixed",
    height_mode_max: "Grows up to a limit",
    height: "Fixed height",
    height_helper: "The card is always this tall, and the rest scrolls inside it.",
    max_height: "Maximum height",
    max_height_helper: "The card grows with its content up to this height, and then the rest scrolls."
  }
};

// src/localize/languages/fi.json
var fi_default = {
  common: {
    name: "Keli",
    description: "Ties\xE4\xE4asemien pito, l\xE4mp\xF6tilat, tienpinta, tuuli, sade ja n\xE4kyvyys",
    invalid_configuration: "Virheellinen konfiguraatio. Lis\xE4\xE4 v\xE4hint\xE4\xE4n yksi ties\xE4\xE4asema.",
    invalid_height: "Virheellinen korkeus. Korkeuksien (height ja max_height) on oltava positiivisia lukuja pikselein\xE4, ja korkeustilan (height_mode) auto, fixed tai max.",
    station_without_device: "Virheellinen konfiguraatio. Jokaiselle asemalle tarvitaan laite (device).",
    no_station: "Asemalta ei l\xF6ytynyt sensoreita",
    no_readings: "Asemalta ei juuri nyt saada lukemia"
  },
  labels: {
    road_temperature: "Tien l\xE4mp\xF6tila",
    air_temperature: "Ilman l\xE4mp\xF6tila",
    road_surface: "Tienpinta",
    wind: "Tuuli",
    precipitation: "Sade",
    visibility: "N\xE4kyvyys",
    road_warning: "Ties\xE4\xE4varoitus"
  },
  scale: {
    very_slippery: "Eritt\xE4in liukas",
    winter: "Talvikeli",
    good: "Hyv\xE4 pito"
  },
  precipitation: {
    none: "Pouta",
    very_light: "Heikko sade",
    drizzle: "Tihku",
    rain: "Sade",
    snow: "Lumi",
    wet_sleet: "M\xE4rk\xE4 r\xE4nt\xE4",
    sleet: "R\xE4nt\xE4",
    hail: "Rakeita",
    ice_crystals: "J\xE4\xE4kiteit\xE4",
    snow_grains: "Lumijyv\xE4si\xE4",
    graupel: "Lumirakeita",
    freezing_drizzle: "J\xE4\xE4t\xE4v\xE4 tihku",
    freezing_rain: "J\xE4\xE4t\xE4v\xE4 sade",
    snow_or_sleet: "Lumi/r\xE4nt\xE4",
    heavy_rain: "Runsas sade",
    heavy_snow: "Runsas lumisade",
    heavy_sleet: "Runsas r\xE4nt\xE4",
    heavy_snow_or_sleet: "Runsas lumi/r\xE4nt\xE4"
  },
  editor: {
    title: "Otsikko",
    stations: "Asemat",
    stations_helper: "Digitraffic Liven ties\xE4\xE4asemat. Kortilla on kaksi tilaa. Lis\xE4\xE4m\xE4ll\xE4 vain yhden aseman, n\xE4ytet\xE4\xE4n kattavat tiedot v\xE4ljemm\xE4ll\xE4 asettelulla. Lis\xE4\xE4m\xE4ll\xE4 useamman aseman, n\xE4ytet\xE4\xE4n tiedot tiivistettyn\xE4 ja asemakohtaisesti rivitettyn\xE4.",
    device: "Ties\xE4\xE4asema",
    name: "Nimi",
    name_helper: "Korvaa aseman oman nimen",
    height_mode: "Korkeus",
    height_mode_helper: "Osioihin jaetun n\xE4kym\xE4n asettelu-v\xE4lilehdell\xE4 asetettu korkeus ohittaa t\xE4m\xE4n.",
    height_mode_auto: "Sis\xE4ll\xF6n mukaan",
    height_mode_fixed: "Kiinte\xE4",
    height_mode_max: "Kasvaa rajaan asti",
    height: "Kiinte\xE4 korkeus",
    height_helper: "Kortti on aina n\xE4in korkea, ja loput vieriv\xE4t sen sis\xE4ll\xE4.",
    max_height: "Enimm\xE4iskorkeus",
    max_height_helper: "Kortti kasvaa sis\xE4lt\xF6ns\xE4 mukana t\xE4h\xE4n korkeuteen asti, ja sen j\xE4lkeen loput vieriv\xE4t."
  }
};

// src/localize/localize.ts
var FILES = { "./languages/en.json": en_default, "./languages/fi.json": fi_default };
var LANGUAGES = Object.fromEntries(
  Object.entries(FILES).map(([path, table]) => [path.replace(/^.*\/|\.json$/g, "").toLowerCase(), table])
);
var LANGUAGE_CODES = Object.keys(LANGUAGES).sort();
function translate(language, key) {
  const code = (language ?? "en").split(/[-_]/)[0].toLowerCase();
  return read(LANGUAGES[code], key) ?? read(LANGUAGES.en, key) ?? key;
}
function read(table, key) {
  let value = table;
  for (const part of key.split(".")) {
    if (value === null || typeof value !== "object") {
      return void 0;
    }
    value = value[part];
  }
  return typeof value === "string" ? value : void 0;
}
function browserLanguage() {
  return document.documentElement.lang || navigator.language || "en";
}

// src/stations.ts
function stationsOf(stations) {
  return (Array.isArray(stations) ? stations : []).map((station) => typeof station === "string" ? { device: station } : station).filter((station) => !!station?.device);
}
function stationSensors(hass, device) {
  const found = {};
  for (const entry of Object.values(hass.entities ?? {})) {
    const key = entry?.translation_key;
    if (entry && entry.device_id === device && entry.platform === PLATFORM && key && SENSORS.includes(key)) {
      found[key] = entry.entity_id;
    }
  }
  return found;
}
function stationDevices(hass) {
  const devices = Object.values(hass.entities ?? {}).filter((entry) => entry?.platform === PLATFORM && SENSORS.includes(entry.translation_key) && entry.device_id).map((entry) => entry?.device_id);
  return [...new Set(devices)];
}
function stationName(hass, station) {
  const device = hass.devices?.[station.device];
  return station.name || device?.name_by_user || device?.name || station.device;
}
function reading(hass, entityId) {
  const entity = entityId ? hass.states[entityId] : void 0;
  return entity && entity.state !== "unknown" && entity.state !== "unavailable" ? entity : void 0;
}
function scale(condition) {
  const position = GRIP_SCALE.indexOf(condition ?? "");
  return GRIP_SCALE.map((part, index) => ({ condition: index <= position ? GRIP_SCALE[position] : part, lit: index <= position }));
}
function showGusts(speed, gusts) {
  const speedFactor = WIND_UNITS[String(speed.attributes.unit_of_measurement)];
  const gustsFactor = WIND_UNITS[String(gusts.attributes.unit_of_measurement)];
  if (speedFactor === void 0 || gustsFactor === void 0) {
    return Number(gusts.state) > Number(speed.state);
  }
  return Number(gusts.state) * gustsFactor - Number(speed.state) * speedFactor >= GUST_MARGIN;
}
function precipitation(type, code) {
  const heavy = HEAVY.includes(code ?? "");
  if (type && PRECIPITATION_TYPE_ICONS[type]) {
    const icon2 = type === "rain" && code === "light" ? "wi:showers" : PRECIPITATION_TYPE_ICONS[type];
    const text2 = heavy && HEAVY_TEXTS[type] || type;
    return { icon: icon2, text: text2, notable: FREEZING.includes(type) || heavy && type !== "none" };
  }
  const [icon, text] = code && PRECIPITATION_ICONS[code] || ["wi:na", void 0];
  return { icon, text, notable: heavy };
}

// src/editor.ts
function schema(text) {
  return [
    { name: "title", selector: { text: {} } },
    {
      name: "stations",
      required: true,
      selector: {
        object: {
          multiple: true,
          label_field: "device",
          description_field: "name",
          fields: {
            device: {
              label: text("editor.device"),
              required: true,
              // The device classes of a station's sensors, as a station has only those it reports. The integration's
              // other devices have none of them: feeds no class, departures timestamps.
              selector: {
                device: {
                  entity: {
                    integration: PLATFORM,
                    domain: "sensor",
                    device_class: ["temperature", "enum", "wind_speed", "precipitation_intensity", "distance"]
                  }
                }
              }
            },
            // A field inside the object selector takes its helper from here; ha-form's computeHelper doesn't reach it.
            name: { label: text("editor.name"), description: text("editor.name_helper"), selector: { text: {} } }
          }
        }
      }
    }
  ];
}
function compactStations(stations) {
  return stationsOf(stations).map((station) => station.name ? { device: station.device, name: station.name } : station.device);
}
var RoadConditionsCardEditor = class extends i4 {
  constructor() {
    super(...arguments);
    this.config = { type: "custom:road-conditions-card", stations: [] };
  }
  setConfig(config) {
    this.config = { ...config };
  }
  render() {
    if (!this.hass) {
      return A;
    }
    return b2`
            <ha-form
                .hass=${this.hass}
                .data=${{ ...this.config, stations: stationsOf(this.config.stations) }}
                .schema=${schema((key) => this.text(key))}
                .computeLabel=${(entry) => this.text(`editor.${entry.name}`)}
                @value-changed=${(event) => this.changed(event.detail.value)}
            ></ha-form>
            <!-- Home Assistant's list of objects shows no helper text, so the stations' one is drawn here, between the list and
                 the height fields, which are a form of their own so it can sit there. -->
            <p class="helper">${this.text("editor.stations_helper")}</p>
            <ha-form
                class="height"
                .hass=${this.hass}
                .data=${heightData(this.config)}
                .schema=${heightSchema(this.config, (key) => this.text(key))}
                .computeLabel=${(entry) => this.text(`editor.${entry.name}`)}
                .computeHelper=${(entry) => this.helper(entry.name)}
                @value-changed=${(event) => this.changed({ ...this.config, ...event.detail.value })}
            ></ha-form>
        `;
  }
  static get styles() {
    return i`
            .helper {
                margin: 8px 0 0;
                padding: 0 16px;
                font-size: 12px;
                line-height: 1.4;
                color: var(--secondary-text-color);
            }

            /* As far from the paragraph as ha-form keeps its own fields apart. */
            ha-form.height {
                display: block;
                margin-top: 24px;
            }
        `;
  }
  changed(value) {
    const config = tidyHeight(value);
    config.stations = compactStations(config.stations ?? []);
    if (!config.title) {
      delete config.title;
    }
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }
  text(key) {
    return translate(this.language(), key);
  }
  /** The height fields' helpers, for the fields that have one. */
  helper(name) {
    const key = `editor.${name}_helper`;
    const helper = translate(this.language(), key);
    return helper === key ? void 0 : helper;
  }
  language() {
    return this.hass?.locale?.language ?? this.hass?.language ?? browserLanguage();
  }
};
__decorateClass([
  n4({ attribute: false })
], RoadConditionsCardEditor.prototype, "hass", 2);
__decorateClass([
  r5()
], RoadConditionsCardEditor.prototype, "config", 2);
if (!customElements.get("road-conditions-card-editor")) {
  customElements.define("road-conditions-card-editor", RoadConditionsCardEditor);
}

// src/fade.ts
var fadeStyles = i`
    .fades {
        --fade-length: min(24px, 25%);
        scroll-padding-block: calc(var(--fade-top-offset, 0px) + var(--fade-length, 24px)) var(--fade-length, 24px);
    }

    .fade-top {
        mask-image: linear-gradient(
            to bottom,
            #000 var(--fade-top-offset, 0px),
            transparent var(--fade-top-offset, 0px),
            #000 calc(var(--fade-top-offset, 0px) + var(--fade-length, 24px))
        );
    }

    .fade-bottom {
        mask-image: linear-gradient(to top, transparent, #000 var(--fade-length, 24px));
    }

    .fade-top.fade-bottom {
        mask-image: linear-gradient(
            to bottom,
            #000 var(--fade-top-offset, 0px),
            transparent var(--fade-top-offset, 0px),
            #000 calc(var(--fade-top-offset, 0px) + var(--fade-length, 24px)),
            #000 calc(100% - var(--fade-length, 24px)),
            transparent
        );
    }
`;
function markFade(part) {
  const hidden = part.scrollHeight - part.clientHeight;
  part.classList.toggle("fade-top", hidden > 1 && part.scrollTop > 1);
  part.classList.toggle("fade-bottom", hidden > 1 && hidden - part.scrollTop > 1);
}
var onScroll = (event) => markFade(event.currentTarget);
var ScrollFade = class {
  constructor(host, parts) {
    this.host = host;
    this.parts = parts;
    /** Each followed part with the children whose size it watches. */
    this.followed = /* @__PURE__ */ new Map();
    this.resized = typeof ResizeObserver === "undefined" ? void 0 : new ResizeObserver((entries) => {
      for (const { target } of entries) {
        const part = this.followed.has(target) ? target : target.parentElement;
        if (part && this.followed.has(part)) {
          markFade(part);
        }
      }
    });
    host.addController(this);
  }
  hostConnected() {
    if (this.host.hasUpdated) {
      this.follow();
    }
  }
  hostUpdated() {
    if (this.host.isConnected) {
      this.follow();
    }
  }
  hostDisconnected() {
    for (const part of [...this.followed.keys()]) {
      this.forget(part);
    }
  }
  follow() {
    const now = new Set(this.parts());
    for (const part of [...this.followed.keys()]) {
      if (!now.has(part)) {
        this.forget(part);
      }
    }
    for (const part of now) {
      if (!this.followed.has(part)) {
        part.addEventListener("scroll", onScroll, { passive: true });
        this.resized?.observe(part);
      }
      part.classList.add("fades");
      const before = this.followed.get(part) ?? [];
      const children = [...part.children];
      before.filter((child) => !children.includes(child)).forEach((child) => this.resized?.unobserve(child));
      children.filter((child) => !before.includes(child)).forEach((child) => this.resized?.observe(child));
      this.followed.set(part, children);
      markFade(part);
    }
  }
  forget(part) {
    this.followed.get(part)?.forEach((child) => this.resized?.unobserve(child));
    this.followed.delete(part);
    part.removeEventListener("scroll", onScroll);
    this.resized?.unobserve(part);
    part.classList.remove("fades", "fade-top", "fade-bottom");
  }
};

// src/weather-icons.ts
var WEATHER_ICONS = {
  thermometer: "M9.91,19.56c0-0.85,0.2-1.64,0.59-2.38s0.94-1.35,1.65-1.84V5.42c0-0.8,0.27-1.48,0.82-2.03S14.2,2.55,15,2.55 c0.81,0,1.49,0.28,2.04,0.83c0.55,0.56,0.83,1.23,0.83,2.03v9.92c0.71,0.49,1.25,1.11,1.64,1.84s0.58,1.53,0.58,2.38 c0,0.92-0.23,1.78-0.68,2.56s-1.07,1.4-1.85,1.85s-1.63,0.68-2.56,0.68c-0.92,0-1.77-0.23-2.55-0.68s-1.4-1.07-1.86-1.85 S9.91,20.48,9.91,19.56z M11.67,19.56c0,0.93,0.33,1.73,0.98,2.39c0.65,0.66,1.44,0.99,2.36,0.99c0.93,0,1.73-0.33,2.4-1 s1.01-1.46,1.01-2.37c0-0.62-0.16-1.2-0.48-1.73c-0.32-0.53-0.76-0.94-1.32-1.23l-0.28-0.14c-0.1-0.04-0.15-0.14-0.15-0.29V5.42 c0-0.32-0.11-0.59-0.34-0.81C15.62,4.4,15.34,4.29,15,4.29c-0.32,0-0.6,0.11-0.83,0.32c-0.23,0.21-0.34,0.48-0.34,0.81v10.74 c0,0.15-0.05,0.25-0.14,0.29l-0.27,0.14c-0.55,0.29-0.98,0.7-1.29,1.23C11.82,18.35,11.67,18.92,11.67,19.56z M12.45,19.56 c0,0.71,0.24,1.32,0.73,1.82s1.07,0.75,1.76,0.75s1.28-0.25,1.79-0.75c0.51-0.5,0.76-1.11,0.76-1.81c0-0.63-0.22-1.19-0.65-1.67 c-0.43-0.48-0.96-0.77-1.58-0.85V9.69c0-0.06-0.03-0.13-0.1-0.19c-0.07-0.07-0.14-0.1-0.22-0.1c-0.09,0-0.16,0.03-0.21,0.08 c-0.05,0.06-0.08,0.12-0.08,0.21v7.34c-0.61,0.09-1.13,0.37-1.56,0.85C12.66,18.37,12.45,18.92,12.45,19.56z",
  "strong-wind": "M3.1,16.97c0,0.24,0.09,0.45,0.28,0.62c0.16,0.19,0.37,0.28,0.63,0.28H18.7c0.29,0,0.53,0.1,0.73,0.3 c0.2,0.2,0.3,0.45,0.3,0.74c0,0.29-0.1,0.53-0.3,0.72c-0.2,0.19-0.44,0.29-0.74,0.29c-0.29,0-0.54-0.1-0.73-0.29 c-0.16-0.18-0.36-0.26-0.6-0.26c-0.25,0-0.46,0.09-0.64,0.26s-0.27,0.38-0.27,0.61c0,0.25,0.09,0.46,0.28,0.63 c0.56,0.55,1.22,0.83,1.96,0.83c0.78,0,1.45-0.27,2.01-0.81c0.56-0.54,0.83-1.19,0.83-1.97s-0.28-1.44-0.84-2 c-0.56-0.56-1.23-0.84-2-0.84H4.01c-0.25,0-0.46,0.09-0.64,0.26C3.19,16.51,3.1,16.72,3.1,16.97z M3.1,13.69 c0,0.23,0.09,0.43,0.28,0.61c0.17,0.18,0.38,0.26,0.63,0.26h20.04c0.78,0,1.45-0.27,2.01-0.82c0.56-0.54,0.84-1.2,0.84-1.97 c0-0.77-0.28-1.44-0.84-1.99s-1.23-0.83-2.01-0.83c-0.77,0-1.42,0.27-1.95,0.8c-0.18,0.16-0.27,0.38-0.27,0.67 c0,0.26,0.09,0.47,0.26,0.63c0.17,0.16,0.38,0.24,0.63,0.24c0.24,0,0.45-0.08,0.63-0.24c0.19-0.21,0.42-0.31,0.7-0.31 c0.29,0,0.53,0.1,0.73,0.3c0.2,0.2,0.3,0.44,0.3,0.73c0,0.29-0.1,0.53-0.3,0.72c-0.2,0.19-0.44,0.29-0.73,0.29H4.01 c-0.25,0-0.46,0.09-0.64,0.26C3.19,13.23,3.1,13.44,3.1,13.69z",
  cloud: "M4.61,16.88c0-1.15,0.36-2.17,1.08-3.07c0.72-0.9,1.63-1.48,2.74-1.73c0.31-1.37,1.02-2.49,2.11-3.37s2.35-1.32,3.76-1.32 c1.38,0,2.61,0.43,3.69,1.28s1.78,1.95,2.1,3.29h0.33c0.9,0,1.73,0.22,2.49,0.65s1.37,1.03,1.81,1.79c0.44,0.76,0.67,1.58,0.67,2.48 c0,0.88-0.21,1.7-0.63,2.45s-1,1.35-1.73,1.8c-0.73,0.45-1.54,0.69-2.41,0.72H9.41c-1.34-0.06-2.47-0.57-3.4-1.53 C5.08,19.37,4.61,18.22,4.61,16.88z M6.32,16.88c0,0.87,0.3,1.62,0.9,2.26s1.33,0.98,2.19,1.03h11.19c0.86-0.04,1.59-0.39,2.19-1.03 c0.61-0.64,0.91-1.4,0.91-2.26c0-0.88-0.33-1.63-0.98-2.27c-0.65-0.64-1.42-0.96-2.32-0.96H18.8c-0.11,0-0.17-0.06-0.17-0.18 l-0.07-0.57c-0.11-1.08-0.58-1.99-1.4-2.72c-0.82-0.73-1.77-1.1-2.86-1.1c-1.09,0-2.05,0.37-2.85,1.1 c-0.81,0.73-1.27,1.64-1.37,2.72l-0.08,0.57c0,0.12-0.07,0.18-0.2,0.18H9.27c-0.84,0.1-1.54,0.46-2.1,1.07S6.32,16.05,6.32,16.88z",
  sprinkle: "M4.64,16.91c0-1.15,0.36-2.17,1.08-3.07c0.72-0.9,1.63-1.47,2.73-1.73c0.31-1.36,1.01-2.48,2.1-3.35s2.35-1.31,3.76-1.31 c1.38,0,2.6,0.43,3.68,1.27c1.07,0.85,1.78,1.94,2.11,3.28h0.31c0.89,0,1.72,0.22,2.48,0.65s1.37,1.03,1.81,1.78 c0.44,0.75,0.67,1.58,0.67,2.47c0,1.34-0.46,2.49-1.38,3.45s-2.05,1.47-3.38,1.51c-0.13,0-0.2-0.06-0.2-0.17v-1.33 c0-0.12,0.07-0.18,0.2-0.18c0.86-0.04,1.58-0.38,2.18-1.02s0.9-1.39,0.9-2.26s-0.32-1.62-0.98-2.26c-0.65-0.64-1.42-0.96-2.31-0.96 h-1.6c-0.12,0-0.19-0.06-0.19-0.17l-0.07-0.58c-0.11-1.07-0.57-1.98-1.38-2.71c-0.82-0.73-1.77-1.1-2.85-1.1 c-1.09,0-2.05,0.36-2.86,1.09c-0.81,0.73-1.27,1.63-1.38,2.71l-0.06,0.54c0,0.12-0.07,0.18-0.2,0.18l-0.53,0.03 c-0.82,0.04-1.51,0.37-2.09,1s-0.86,1.37-0.86,2.22c0,0.87,0.3,1.62,0.9,2.26s1.33,0.98,2.18,1.02c0.11,0,0.17,0.06,0.17,0.18v1.33 c0,0.11-0.06,0.17-0.17,0.17c-1.34-0.06-2.47-0.57-3.4-1.53S4.64,18.24,4.64,16.91z M10.57,17.79c0-0.24,0.12-0.57,0.37-0.99 c0.24-0.42,0.47-0.75,0.68-1.01c0.21-0.24,0.34-0.38,0.38-0.42l0.36,0.4c0.26,0.28,0.5,0.61,0.72,1.02c0.22,0.4,0.33,0.74,0.33,1 c0,0.39-0.13,0.72-0.4,0.98c-0.27,0.26-0.6,0.39-1,0.39c-0.39,0-0.73-0.13-1.01-0.4C10.71,18.5,10.57,18.17,10.57,17.79z M13.55,21.78c0-0.28,0.08-0.59,0.24-0.96s0.35-0.7,0.59-1.02c0.18-0.26,0.4-0.54,0.67-0.84c0.26-0.3,0.46-0.52,0.6-0.65 c0.07-0.06,0.15-0.14,0.24-0.23l0.24,0.23c0.38,0.33,0.8,0.82,1.27,1.46c0.24,0.33,0.43,0.68,0.59,1.04s0.23,0.68,0.23,0.97 c0,0.64-0.23,1.19-0.68,1.65s-1.01,0.68-1.66,0.68c-0.64,0-1.19-0.23-1.65-0.67C13.77,22.98,13.55,22.43,13.55,21.78z M15.02,15.12 c0-0.42,0.32-0.95,0.97-1.6l0.24,0.25c0.18,0.21,0.33,0.45,0.48,0.71c0.14,0.26,0.22,0.47,0.22,0.64c0,0.26-0.09,0.48-0.28,0.66 c-0.18,0.18-0.4,0.28-0.66,0.28c-0.27,0-0.5-0.09-0.69-0.28C15.11,15.6,15.02,15.38,15.02,15.12z",
  showers: "M4.6,16.93c0-1.16,0.36-2.18,1.09-3.08c0.72-0.9,1.65-1.48,2.78-1.73c0.29-1.38,0.98-2.5,2.07-3.39S12.88,7.4,14.3,7.4 c1.39,0,2.63,0.43,3.72,1.28c1.08,0.85,1.79,1.95,2.12,3.3h0.34c0.9,0,1.73,0.22,2.48,0.66c0.76,0.44,1.35,1.04,1.79,1.8 c0.43,0.76,0.65,1.59,0.65,2.49c0,1.34-0.46,2.48-1.37,3.44c-0.92,0.96-2.04,1.46-3.37,1.5c-0.12,0-0.18-0.06-0.18-0.17v-1.34 c0-0.11,0.06-0.17,0.18-0.17c0.84-0.07,1.57-0.42,2.17-1.05s0.9-1.37,0.9-2.22c0-0.89-0.32-1.66-0.96-2.31 c-0.64-0.64-1.4-0.97-2.29-0.97h-1.63c-0.12,0-0.19-0.06-0.22-0.18l-0.07-0.57c-0.07-0.71-0.3-1.36-0.7-1.94s-0.91-1.03-1.53-1.36 c-0.62-0.33-1.3-0.49-2.02-0.49c-1.1,0-2.05,0.36-2.86,1.09c-0.81,0.73-1.27,1.64-1.37,2.72l-0.07,0.54c0,0.09-0.05,0.14-0.16,0.14 L9.31,13.7c-0.84,0.07-1.55,0.41-2.11,1.03c-0.57,0.62-0.85,1.35-0.85,2.2c0,0.87,0.3,1.62,0.89,2.25c0.59,0.63,1.31,0.97,2.17,1.02 c0.12,0,0.18,0.06,0.18,0.17v1.34c0,0.11-0.06,0.17-0.18,0.17c-0.66-0.03-1.28-0.18-1.88-0.45S6.42,20.8,6,20.36 c-0.43-0.44-0.77-0.95-1.02-1.55S4.6,17.59,4.6,16.93z M10.02,23.7c0-0.03,0.01-0.08,0.02-0.13s0.02-0.09,0.02-0.11l0.27-1.03 c0.07-0.22,0.2-0.4,0.4-0.51c0.2-0.12,0.41-0.14,0.64-0.07c0.23,0.07,0.4,0.2,0.52,0.4c0.12,0.2,0.14,0.41,0.07,0.64l-0.24,1.01 c-0.13,0.44-0.38,0.66-0.76,0.66c-0.03,0-0.05,0-0.09,0c-0.03,0-0.07-0.01-0.11-0.01c-0.04-0.01-0.07-0.01-0.1-0.01 c-0.21-0.06-0.37-0.18-0.48-0.34S10.02,23.86,10.02,23.7z M11.34,18.88c0-0.02,0-0.06,0.01-0.11c0.01-0.05,0.01-0.08,0.01-0.09 l0.3-1.05c0.06-0.19,0.17-0.34,0.32-0.45c0.15-0.1,0.31-0.15,0.47-0.15c0.02,0,0.05,0,0.08,0c0.03,0,0.06,0.01,0.09,0.01 c0.03,0.01,0.06,0.01,0.08,0.01c0.23,0.07,0.4,0.2,0.51,0.4c0.12,0.2,0.14,0.41,0.07,0.64l-0.24,1c-0.07,0.28-0.2,0.47-0.4,0.59 s-0.42,0.12-0.65,0.02c-0.22-0.06-0.38-0.17-0.49-0.34S11.34,19.04,11.34,18.88z M12.57,26.83c0-0.03,0.01-0.07,0.02-0.13 s0.02-0.09,0.02-0.12l0.29-0.99c0.06-0.24,0.2-0.42,0.4-0.54c0.2-0.12,0.42-0.15,0.65-0.08c0.23,0.07,0.39,0.2,0.51,0.41 s0.13,0.42,0.07,0.65l-0.25,1.04c-0.11,0.41-0.37,0.61-0.8,0.61c-0.05,0-0.13-0.01-0.24-0.04c-0.22-0.04-0.38-0.14-0.49-0.3 C12.63,27.18,12.57,27.01,12.57,26.83z M13.91,22.06c0-0.06,0.01-0.14,0.04-0.25l0.27-1.03c0.07-0.23,0.2-0.4,0.41-0.51 c0.2-0.12,0.42-0.14,0.65-0.07c0.23,0.06,0.39,0.19,0.51,0.39c0.11,0.2,0.13,0.41,0.06,0.65l-0.24,0.99 c-0.13,0.45-0.37,0.68-0.72,0.68c-0.04,0-0.15-0.02-0.31-0.06c-0.22-0.04-0.38-0.14-0.49-0.3C13.97,22.4,13.91,22.23,13.91,22.06z M16.73,23.74c0-0.07,0.01-0.15,0.03-0.24l0.28-0.99c0.07-0.24,0.2-0.42,0.41-0.54s0.41-0.15,0.63-0.09 c0.23,0.07,0.41,0.2,0.53,0.41c0.12,0.2,0.15,0.41,0.09,0.63l-0.29,1.06c-0.1,0.41-0.36,0.61-0.79,0.61c-0.09,0-0.18-0.01-0.26-0.03 c-0.2-0.04-0.35-0.14-0.46-0.3C16.8,24.08,16.74,23.91,16.73,23.74z M18.11,18.98c0-0.03,0.02-0.12,0.05-0.26l0.3-1.03 c0.04-0.21,0.13-0.37,0.29-0.47c0.16-0.1,0.32-0.15,0.49-0.14c0.04-0.01,0.13,0,0.24,0.03c0.22,0.05,0.39,0.18,0.52,0.38 c0.12,0.17,0.14,0.38,0.07,0.65l-0.24,1.03c-0.13,0.43-0.38,0.65-0.76,0.65c-0.06,0-0.17-0.02-0.34-0.06 c-0.21-0.06-0.36-0.17-0.46-0.31C18.16,19.29,18.11,19.14,18.11,18.98z",
  rain: "M4.64,16.91c0-1.15,0.36-2.17,1.08-3.07c0.72-0.9,1.63-1.47,2.73-1.73c0.31-1.36,1.02-2.48,2.11-3.36s2.34-1.31,3.75-1.31 c1.38,0,2.6,0.43,3.68,1.28c1.08,0.85,1.78,1.95,2.1,3.29h0.32c0.89,0,1.72,0.22,2.48,0.65s1.37,1.03,1.81,1.78 c0.44,0.75,0.67,1.58,0.67,2.47c0,0.88-0.21,1.69-0.63,2.44c-0.42,0.75-1,1.35-1.73,1.8c-0.73,0.45-1.53,0.69-2.4,0.71 c-0.13,0-0.2-0.06-0.2-0.17v-1.33c0-0.12,0.07-0.18,0.2-0.18c0.85-0.04,1.58-0.38,2.18-1.02s0.9-1.39,0.9-2.26s-0.33-1.62-0.98-2.26 s-1.42-0.96-2.31-0.96h-1.61c-0.12,0-0.18-0.06-0.18-0.17l-0.08-0.58c-0.11-1.08-0.58-1.99-1.39-2.71 c-0.82-0.73-1.76-1.09-2.85-1.09c-1.09,0-2.05,0.36-2.85,1.09c-0.81,0.73-1.26,1.63-1.36,2.71l-0.07,0.53c0,0.12-0.07,0.19-0.2,0.19 l-0.53,0.03c-0.83,0.1-1.53,0.46-2.1,1.07s-0.85,1.33-0.85,2.16c0,0.87,0.3,1.62,0.9,2.26s1.33,0.98,2.18,1.02 c0.11,0,0.17,0.06,0.17,0.18v1.33c0,0.11-0.06,0.17-0.17,0.17c-1.34-0.06-2.47-0.57-3.4-1.53S4.64,18.24,4.64,16.91z M9.99,23.6 c0-0.04,0.01-0.11,0.04-0.2l1.63-5.77c0.06-0.19,0.17-0.34,0.32-0.44c0.15-0.1,0.31-0.15,0.46-0.15c0.07,0,0.15,0.01,0.24,0.03 c0.24,0.04,0.42,0.17,0.54,0.37c0.12,0.2,0.15,0.42,0.08,0.67l-1.63,5.73c-0.12,0.43-0.4,0.64-0.82,0.64 c-0.04,0-0.07-0.01-0.11-0.02c-0.06-0.02-0.09-0.03-0.1-0.03c-0.22-0.06-0.38-0.17-0.49-0.33C10.04,23.93,9.99,23.77,9.99,23.6z M12.61,26.41l2.44-8.77c0.04-0.19,0.14-0.34,0.3-0.44c0.16-0.1,0.32-0.15,0.49-0.15c0.09,0,0.18,0.01,0.27,0.03 c0.22,0.06,0.38,0.19,0.49,0.39c0.11,0.2,0.13,0.41,0.07,0.64l-2.43,8.78c-0.04,0.17-0.13,0.31-0.29,0.43 c-0.16,0.12-0.32,0.18-0.51,0.18c-0.09,0-0.18-0.02-0.25-0.05c-0.2-0.05-0.37-0.18-0.52-0.39C12.56,26.88,12.54,26.67,12.61,26.41z M16.74,23.62c0-0.04,0.01-0.11,0.04-0.23l1.63-5.77c0.06-0.19,0.16-0.34,0.3-0.44c0.15-0.1,0.3-0.15,0.46-0.15 c0.08,0,0.17,0.01,0.26,0.03c0.21,0.06,0.36,0.16,0.46,0.31c0.1,0.15,0.15,0.31,0.15,0.47c0,0.03-0.01,0.08-0.02,0.14 s-0.02,0.1-0.02,0.12l-1.63,5.73c-0.04,0.19-0.13,0.35-0.28,0.46s-0.32,0.17-0.51,0.17l-0.24-0.05c-0.2-0.06-0.35-0.16-0.46-0.32 C16.79,23.94,16.74,23.78,16.74,23.62z",
  snow: "M4.64,16.95c0-1.16,0.35-2.18,1.06-3.08s1.62-1.48,2.74-1.76c0.31-1.36,1.01-2.48,2.1-3.36s2.34-1.31,3.75-1.31 c1.38,0,2.6,0.43,3.68,1.28c1.08,0.85,1.78,1.95,2.1,3.29h0.32c0.89,0,1.72,0.22,2.48,0.66c0.76,0.44,1.37,1.04,1.81,1.8 c0.44,0.76,0.67,1.59,0.67,2.48c0,1.32-0.46,2.47-1.39,3.42c-0.92,0.96-2.05,1.46-3.38,1.5c-0.13,0-0.2-0.06-0.2-0.17v-1.33 c0-0.12,0.07-0.18,0.2-0.18c0.85-0.04,1.58-0.38,2.18-1.02s0.9-1.38,0.9-2.23c0-0.89-0.32-1.65-0.97-2.3s-1.42-0.97-2.32-0.97h-1.61 c-0.12,0-0.18-0.06-0.18-0.17l-0.08-0.58c-0.11-1.08-0.58-1.99-1.39-2.72c-0.82-0.73-1.76-1.1-2.85-1.1c-1.1,0-2.05,0.37-2.86,1.11 c-0.81,0.74-1.27,1.65-1.37,2.75l-0.06,0.5c0,0.12-0.07,0.19-0.2,0.19l-0.53,0.07c-0.83,0.07-1.53,0.41-2.1,1.04 s-0.85,1.35-0.85,2.19c0,0.85,0.3,1.59,0.9,2.23s1.33,0.97,2.18,1.02c0.11,0,0.17,0.06,0.17,0.18v1.33c0,0.11-0.06,0.17-0.17,0.17 c-1.34-0.04-2.47-0.54-3.4-1.5C5.1,19.42,4.64,18.27,4.64,16.95z M11,21.02c0-0.22,0.08-0.42,0.24-0.58 c0.16-0.16,0.35-0.24,0.59-0.24c0.23,0,0.43,0.08,0.59,0.24c0.16,0.16,0.24,0.36,0.24,0.58c0,0.24-0.08,0.44-0.24,0.6 c-0.16,0.17-0.35,0.25-0.59,0.25c-0.23,0-0.43-0.08-0.59-0.25C11.08,21.46,11,21.26,11,21.02z M11,24.65c0-0.24,0.08-0.44,0.24-0.6 c0.16-0.15,0.35-0.23,0.58-0.23c0.23,0,0.43,0.08,0.59,0.23c0.16,0.16,0.24,0.35,0.24,0.59c0,0.24-0.08,0.43-0.24,0.59 c-0.16,0.16-0.35,0.23-0.59,0.23c-0.23,0-0.43-0.08-0.59-0.23C11.08,25.08,11,24.88,11,24.65z M14.19,22.95 c0-0.23,0.08-0.44,0.25-0.62c0.16-0.16,0.35-0.24,0.57-0.24c0.23,0,0.43,0.09,0.6,0.26c0.17,0.17,0.26,0.37,0.26,0.6 c0,0.23-0.08,0.43-0.25,0.6c-0.17,0.17-0.37,0.25-0.61,0.25c-0.23,0-0.42-0.08-0.58-0.25S14.19,23.18,14.19,22.95z M14.19,19.33 c0-0.23,0.08-0.43,0.25-0.6c0.18-0.16,0.37-0.24,0.57-0.24c0.24,0,0.44,0.08,0.61,0.25c0.17,0.17,0.25,0.36,0.25,0.6 c0,0.23-0.08,0.43-0.25,0.59c-0.17,0.16-0.37,0.24-0.61,0.24c-0.23,0-0.42-0.08-0.58-0.24C14.27,19.76,14.19,19.56,14.19,19.33z M14.19,26.61c0-0.23,0.08-0.43,0.25-0.61c0.16-0.16,0.35-0.24,0.57-0.24c0.24,0,0.44,0.08,0.61,0.25c0.17,0.17,0.25,0.37,0.25,0.6 s-0.08,0.43-0.25,0.59c-0.17,0.16-0.37,0.24-0.61,0.24c-0.23,0-0.42-0.08-0.58-0.24C14.27,27.03,14.19,26.84,14.19,26.61z M17.41,21.02c0-0.22,0.08-0.41,0.25-0.58c0.17-0.17,0.37-0.25,0.6-0.25c0.23,0,0.43,0.08,0.59,0.24c0.16,0.16,0.24,0.36,0.24,0.58 c0,0.24-0.08,0.44-0.24,0.6c-0.16,0.17-0.35,0.25-0.59,0.25c-0.24,0-0.44-0.08-0.6-0.25C17.5,21.45,17.41,21.25,17.41,21.02z M17.41,24.65c0-0.22,0.08-0.42,0.25-0.6c0.16-0.15,0.36-0.23,0.6-0.23c0.24,0,0.43,0.08,0.59,0.23s0.23,0.35,0.23,0.59 c0,0.24-0.08,0.43-0.23,0.59c-0.16,0.16-0.35,0.23-0.59,0.23c-0.24,0-0.44-0.08-0.6-0.24C17.5,25.07,17.41,24.88,17.41,24.65z",
  sleet: "M4.09,16.95c0-1.16,0.36-2.19,1.08-3.09s1.64-1.49,2.74-1.74c0.31-1.37,1.01-2.49,2.1-3.37s2.35-1.32,3.77-1.32 c0.81,0,1.55,0.13,2.2,0.4c0,0.01,0,0.01,0.01,0.02c0.84,0.32,1.58,0.84,2.21,1.55h0.03c0.68,0.73,1.13,1.6,1.37,2.62h0.31 c1.08,0,2.02,0.29,2.83,0.86v-0.01c0.53,0.36,0.98,0.8,1.34,1.33c0.36,0.53,0.6,1.11,0.73,1.74c0.04,0.21,0.06,0.38,0.08,0.52v0.06 c0,0.01,0,0.06,0.01,0.17s0.01,0.19,0.01,0.24v0.03c0,0.88-0.21,1.7-0.64,2.45c-0.42,0.75-1,1.36-1.74,1.81 c-0.73,0.45-1.54,0.69-2.42,0.72c-0.13,0-0.2-0.06-0.2-0.17v-1.34c0-0.13,0.07-0.19,0.2-0.19c0.86-0.04,1.58-0.38,2.18-1.02 c0.6-0.64,0.9-1.39,0.9-2.26c0-0.89-0.32-1.65-0.97-2.29c-0.64-0.64-1.41-0.96-2.31-0.96h-1.61c-0.12,0-0.18-0.06-0.18-0.17 l-0.08-0.59c-0.1-1-0.52-1.86-1.27-2.59c-0.01-0.01-0.01-0.02-0.02-0.03s-0.02-0.02-0.02-0.03c-0.01-0.01-0.02-0.02-0.04-0.02 c0-0.02-0.01-0.03-0.02-0.03c-0.73-0.66-1.58-1.04-2.56-1.12c-0.07-0.01-0.18-0.01-0.34-0.01c-1.1,0-2.05,0.37-2.86,1.1 s-1.27,1.64-1.37,2.72l-0.08,0.59c-0.03,0.09-0.11,0.14-0.22,0.14L8.75,13.7c-0.84,0.1-1.55,0.46-2.11,1.07s-0.84,1.34-0.84,2.18 v0.04h0.03c0.01,0.48,0.11,0.93,0.3,1.35c0.2,0.43,0.46,0.79,0.8,1.09c0.21,0.18,0.45,0.34,0.74,0.48v0.01 c0.4,0.19,0.8,0.3,1.21,0.32c0.11,0,0.17,0.06,0.17,0.18v1.34c0,0.11-0.06,0.17-0.17,0.17c-0.52-0.03-1.01-0.13-1.48-0.3v0.01 c-0.83-0.29-1.54-0.77-2.11-1.43s-0.95-1.44-1.11-2.31v-0.03c-0.01-0.01-0.01-0.02-0.01-0.04C4.11,17.57,4.09,17.27,4.09,16.95z M9.59,24.12c0-0.03,0.01-0.07,0.02-0.13c0.01-0.05,0.02-0.09,0.02-0.12l0.09-0.59c0.07-0.24,0.2-0.41,0.41-0.53 s0.43-0.14,0.68-0.08c0.23,0.07,0.39,0.21,0.51,0.41c0.11,0.21,0.13,0.42,0.07,0.63l-0.14,0.6c-0.1,0.44-0.35,0.66-0.76,0.66 c-0.03,0-0.08-0.01-0.14-0.02c-0.06-0.01-0.1-0.02-0.14-0.02c-0.21-0.06-0.36-0.17-0.46-0.33C9.64,24.45,9.59,24.29,9.59,24.12z M10.33,21.18c0-0.24,0.08-0.43,0.23-0.59s0.35-0.23,0.59-0.23s0.43,0.08,0.59,0.23s0.23,0.35,0.23,0.59c0,0.23-0.08,0.42-0.23,0.58 s-0.35,0.23-0.59,0.23c-0.23,0-0.42-0.08-0.57-0.24C10.42,21.59,10.33,21.4,10.33,21.18z M11.97,27.17c0-0.04,0.01-0.11,0.04-0.23 l0.13-0.59c0.07-0.23,0.21-0.4,0.41-0.51c0.21-0.12,0.42-0.14,0.63-0.07c0.23,0.04,0.41,0.17,0.53,0.37 c0.12,0.2,0.15,0.43,0.08,0.68l-0.13,0.59c-0.1,0.41-0.37,0.61-0.8,0.61c-0.07,0-0.16-0.01-0.24-0.03 c-0.22-0.06-0.38-0.17-0.49-0.33C12.03,27.5,11.97,27.34,11.97,27.17z M12.76,24.26c0-0.23,0.08-0.43,0.23-0.58 c0.16-0.16,0.35-0.23,0.59-0.23s0.43,0.08,0.59,0.23c0.16,0.16,0.23,0.35,0.23,0.58c0,0.24-0.08,0.43-0.23,0.59 c-0.16,0.16-0.35,0.23-0.59,0.23c-0.23,0-0.42-0.08-0.58-0.24C12.84,24.68,12.76,24.49,12.76,24.26z M13.38,21.99 c0-0.1,0.01-0.19,0.03-0.27l0.23-0.9c0.07-0.23,0.21-0.41,0.41-0.53c0.21-0.12,0.42-0.15,0.64-0.08c0.24,0.07,0.41,0.2,0.53,0.4 s0.14,0.41,0.07,0.63l-0.26,0.9c-0.08,0.28-0.22,0.46-0.41,0.56c-0.19,0.1-0.41,0.12-0.64,0.06c-0.2-0.04-0.35-0.14-0.45-0.3 C13.41,22.3,13.37,22.14,13.38,21.99z M16.14,24.13c0-0.03,0-0.08,0.01-0.13s0.01-0.09,0.01-0.11l0.09-0.59 c0.07-0.24,0.2-0.41,0.41-0.53s0.43-0.14,0.68-0.08c0.23,0.07,0.4,0.21,0.51,0.41c0.12,0.21,0.14,0.42,0.07,0.63l-0.14,0.6 c-0.1,0.44-0.35,0.66-0.76,0.66c-0.03,0-0.08-0.01-0.14-0.02c-0.06-0.01-0.11-0.02-0.14-0.02c-0.2-0.06-0.35-0.17-0.45-0.33 C16.2,24.46,16.14,24.3,16.14,24.13z M16.88,21.19c0-0.24,0.08-0.43,0.23-0.59c0.16-0.16,0.35-0.23,0.59-0.23 c0.24,0,0.43,0.08,0.59,0.23c0.16,0.16,0.23,0.35,0.23,0.59c0,0.23-0.08,0.43-0.23,0.58C18.14,21.92,17.95,22,17.71,22 c-0.24,0-0.43-0.08-0.58-0.24C16.97,21.61,16.88,21.42,16.88,21.19z",
  fog: "M2.62,21.05c0-0.24,0.08-0.45,0.25-0.61c0.17-0.16,0.38-0.24,0.63-0.24h18.67c0.25,0,0.45,0.08,0.61,0.24 c0.16,0.16,0.24,0.36,0.24,0.61c0,0.23-0.08,0.43-0.25,0.58c-0.17,0.16-0.37,0.23-0.6,0.23H3.5c-0.25,0-0.46-0.08-0.63-0.23 C2.7,21.47,2.62,21.28,2.62,21.05z M5.24,17.91c0-0.24,0.09-0.44,0.26-0.6c0.15-0.15,0.35-0.23,0.59-0.23h18.67 c0.23,0,0.42,0.08,0.58,0.24c0.16,0.16,0.23,0.35,0.23,0.59c0,0.24-0.08,0.44-0.23,0.6c-0.16,0.17-0.35,0.25-0.58,0.25H6.09 c-0.24,0-0.44-0.08-0.6-0.25C5.32,18.34,5.24,18.14,5.24,17.91z M5.37,15.52c0,0.09,0.05,0.13,0.15,0.13h1.43 c0.06,0,0.13-0.05,0.2-0.16c0.24-0.52,0.59-0.94,1.06-1.27c0.47-0.33,0.99-0.52,1.55-0.56l0.55-0.07c0.11,0,0.17-0.06,0.17-0.18 l0.07-0.5c0.11-1.08,0.56-1.98,1.37-2.7c0.81-0.72,1.76-1.08,2.85-1.08c1.08,0,2.02,0.36,2.83,1.07c0.8,0.71,1.26,1.61,1.37,2.68 l0.08,0.57c0,0.11,0.07,0.17,0.2,0.17h1.59c0.64,0,1.23,0.17,1.76,0.52s0.92,0.8,1.18,1.37c0.07,0.11,0.14,0.16,0.21,0.16h1.43 c0.12,0,0.17-0.07,0.14-0.23c-0.29-1.02-0.88-1.86-1.74-2.51c-0.87-0.65-1.86-0.97-2.97-0.97h-0.32c-0.33-1.33-1.03-2.42-2.1-3.27 s-2.28-1.27-3.65-1.27c-1.4,0-2.64,0.44-3.73,1.32s-1.78,2-2.09,3.36c-0.85,0.2-1.6,0.6-2.24,1.21c-0.64,0.61-1.09,1.33-1.34,2.18 v-0.04C5.37,15.45,5.37,15.48,5.37,15.52z M6.98,24.11c0-0.24,0.09-0.43,0.26-0.59c0.15-0.15,0.35-0.23,0.6-0.23h18.68 c0.24,0,0.44,0.08,0.6,0.23c0.17,0.16,0.25,0.35,0.25,0.58c0,0.24-0.08,0.44-0.25,0.61c-0.17,0.17-0.37,0.25-0.6,0.25H7.84 c-0.23,0-0.43-0.09-0.6-0.26C7.07,24.55,6.98,24.34,6.98,24.11z",
  na: "M6.87,18.23h1.94v-3.64h0.02l2.05,3.64h1.99v-6.66h-1.94v3.55h-0.02l-1.94-3.55h-2.1V18.23z M13.39,18.38h1.43l2.61-6.97 h-1.42L13.39,18.38z M16.26,18.23h2.07l0.29-0.95h2.12l0.28,0.95h2.13l-2.43-6.66h-2.01L16.26,18.23z M19.07,15.84l0.64-2.04h0.03 l0.6,2.04H19.07z",
  hail: "M4.64,16.9c0,1.33,0.46,2.47,1.39,3.43c0.93,0.96,2.06,1.47,3.4,1.53c0.11,0,0.17-0.06,0.17-0.17v-1.34 c0-0.11-0.06-0.17-0.17-0.17c-0.86-0.04-1.58-0.38-2.18-1.02c-0.6-0.64-0.9-1.39-0.9-2.26c0-0.83,0.28-1.54,0.84-2.16 c0.56-0.61,1.26-0.97,2.09-1.07l0.53-0.03c0.13,0,0.2-0.06,0.2-0.19l0.06-0.53c0.11-1.08,0.56-1.99,1.37-2.71 c0.81-0.73,1.76-1.09,2.85-1.09c1.09,0,2.04,0.36,2.85,1.09c0.81,0.73,1.27,1.63,1.39,2.71l0.08,0.58c0,0.11,0.06,0.17,0.18,0.17 h1.61c0.89,0,1.66,0.32,2.31,0.96c0.65,0.64,0.98,1.39,0.98,2.27c0,0.87-0.3,1.62-0.9,2.26c-0.6,0.64-1.33,0.98-2.18,1.02 c-0.13,0-0.2,0.06-0.2,0.17v1.34c0,0.11,0.07,0.17,0.2,0.17c0.87-0.02,1.67-0.26,2.4-0.71c0.73-0.45,1.31-1.05,1.73-1.8 c0.42-0.75,0.63-1.57,0.63-2.44c0-0.89-0.22-1.72-0.67-2.47c-0.44-0.75-1.05-1.35-1.81-1.78S21.29,12,20.4,12h-0.32 c-0.32-1.34-1.03-2.43-2.1-3.28s-2.3-1.28-3.68-1.28c-1.41,0-2.66,0.44-3.75,1.31c-1.09,0.87-1.79,1.99-2.1,3.35 c-1.11,0.26-2.02,0.83-2.73,1.73S4.64,15.75,4.64,16.9z M10.09,24.1c0.09,0.21,0.25,0.37,0.46,0.46c0.2,0.1,0.41,0.11,0.62,0.02 c0.22-0.09,0.36-0.24,0.45-0.45c0.1-0.22,0.11-0.43,0.02-0.64c-0.08-0.21-0.24-0.35-0.45-0.44c-0.2-0.11-0.4-0.12-0.61-0.03 c-0.21,0.09-0.36,0.24-0.46,0.47C10.01,23.66,10.01,23.86,10.09,24.1z M10.72,21.28c0,0.16,0.05,0.31,0.15,0.45 c0.1,0.15,0.26,0.25,0.46,0.32c0.19,0.11,0.4,0.12,0.62,0.01c0.22-0.1,0.37-0.3,0.44-0.6l0.9-3.38c0.06-0.25,0.04-0.47-0.08-0.67 c-0.12-0.2-0.29-0.32-0.53-0.36c-0.08-0.02-0.16-0.03-0.24-0.03c-0.16,0-0.32,0.05-0.47,0.15c-0.15,0.1-0.26,0.25-0.32,0.44 l-0.88,3.39C10.73,21.16,10.72,21.25,10.72,21.28z M12.58,26.87c0,0.12,0.02,0.22,0.06,0.29c0.09,0.22,0.24,0.37,0.45,0.45 c0.09,0.05,0.2,0.08,0.33,0.08c0.06,0,0.16-0.02,0.3-0.06c0.22-0.08,0.38-0.23,0.47-0.45c0.1-0.22,0.1-0.44,0-0.66 c-0.1-0.22-0.25-0.37-0.45-0.46c-0.2-0.09-0.4-0.09-0.62,0c-0.19,0.08-0.32,0.2-0.41,0.36C12.62,26.58,12.58,26.73,12.58,26.87z M13.31,24.26c0,0.37,0.21,0.61,0.63,0.73c0.11,0.03,0.19,0.04,0.24,0.04c0.15,0,0.28-0.03,0.38-0.08c0.21-0.08,0.35-0.27,0.42-0.57 l1.67-6.29c0.06-0.24,0.04-0.45-0.06-0.65c-0.1-0.19-0.27-0.32-0.49-0.38c-0.08-0.02-0.17-0.03-0.27-0.03 c-0.16,0-0.32,0.05-0.48,0.15c-0.16,0.1-0.26,0.25-0.3,0.44l-1.71,6.34C13.32,24.1,13.31,24.2,13.31,24.26z M16.74,23.8 c0,0.12,0.02,0.23,0.08,0.32c0.08,0.19,0.23,0.34,0.44,0.44c0.11,0.04,0.23,0.07,0.35,0.07c0.06,0,0.16-0.02,0.3-0.06 c0.21-0.08,0.37-0.23,0.46-0.44c0.07-0.22,0.07-0.43-0.01-0.63c-0.08-0.2-0.22-0.35-0.42-0.45c-0.23-0.11-0.44-0.12-0.65-0.03 c-0.21,0.09-0.36,0.24-0.46,0.47C16.77,23.59,16.74,23.69,16.74,23.8z M17.47,21.23c0,0.14,0.05,0.29,0.16,0.45 c0.11,0.16,0.26,0.27,0.45,0.33c0.16,0.03,0.25,0.05,0.27,0.05c0.09,0,0.22-0.03,0.37-0.1c0.2-0.09,0.33-0.27,0.4-0.52l0.9-3.34 c0.02-0.17,0.03-0.26,0.03-0.26c0-0.16-0.05-0.31-0.15-0.46c-0.1-0.15-0.25-0.25-0.45-0.31c-0.09-0.02-0.18-0.03-0.26-0.03 c-0.16,0-0.32,0.05-0.47,0.15s-0.25,0.25-0.31,0.45l-0.9,3.36L17.47,21.23z",
  "rain-mix": "M4.65,16.96c0,1.32,0.47,2.46,1.4,3.41c0.93,0.96,2.06,1.46,3.38,1.5c0.12,0,0.18-0.06,0.18-0.17v-1.33 c0-0.12-0.06-0.18-0.18-0.18c-0.84-0.04-1.57-0.38-2.17-1.02s-0.91-1.37-0.91-2.22c0-0.84,0.28-1.57,0.85-2.19 c0.57-0.62,1.26-0.97,2.1-1.04l0.53-0.07c0.12,0,0.19-0.06,0.19-0.18l0.07-0.5c0.1-1.09,0.55-2.01,1.36-2.75s1.76-1.11,2.86-1.11 c1.08,0,2.03,0.37,2.84,1.1c0.81,0.73,1.28,1.63,1.4,2.71l0.07,0.58c0,0.12,0.06,0.18,0.19,0.18h1.6c0.9,0,1.67,0.32,2.32,0.97 c0.64,0.64,0.97,1.41,0.97,2.3c0,0.84-0.3,1.58-0.9,2.22c-0.6,0.63-1.33,0.97-2.18,1.02c-0.13,0-0.2,0.06-0.2,0.18v1.33 c0,0.11,0.07,0.17,0.2,0.17c1.33-0.04,2.46-0.54,3.38-1.5s1.38-2.09,1.38-3.42c0-0.89-0.22-1.72-0.67-2.48 c-0.44-0.76-1.05-1.36-1.81-1.8c-0.76-0.44-1.59-0.66-2.48-0.66h-0.31c-0.33-1.34-1.03-2.43-2.11-3.29 c-1.07-0.85-2.3-1.28-3.68-1.28c-1.41,0-2.66,0.44-3.75,1.31s-1.79,1.99-2.1,3.35c-1.13,0.29-2.04,0.88-2.75,1.77 S4.65,15.8,4.65,16.96z M10.05,23.98c0,0.17,0.05,0.34,0.16,0.51c0.11,0.17,0.27,0.28,0.47,0.35c0.23,0.07,0.44,0.06,0.64-0.04 c0.19-0.09,0.33-0.28,0.39-0.56l0.14-0.61c0.05-0.23,0.02-0.44-0.09-0.63s-0.28-0.33-0.52-0.4c-0.22-0.07-0.44-0.04-0.64,0.08 s-0.34,0.3-0.4,0.53l-0.14,0.59C10.06,23.83,10.05,23.89,10.05,23.98z M10.81,21.08c0,0.21,0.08,0.4,0.25,0.57 c0.16,0.17,0.34,0.25,0.56,0.25c0.24,0,0.44-0.08,0.6-0.24c0.16-0.16,0.24-0.35,0.24-0.59c0-0.23-0.08-0.43-0.24-0.59 c-0.16-0.16-0.36-0.24-0.6-0.24c-0.23,0-0.42,0.08-0.58,0.23C10.89,20.65,10.81,20.85,10.81,21.08z M11.42,18.81 c-0.01,0.16,0.03,0.31,0.14,0.45c0.1,0.15,0.26,0.25,0.48,0.32c0.21,0.06,0.41,0.04,0.62-0.07S13,19.23,13.07,19l0.28-0.9 c0.07-0.24,0.05-0.46-0.07-0.65c-0.12-0.19-0.3-0.32-0.54-0.39c-0.22-0.07-0.43-0.05-0.63,0.07c-0.2,0.11-0.34,0.28-0.41,0.5 l-0.24,0.92c0,0.02-0.01,0.06-0.02,0.12C11.43,18.72,11.42,18.77,11.42,18.81z M12.59,27.1c0,0.18,0.05,0.34,0.15,0.5 c0.1,0.16,0.26,0.27,0.48,0.33c0.08,0.02,0.17,0.03,0.25,0.03c0.43,0,0.69-0.2,0.79-0.61l0.14-0.59c0.06-0.26,0.03-0.48-0.08-0.68 c-0.12-0.2-0.29-0.32-0.52-0.37c-0.21-0.07-0.42-0.05-0.63,0.07c-0.21,0.12-0.34,0.29-0.41,0.51l-0.14,0.59 C12.6,26.97,12.59,27.04,12.59,27.1z M13.36,24.2c0,0.22,0.08,0.41,0.25,0.58c0.16,0.16,0.35,0.24,0.57,0.24 c0.24,0,0.43-0.08,0.59-0.23c0.16-0.16,0.23-0.35,0.23-0.59c0-0.23-0.08-0.42-0.23-0.58c-0.16-0.16-0.35-0.23-0.59-0.23 c-0.24,0-0.43,0.08-0.59,0.23S13.36,23.97,13.36,24.2z M13.99,21.93c-0.01,0.15,0.03,0.31,0.13,0.47c0.1,0.16,0.25,0.26,0.45,0.3 c0.23,0.06,0.44,0.04,0.64-0.06s0.33-0.29,0.41-0.56l0.27-0.9c0.07-0.22,0.05-0.43-0.07-0.63c-0.12-0.2-0.29-0.33-0.53-0.4 c-0.22-0.07-0.43-0.04-0.64,0.08c-0.21,0.12-0.34,0.3-0.41,0.53l-0.23,0.9C14,21.74,13.99,21.83,13.99,21.93z M16.75,24.08 c0,0.16,0.05,0.32,0.15,0.48c0.1,0.16,0.26,0.27,0.46,0.33c0.03,0,0.08,0.01,0.14,0.02c0.06,0.01,0.1,0.02,0.14,0.02 c0.41,0,0.66-0.22,0.76-0.66l0.14-0.6c0.07-0.21,0.05-0.42-0.07-0.63c-0.11-0.21-0.28-0.34-0.51-0.41 c-0.25-0.06-0.48-0.04-0.68,0.08s-0.34,0.29-0.41,0.53l-0.09,0.59c0,0.02-0.01,0.07-0.02,0.12S16.75,24.04,16.75,24.08z M17.49,21.12c0,0.22,0.08,0.42,0.25,0.57c0.15,0.16,0.34,0.24,0.57,0.24c0.24,0,0.43-0.08,0.59-0.23s0.23-0.35,0.23-0.58 c0-0.24-0.08-0.43-0.23-0.59s-0.35-0.23-0.59-0.23c-0.24,0-0.43,0.08-0.59,0.23C17.57,20.69,17.49,20.88,17.49,21.12z M18.1,18.81 c0,0.17,0.05,0.33,0.16,0.48c0.11,0.15,0.27,0.26,0.49,0.32c0.02,0,0.06,0.01,0.12,0.02s0.11,0.02,0.14,0.02 c0.1,0,0.22-0.03,0.36-0.09c0.21-0.11,0.35-0.29,0.41-0.52l0.24-0.9c0.06-0.23,0.04-0.44-0.08-0.63c-0.11-0.2-0.28-0.33-0.51-0.4 c-0.23-0.07-0.44-0.05-0.64,0.06c-0.19,0.11-0.33,0.27-0.39,0.51l-0.28,0.91c0,0.02-0.01,0.06-0.02,0.12 C18.1,18.74,18.1,18.78,18.1,18.81z",
  "snowflake-cold": "M7.46,14.41c0-0.19,0.07-0.36,0.2-0.5c0.13-0.14,0.29-0.21,0.48-0.21c0.19,0,0.36,0.07,0.49,0.21c0.13,0.14,0.2,0.3,0.2,0.5 c0,0.19-0.07,0.35-0.2,0.48c-0.13,0.13-0.3,0.2-0.48,0.2s-0.35-0.07-0.48-0.2C7.52,14.75,7.46,14.59,7.46,14.41z M9.44,14.41 c0-0.19,0.07-0.36,0.2-0.5c0.13-0.14,0.29-0.21,0.48-0.21h3.23l-2.28-2.28c-0.14-0.12-0.21-0.28-0.21-0.47 c0-0.19,0.07-0.35,0.21-0.49c0.14-0.14,0.3-0.21,0.49-0.21s0.35,0.07,0.49,0.21l2.27,2.27V9.52c0-0.19,0.07-0.36,0.21-0.5 s0.3-0.21,0.5-0.21c0.19,0,0.35,0.07,0.48,0.21c0.13,0.14,0.2,0.3,0.2,0.5v3.23l2.29-2.3c0.14-0.14,0.3-0.21,0.48-0.21 c0.18,0,0.35,0.07,0.49,0.21c0.12,0.14,0.18,0.3,0.18,0.49c0,0.19-0.06,0.35-0.18,0.47l-2.28,2.28h3.23c0.18,0,0.34,0.07,0.47,0.21 c0.13,0.14,0.2,0.3,0.2,0.5c0,0.18-0.07,0.34-0.2,0.47c-0.13,0.13-0.29,0.2-0.47,0.2h-3.23l2.29,2.29c0.12,0.12,0.18,0.28,0.18,0.47 s-0.06,0.35-0.18,0.49c-0.14,0.14-0.31,0.21-0.49,0.21c-0.18,0-0.35-0.07-0.48-0.21l-2.29-2.3v3.24c0,0.19-0.07,0.36-0.2,0.49 c-0.13,0.13-0.29,0.2-0.48,0.2c-0.19,0-0.36-0.07-0.5-0.2c-0.14-0.13-0.21-0.3-0.21-0.49v-3.22l-2.27,2.27 c-0.14,0.14-0.3,0.21-0.49,0.21s-0.35-0.07-0.49-0.21s-0.21-0.3-0.21-0.49s0.07-0.34,0.21-0.47l2.3-2.29h-3.24 c-0.19,0-0.35-0.07-0.48-0.2C9.5,14.75,9.44,14.59,9.44,14.41z M9.45,19.25c0-0.18,0.07-0.35,0.21-0.48 c0.12-0.14,0.28-0.21,0.47-0.21c0.19,0,0.35,0.07,0.49,0.21c0.14,0.14,0.21,0.3,0.21,0.48c0,0.18-0.07,0.35-0.21,0.48 c-0.14,0.14-0.3,0.21-0.49,0.21c-0.19,0-0.35-0.07-0.47-0.21C9.52,19.6,9.45,19.44,9.45,19.25z M9.45,9.54 c0-0.18,0.07-0.35,0.21-0.48c0.12-0.14,0.28-0.21,0.47-0.21c0.19,0,0.35,0.07,0.49,0.21c0.14,0.14,0.21,0.3,0.21,0.48 s-0.07,0.35-0.21,0.49c-0.14,0.14-0.3,0.21-0.49,0.21c-0.19,0-0.35-0.07-0.47-0.21C9.52,9.89,9.45,9.72,9.45,9.54z M14.3,21.25 c0-0.18,0.07-0.34,0.21-0.47c0.14-0.13,0.3-0.2,0.5-0.2c0.19,0,0.35,0.07,0.48,0.2c0.13,0.13,0.2,0.29,0.2,0.47 c0,0.19-0.07,0.36-0.2,0.49c-0.13,0.13-0.29,0.2-0.48,0.2c-0.19,0-0.36-0.07-0.5-0.2C14.37,21.61,14.3,21.45,14.3,21.25z M14.3,7.54 c0-0.19,0.07-0.36,0.21-0.49s0.3-0.2,0.5-0.2c0.19,0,0.35,0.07,0.48,0.2c0.13,0.13,0.2,0.3,0.2,0.49c0,0.18-0.07,0.34-0.2,0.47 c-0.13,0.13-0.29,0.2-0.48,0.2c-0.19,0-0.36-0.07-0.5-0.2C14.37,7.88,14.3,7.72,14.3,7.54z M19.17,19.25c0-0.18,0.07-0.35,0.21-0.48 c0.12-0.14,0.28-0.21,0.47-0.21c0.19,0,0.35,0.07,0.49,0.21c0.14,0.14,0.21,0.3,0.21,0.48c0,0.18-0.07,0.35-0.21,0.48 c-0.14,0.14-0.3,0.21-0.49,0.21c-0.19,0-0.35-0.07-0.47-0.21C19.24,19.6,19.17,19.44,19.17,19.25z M19.17,9.54 c0-0.18,0.07-0.35,0.21-0.48c0.12-0.14,0.28-0.21,0.47-0.21c0.19,0,0.35,0.07,0.49,0.21c0.14,0.14,0.21,0.3,0.21,0.48 s-0.07,0.35-0.21,0.49c-0.14,0.14-0.3,0.21-0.49,0.21c-0.19,0-0.35-0.07-0.47-0.21C19.24,9.89,19.17,9.72,19.17,9.54z M21.17,14.41 c0-0.19,0.07-0.36,0.2-0.5c0.13-0.14,0.3-0.21,0.49-0.21c0.18,0,0.34,0.07,0.47,0.21c0.13,0.14,0.2,0.3,0.2,0.5 c0,0.18-0.07,0.34-0.2,0.47c-0.13,0.13-0.29,0.2-0.47,0.2c-0.19,0-0.36-0.07-0.49-0.2C21.24,14.75,21.17,14.59,21.17,14.41z"
};

// src/road-conditions-card.ts
var RoadConditionsCard = class extends i4 {
  constructor() {
    super();
    new ScrollFade(
      this,
      () => this.heightStyle() ? this.renderRoot.querySelectorAll("ha-card > .station, ha-card > .rows") : []
    );
  }
  static getConfigElement() {
    return document.createElement("road-conditions-card-editor");
  }
  /** Offers the first road weather station there is when the card is added from the picker. */
  static getStubConfig(hass) {
    return { stations: hass ? stationDevices(hass).slice(0, 1) : [] };
  }
  setConfig(config) {
    if (!config || stationsOf(config.stations).length === 0) {
      throw new Error(translate(browserLanguage(), "common.invalid_configuration"));
    }
    if (stationsOf(config.stations).length !== config.stations.length) {
      throw new Error(translate(browserLanguage(), "common.station_without_device"));
    }
    if (!validHeight(config)) {
      throw new Error(translate(browserLanguage(), "common.invalid_height"));
    }
    this.config = { ...config };
  }
  /**
   * In a sections view the card takes a whole section by default and is never narrower than half of one, nor lower
   * than its minimum height.
   */
  getGridOptions() {
    return { columns: 12, rows: "auto", min_columns: 6, min_rows: gridMinRows(this.minimumHeight()) };
  }
  getCardSize() {
    const count = this.config ? stationsOf(this.config.stations).length : 1;
    return heightCardSize(this.config ?? {}, count === 1 ? 4 : 1 + count, this.minimumHeight());
  }
  shouldUpdate(changed) {
    const previous = changed.get("hass");
    if (changed.has("config") || changed.has("layout") || !this.config || !this.hass || !changed.has("hass") || !previous) {
      return true;
    }
    if (previous.entities !== this.hass.entities || previous.devices !== this.hass.devices) {
      return true;
    }
    if (previous.locale !== this.hass.locale || previous.language !== this.hass.language || previous.formatEntityState !== this.hass.formatEntityState) {
      return true;
    }
    const ids = stationsOf(this.config.stations).flatMap((station) => Object.values(this.sensors(station.device)));
    return ids.some((id) => previous.states[id] !== this.hass?.states[id]);
  }
  /** A station's sensors, looked up again only when the entity registry changes, not on every state change. */
  sensors(device) {
    const hass = this.hass;
    let cache = this.sensorCache;
    if (!cache || cache.entities !== hass.entities) {
      cache = { entities: hass.entities, byDevice: /* @__PURE__ */ new Map() };
      this.sensorCache = cache;
    }
    let found = cache.byDevice.get(device);
    if (!found) {
      found = stationSensors(hass, device);
      cache.byDevice.set(device, found);
    }
    return found;
  }
  render() {
    if (!this.hass || !this.config) {
      return A;
    }
    const stations = stationsOf(this.config.stations);
    const height = this.heightStyle();
    return b2`
            <ha-card class=${height ? "held" : ""} style=${height}>
                ${this.config.title ? b2`<h1 class="card-title">${this.config.title}</h1>` : A}
                ${stations.length === 1 ? this.station(stations[0]) : b2`<div class="rows">${stations.map((station) => this.row(station))}</div>`}
            </ha-card>
        `;
  }
  /**
   * The whole card for one station: its name, and under it the grade on its scale, the values in a grid and a warning
   * when there is one, which is the part that scrolls when the card is held to a height.
   */
  station(station) {
    const hass = this.hass;
    const sensors = this.sensors(station.device);
    const name = stationName(hass, station);
    if (Object.keys(sensors).length === 0) {
      return b2`<div class="name">${name}</div>
                <div class="station"><div class="message">${this.text("common.no_station")}</div></div>`;
    }
    const condition = reading(hass, sensors.grip_condition);
    const grip = reading(hass, sensors.grip);
    const warning = reading(hass, sensors.road_warning);
    const values = this.values(sensors);
    if (!condition && values.length === 0 && !warning) {
      return b2`<div class="name">${name}</div>
                <div class="station"><div class="message">${this.text("common.no_readings")}</div></div>`;
    }
    return b2`
            <div class="name">${name}</div>
            <div class="station">
                ${condition ? b2`
                              <button class="grade" @click=${() => this.moreInfo(condition.entity_id)}>
                                  <span class="grade-text">${this.format(condition)}</span>
                                  ${grip ? b2`<span class="grip">${this.format(grip)}</span>` : A}
                              </button>
                              ${this.scale(condition.state, "large")}
                              <div class="scale-labels" aria-hidden="true">
                                  <span>${this.text("scale.very_slippery")}</span><span>${this.text("scale.winter")}</span
                                  ><span>${this.text("scale.good")}</span>
                              </div>
                          ` : A}
                ${values.length ? b2`<div class="values ${condition ? "divided" : ""}">
                              ${values.map(
      (value) => b2`
                                      <button
                                          class="value ${value.key} ${value.notable ? "notable" : ""}"
                                          title="${value.label}"
                                          aria-label="${value.spoken}"
                                          @click=${() => this.moreInfo(value.entity)}
                                      >
                                          ${this.icon(value.icon)} ${value.text ? b2`<span>${value.text}</span>` : A}
                                      </button>
                                  `
    )}
                          </div>` : A}
                ${warning && warning.state !== "ok" ? b2`<button class="warning" @click=${() => this.moreInfo(warning.entity_id)}>
                              ${this.icon(ICONS.road_warning)}
                              <span>${this.text("labels.road_warning")}: ${this.format(warning)}</span>
                          </button>` : A}
            </div>
        `;
  }
  /** One station as a row: its name and main values on the left, the grade and a small scale on the right. */
  row(station) {
    const hass = this.hass;
    const sensors = this.sensors(station.device);
    const name = stationName(hass, station);
    const condition = reading(hass, sensors.grip_condition);
    const grip = reading(hass, sensors.grip);
    const summary = this.values(sensors).filter(
      (value) => value.notable || ["road_temperature", "road_surface", "wind"].includes(value.key)
    );
    let message;
    if (Object.keys(sensors).length === 0) {
      message = this.text("common.no_station");
    } else if (summary.length === 0 && !condition) {
      message = this.text("common.no_readings");
    }
    const content = b2`
            <span class="row-text">
                <span class="row-name">${name}</span>
                <span class="row-values">
                    ${message ? message : summary.map(
      (value) => b2`<span class="row-value ${value.notable ? "notable" : ""}" title="${value.label}"
                                          >${this.icon(value.icon)}${value.text}</span
                                      >`
    )}
                </span>
            </span>
            ${condition ? b2`<span class="row-grade">
                          <span>${this.format(condition)}${grip ? b2` <span class="grip">${this.format(grip)}</span>` : A}</span>
                          ${this.scale(condition.state, "small")}
                      </span>` : A}
        `;
    const target = sensors.grip_condition ?? sensors.road_temperature;
    if (!target) {
      return b2`<div class="row">${content}</div>`;
    }
    const spoken = [name, ...summary.map((value) => value.spoken)];
    if (condition) {
      spoken.push(grip ? `${this.format(condition)} ${this.format(grip)}` : this.format(condition));
    }
    return b2`<button class="row" aria-label=${spoken.join(", ")} @click=${() => this.moreInfo(target)}>${content}</button>`;
  }
  heightStyle() {
    return heightStyle(this.config ?? {}, this.layout, this.minimumHeight());
  }
  /**
   * The lowest the card is held to, in pixels: its padding, the title when it has one, and for one station its name,
   * the grade on its scale and the first line of values, for several the first station's row. The padding, the title,
   * the station's name and the row as measured on a full section's width, the grade and the values estimated from the
   * styles.
   */
  minimumHeight() {
    const padding = 34;
    const title = 37;
    const name = 31;
    const grade = 88;
    const values = 20;
    const row = 62;
    const one = this.config ? stationsOf(this.config.stations).length === 1 : true;
    return padding + (this.config?.title ? title : 0) + (one ? name + grade + values : row);
  }
  scale(condition, size) {
    return b2`<div class="scale ${size}" aria-hidden="true">
            ${scale(condition).map((part) => b2`<span class="part grip-${part.condition} ${part.lit ? "lit" : ""}"></span>`)}
        </div>`;
  }
  /** A Weather Icons glyph drawn inline ("wi:rain"), or a Material Design Icon through Home Assistant. */
  icon(name) {
    if (name.startsWith("wi:")) {
      return b2`<svg class="icon" data-icon=${name} viewBox="0 0 30 30" aria-hidden="true">
                ${w`<path d=${WEATHER_ICONS[name.slice(3)] ?? ""}></path>`}
            </svg>`;
    }
    return b2`<ha-icon class="icon" data-icon=${name} icon=${name}></ha-icon>`;
  }
  /** The station's values in the order they are shown, leaving out what it doesn't measure. */
  values(sensors) {
    const hass = this.hass;
    const values = [];
    const add = (key, entity, icon, text) => {
      if (entity) {
        const label = this.text(`labels.${key}`);
        values.push({ key, icon, label, text, spoken: `${label} ${text}`, entity: entity.entity_id });
      }
    };
    for (const key of ["road_temperature", "air_temperature", "road_surface"]) {
      const entity = reading(hass, sensors[key]);
      add(key, entity, ICONS[key], entity ? this.format(entity) : "");
    }
    const speed = reading(hass, sensors.wind_speed);
    if (speed) {
      const gusts = reading(hass, sensors.wind_gusts);
      const extra = gusts && showGusts(speed, gusts) ? ` (${this.format(gusts)})` : "";
      add("wind", speed, ICONS.wind, `${this.format(speed)}${extra}`);
    }
    const code = reading(hass, sensors.precipitation);
    const type = reading(hass, sensors.precipitation_type);
    if (code || type) {
      const shown = precipitation(type?.state, code?.state);
      const entity = type ?? code;
      const intensity = reading(hass, sensors.rain_intensity);
      const described = [
        entity,
        ...type && code && HEAVY.includes(code.state) ? [code] : [],
        ...intensity && Number(intensity.state) > 0 ? [intensity] : []
      ];
      const label = `${this.text("labels.precipitation")}: ${described.map((part) => this.format(part)).join(", ")}`;
      values.push({
        key: "precipitation",
        notable: shown.notable,
        icon: shown.icon,
        label,
        text: shown.text ? this.text(`precipitation.${shown.text}`) : this.format(entity),
        // The label already says it all; the short word would be heard twice.
        spoken: label,
        entity: entity.entity_id
      });
    }
    const visibility = reading(hass, sensors.visibility);
    add("visibility", visibility, ICONS.visibility, visibility ? this.format(visibility) : "");
    return values;
  }
  /** A state as Home Assistant shows it, in the user's language and with its unit. */
  format(entity) {
    return this.hass.formatEntityState(entity);
  }
  moreInfo(entityId) {
    if (entityId) {
      this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
    }
  }
  text(key) {
    return translate(this.language(), key);
  }
  language() {
    return this.hass?.locale?.language ?? this.hass?.language ?? browserLanguage();
  }
  static get styles() {
    return [
      i`
                ha-card {
                    padding: 16px;
                    container-type: inline-size;
                    font-variant-numeric: tabular-nums;
                    --road-very-slippery: var(--road-conditions-very-slippery-color, var(--error-color, #db4437));
                    --road-slippery: var(--road-conditions-slippery-color, #f4511e);
                    --road-fair-winter: var(--road-conditions-fair-winter-color, #fb8c00);
                    --road-good-winter: var(--road-conditions-good-winter-color, #ffb300);
                    --road-fair: var(--road-conditions-fair-color, #9ccc65);
                    --road-good: var(--road-conditions-good-color, var(--success-color, #43a047));
                }

                button {
                    font: inherit;
                    color: inherit;
                    background: none;
                    border: none;
                    padding: 0;
                    margin: 0;
                    text-align: inherit;
                    cursor: pointer;
                }

                .card-title {
                    margin: 0 0 12px;
                    font-size: var(--ha-card-header-font-size, 24px);
                    font-weight: var(--ha-font-weight-normal, 400);
                    line-height: 1.2;
                }

                .name {
                    font-size: 16px;
                    font-weight: var(--ha-font-weight-medium, 500);
                    margin-bottom: 12px;
                }

                .message {
                    color: var(--secondary-text-color);
                }

                .grip-very_slippery {
                    color: var(--road-very-slippery);
                }
                .grip-slippery {
                    color: var(--road-slippery);
                }
                .grip-fair_winter {
                    color: var(--road-fair-winter);
                }
                .grip-good_winter {
                    color: var(--road-good-winter);
                }
                .grip-fair {
                    color: var(--road-fair);
                }
                .grip-good {
                    color: var(--road-good);
                }

                .grade {
                    display: flex;
                    justify-content: space-between;
                    align-items: baseline;
                    gap: 12px;
                    width: 100%;
                    margin-bottom: 10px;
                }

                .grade-text {
                    font-size: 20px;
                    font-weight: var(--ha-font-weight-medium, 500);
                }

                /* "0,22 µ" stays whole on its line. */
                .grip {
                    color: var(--primary-text-color);
                    white-space: nowrap;
                }

                .grade .grip {
                    font-size: 16px;
                }

                /* The scale is six parts, faint in the colours of their conditions, lit up to the one the road is in. */
                .scale {
                    display: grid;
                    grid-template-columns: repeat(6, minmax(0, 1fr));
                    gap: 3px;
                }

                .scale.large .part {
                    height: 8px;
                }

                .scale.small {
                    width: 72px;
                    gap: 2px;
                }

                .scale.small .part {
                    height: 4px;
                }

                .part {
                    background: currentColor;
                    opacity: 0.25;
                }

                .part.lit {
                    opacity: 1;
                }

                .scale.large .part:first-child {
                    border-radius: 4px 0 0 4px;
                }

                .scale.large .part:last-child {
                    border-radius: 0 4px 4px 0;
                }

                /* Equal side columns keep the middle label on the meter's middle gap, however long the outer ones are. */
                .scale-labels {
                    display: grid;
                    grid-template-columns: 1fr auto 1fr;
                    gap: 8px;
                    margin-top: 6px;
                    font-size: 11px;
                    color: var(--secondary-text-color);
                }

                .scale-labels span:last-child {
                    text-align: right;
                }

                /* The values flow into three columns, so a value the station lacks leaves no gap. */
                .values {
                    display: grid;
                    grid-template-columns: repeat(3, minmax(0, 1fr));
                    gap: 12px 8px;
                }

                /* Two columns on a narrow card (half a section), every value on one row on a wide one (two sections). */
                @container (max-width: 299px) {
                    .values {
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                    }
                }

                @container (min-width: 800px) {
                    .values {
                        grid-template-columns: none;
                        grid-auto-flow: column;
                        grid-auto-columns: minmax(0, 1fr);
                    }
                }

                .values.divided {
                    margin-top: 14px;
                    padding-top: 12px;
                    border-top: 1px solid var(--divider-color);
                }

                .value {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    min-width: 0;
                    font-size: 15px;
                }

                .icon {
                    flex: 0 0 auto;
                    width: 20px;
                    height: 20px;
                    --mdc-icon-size: 20px;
                    color: var(--state-icon-color, var(--secondary-text-color));
                }

                /* Weather Icons leave a wide margin inside their canvas, so they are drawn larger to match. */
                svg.icon {
                    width: 26px;
                    height: 26px;
                    margin: -3px;
                    fill: currentColor;
                }

                /* A value too long for its column wraps rather than being cut. */
                .value span {
                    min-width: 0;
                    overflow-wrap: anywhere;
                    line-height: 1.25;
                }

                /* Freezing or heavy precipitation matters at a glance. */
                .notable,
                .notable .icon {
                    color: var(--warning-color, #ffa600);
                }

                .warning {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    margin-top: 12px;
                    font-size: 14px;
                    line-height: 1.25;
                    color: var(--warning-color, #ffa600);
                }

                .warning .icon {
                    color: inherit;
                }

                .rows {
                    display: flex;
                    flex-direction: column;
                }

                /* Held to a height, by its height mode or a sections view's rows, the card is a column in which only the station's
                   view scrolls, under the title and the station's name, or the list of stations under the title. */
                ha-card.held {
                    box-sizing: border-box;
                    display: flex;
                    flex-direction: column;
                    overflow: clip;
                }

                ha-card.held > * {
                    flex: none;
                }

                /*
                 * It clips at its padding box, so it reaches 4 px out on every side, where the focus rings are drawn: over the
                 * card's padding at the sides and the bottom, and at the top over the 12 px margin under the title or the
                 * station's name, or over the card's padding, where nothing takes a tap.
                 */
                ha-card.held > .station,
                ha-card.held > .rows {
                    margin: -4px;
                    padding: 4px;
                    flex: 1 1 auto;
                    min-height: 0;
                    overflow-y: auto;
                    overscroll-behavior: contain;
                    scrollbar-width: thin;
                }

                .row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 12px;
                    width: 100%;
                    padding: 10px 0;
                }

                .row + .row {
                    border-top: 1px solid var(--divider-color);
                }

                .row-text {
                    display: flex;
                    flex-direction: column;
                    gap: 2px;
                    min-width: 0;
                }

                .row-name {
                    font-size: 15px;
                    overflow-wrap: anywhere;
                }

                .row-values {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 2px 12px;
                    font-size: 13px;
                    color: var(--secondary-text-color);
                }

                .row-value {
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    min-width: 0;
                    overflow-wrap: anywhere;
                }

                .row-value .icon {
                    width: 16px;
                    height: 16px;
                    --mdc-icon-size: 16px;
                }

                .row-value svg.icon {
                    width: 21px;
                    height: 21px;
                    margin: -2.5px;
                }

                .row-grade {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    gap: 4px;
                    flex: 0 0 auto;
                    font-size: 14px;
                    text-align: right;
                }

                .row-grade .grip {
                    font-size: 12px;
                    color: var(--secondary-text-color);
                }

                /* Beside a long grade a narrow card leaves the name and values no room, so the grade goes below them. */
                @container (max-width: 339px) {
                    .row {
                        flex-direction: column;
                        align-items: stretch;
                        gap: 6px;
                    }

                    .row-grade {
                        align-items: flex-start;
                        text-align: left;
                    }
                }
            `,
      fadeStyles
    ];
  }
};
__decorateClass([
  n4({ attribute: false })
], RoadConditionsCard.prototype, "hass", 2);
__decorateClass([
  n4({ attribute: false })
], RoadConditionsCard.prototype, "layout", 2);
__decorateClass([
  r5()
], RoadConditionsCard.prototype, "config", 2);
if (!customElements.get("road-conditions-card")) {
  console.info(
    `%c  ROAD-CONDITIONS-CARD 
%c  ${CARD_VERSION}    `,
    "color: orange; font-weight: bold; background: black",
    "color: white; font-weight: bold; background: dimgray"
  );
  const registry = window;
  registry.customCards = registry.customCards ?? [];
  registry.customCards.push({
    type: "road-conditions-card",
    name: translate(browserLanguage(), "common.name"),
    description: translate(browserLanguage(), "common.description"),
    documentationURL: "https://github.com/jesmak/digitraffic_live#road-conditions-card",
    preview: true
  });
  customElements.define("road-conditions-card", RoadConditionsCard);
}
export {
  RoadConditionsCard
};
