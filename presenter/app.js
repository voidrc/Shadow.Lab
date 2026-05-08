/* ═══════════════════════════════════════════════════════════════
  Presenter — app.js
  Pure vanilla JS. No frameworks, no build step.
════════════════════════════════════════════════════════════════ */

"use strict";

// ─── State ──────────────────────────────────────────────────────────────────
const STATE = {
  title: "Untitled Presentation",
  slides: [],
  activeIdx: -1,
  viewerIdx: 0,
  transition: "fade",
};

// ─── Default slide template ─────────────────────────────────────────────────
function defaultSlide(overrides = {}) {
  return Object.assign(
    {
      id: crypto.randomUUID(),
      layout: "center", // center | top | split | blank
      bgType: "solid", // solid | gradient | image
      bgColor: "#080b08",
      bgGradient: "linear-gradient(135deg,#050a05 0%,#0a1a0a 50%,#050d05 100%)",
      bgImage: "",
      titleText: "Slide Title",
      titleColor: "#00ff41",
      titleSize: 48,
      subtitleText: "Subtitle or tagline",
      subtitleColor: "#4a9a5a",
      bodyText: "",
      bodyColor: "#c8d8c0",
      bodySize: 22,
      bullets: [],
      codeText: "",
      codeLang: "",
      imageUrl: "",
      showTitle: true,
      showSubtitle: true,
      showBody: false,
      showBullets: false,
      showCode: false,
      showImage: false,
      textAlign: "center",
      fontFamily: "'Courier New', 'Fira Mono', monospace",
      transition: "fade",
    },
    overrides,
  );
}

// ─── Persistence ────────────────────────────────────────────────────────────
const STORAGE_KEY = "presenter_data";
const THEME_VERSION = "cyber-v1";
const THEME_KEY = "presenter_theme_version";

function saveToStorage() {
  const data = {
    title: STATE.title,
    slides: STATE.slides,
    transition: STATE.transition,
  };
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (_) {}
}

function loadFromStorage() {
  try {
    if (localStorage.getItem(THEME_KEY) !== THEME_VERSION) {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.setItem(THEME_KEY, THEME_VERSION);
      return false;
    }
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return false;
    const data = JSON.parse(raw);
    STATE.title = data.title || "Untitled Presentation";
    STATE.slides = (data.slides || []).map((s) =>
      Object.assign(defaultSlide(), s),
    );
    STATE.transition = data.transition || "fade";
    return true;
  } catch (_) {
    return false;
  }
}

// ─── DOM refs ────────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const elSlideList = $("slide-list");
const elCanvas = $("slide-canvas");
const elPropsBody = $("props-body");
const elPresTitle = $("pres-title");
const elViewerOverlay = $("viewer-overlay");
const elViewerSlide = $("viewer-slide");
const elViewerStrip = $("viewer-strip");
const elViewerCounter = $("viewer-counter");

// ─── Slide rendering helpers ─────────────────────────────────────────────────
function applyBackground(el, slide) {
  if (slide.bgType === "solid") {
    el.style.background = slide.bgColor;
    el.style.backgroundImage = "";
  } else if (slide.bgType === "gradient") {
    el.style.background = slide.bgGradient;
    el.style.backgroundImage = "";
  } else if (slide.bgType === "image" && slide.bgImage) {
    el.style.backgroundImage = `url('${slide.bgImage}')`;
    el.style.backgroundSize = "cover";
    el.style.backgroundPosition = "center";
    el.style.backgroundColor = "#000";
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderSlideHTML(slide) {
  const layoutClass = `layout-${slide.layout}`;
  const alignStyle = `text-align:${slide.textAlign};`;
  const fontStyle = `font-family:${slide.fontFamily};`;

  let parts = "";

  if (slide.layout === "split") {
    let textParts = "";
    if (slide.showTitle)
      textParts += `<div class="slide-title" style="color:${slide.titleColor};font-size:${slide.titleSize}px">${escapeHtml(slide.titleText)}</div>`;
    if (slide.showSubtitle)
      textParts += `<div class="slide-subtitle" style="color:${slide.subtitleColor}">${escapeHtml(slide.subtitleText)}</div>`;
    if (slide.showBody)
      textParts += `<div class="slide-body" style="color:${slide.bodyColor};font-size:${slide.bodySize}px">${escapeHtml(slide.bodyText)}</div>`;
    if (slide.showBullets && slide.bullets.length)
      textParts += `<ul class="slide-bullets" style="color:${slide.bodyColor}">${slide.bullets.map((b) => `<li>${escapeHtml(b)}</li>`).join("")}</ul>`;

    let imgPart = "";
    if (slide.showImage && slide.imageUrl)
      imgPart = `<img class="slide-image" src="${escapeHtml(slide.imageUrl)}" alt="" />`;
    if (slide.showCode && slide.codeText)
      imgPart = `<pre class="slide-code">${escapeHtml(slide.codeText)}</pre>`;

    parts = `<div class="slide-text-col" style="${alignStyle}">${textParts}</div>
            <div class="slide-img-col">${imgPart}</div>`;
  } else {
    if (slide.showTitle)
      parts += `<div class="slide-title" style="color:${slide.titleColor};font-size:${slide.titleSize}px">${escapeHtml(slide.titleText)}</div>`;
    if (slide.showSubtitle)
      parts += `<div class="slide-subtitle" style="color:${slide.subtitleColor}">${escapeHtml(slide.subtitleText)}</div>`;
    if (slide.showBody)
      parts += `<div class="slide-body" style="color:${slide.bodyColor};font-size:${slide.bodySize}px">${escapeHtml(slide.bodyText)}</div>`;
    if (slide.showBullets && slide.bullets.length)
      parts += `<ul class="slide-bullets" style="color:${slide.bodyColor}">${slide.bullets.map((b) => `<li>${escapeHtml(b)}</li>`).join("")}</ul>`;
    if (slide.showCode && slide.codeText)
      parts += `<pre class="slide-code">${escapeHtml(slide.codeText)}</pre>`;
    if (slide.showImage && slide.imageUrl)
      parts += `<img class="slide-image" src="${escapeHtml(slide.imageUrl)}" alt="" />`;
  }

  return `<div class="slide-content ${layoutClass}" style="${alignStyle}${fontStyle}">${parts}</div>`;
}

// ─── Mini thumbnail render ────────────────────────────────────────────────────
function renderMini(slide) {
  const div = document.createElement("div");
  div.className = "mini-slide";
  applyBackground(div, slide);
  div.style.color = slide.titleColor;
  if (slide.showTitle)
    div.innerHTML += `<div style="font-weight:700;font-size:7px;margin-bottom:2px">${escapeHtml(slide.titleText)}</div>`;
  if (slide.showSubtitle)
    div.innerHTML += `<div style="font-size:5px;opacity:.7">${escapeHtml(slide.subtitleText)}</div>`;
  return div;
}

// ─── Canvas (editor preview) ─────────────────────────────────────────────────
function renderCanvas() {
  const slide = STATE.slides[STATE.activeIdx];
  if (!slide) {
    elCanvas.innerHTML =
      '<div class="canvas-placeholder">Select or add a slide</div>';
    elCanvas.style.background = "";
    return;
  }
  applyBackground(elCanvas, slide);
  elCanvas.innerHTML = renderSlideHTML(slide);
}

// ─── Slide list (left panel) ─────────────────────────────────────────────────
function renderSlideList() {
  elSlideList.innerHTML = "";
  STATE.slides.forEach((slide, i) => {
    const li = document.createElement("li");
    li.className =
      "slide-thumb-item" + (i === STATE.activeIdx ? " active" : "");
    li.dataset.idx = i;
    li.draggable = true;

    const num = document.createElement("span");
    num.className = "slide-num";
    num.textContent = i + 1;

    const preview = document.createElement("div");
    preview.className = "slide-thumb-preview";
    preview.appendChild(renderMini(slide));

    const actions = document.createElement("div");
    actions.className = "slide-thumb-actions";

    const btnDup = document.createElement("button");
    btnDup.className = "btn-icon";
    btnDup.title = "Duplicate";
    btnDup.textContent = "⎘";
    btnDup.addEventListener("click", (e) => {
      e.stopPropagation();
      duplicateSlide(i);
    });

    const btnDel = document.createElement("button");
    btnDel.className = "btn-icon";
    btnDel.title = "Delete";
    btnDel.textContent = "✕";
    btnDel.style.color = "#e05c5c";
    btnDel.addEventListener("click", (e) => {
      e.stopPropagation();
      confirmDeleteSlide(i);
    });

    actions.appendChild(btnDup);
    actions.appendChild(btnDel);

    li.appendChild(num);
    li.appendChild(preview);
    li.appendChild(actions);

    li.addEventListener("click", () => selectSlide(i));

    // ── Drag & drop reorder ──
    li.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", i);
      li.style.opacity = ".4";
    });
    li.addEventListener("dragend", () => {
      li.style.opacity = "";
    });
    li.addEventListener("dragover", (e) => {
      e.preventDefault();
      li.classList.add("drag-over");
    });
    li.addEventListener("dragleave", () => li.classList.remove("drag-over"));
    li.addEventListener("drop", (e) => {
      e.preventDefault();
      li.classList.remove("drag-over");
      const fromIdx = parseInt(e.dataTransfer.getData("text/plain"));
      if (fromIdx === i) return;
      const moved = STATE.slides.splice(fromIdx, 1)[0];
      STATE.slides.splice(i, 0, moved);
      STATE.activeIdx = i;
      refresh();
    });

    elSlideList.appendChild(li);
  });
}

// ─── Properties panel ────────────────────────────────────────────────────────
function renderProps() {
  const slide = STATE.slides[STATE.activeIdx];
  if (!slide) {
    elPropsBody.innerHTML =
      '<p class="props-hint">Select a slide to edit its properties.</p>';
    return;
  }

  const html = `
  <!-- Layout -->
  <div class="form-group">
    <label>Layout</label>
    <select id="p-layout">
      <option value="center" ${slide.layout === "center" ? "selected" : ""}>Center</option>
      <option value="top"    ${slide.layout === "top" ? "selected" : ""}>Top / Classic</option>
      <option value="split"  ${slide.layout === "split" ? "selected" : ""}>Split (Text + Media)</option>
      <option value="blank"  ${slide.layout === "blank" ? "selected" : ""}>Blank</option>
    </select>
  </div>

  <hr class="sep" />

  <!-- Background -->
  <div class="form-group">
    <label>Background Type</label>
    <select id="p-bgtype">
      <option value="solid"    ${slide.bgType === "solid" ? "selected" : ""}>Solid Color</option>
      <option value="gradient" ${slide.bgType === "gradient" ? "selected" : ""}>Gradient</option>
      <option value="image"    ${slide.bgType === "image" ? "selected" : ""}>Image URL</option>
    </select>
  </div>
  <div class="form-group" id="p-bg-solid-row"   ${slide.bgType !== "solid" ? 'style="display:none"' : ""}>
    <label>Background Color</label>
    <input type="color" id="p-bgcolor" value="${slide.bgColor}" />
  </div>
  <div class="form-group" id="p-bg-gradient-row" ${slide.bgType !== "gradient" ? 'style="display:none"' : ""}>
    <label>Gradient CSS</label>
    <input type="text" id="p-bggradient" value="${escapeHtml(slide.bgGradient)}" placeholder="linear-gradient(...)"/>
  </div>
  <div class="form-group" id="p-bg-image-row" ${slide.bgType !== "image" ? 'style="display:none"' : ""}>
    <label>Image URL</label>
    <input type="text" id="p-bgimage" value="${escapeHtml(slide.bgImage)}" placeholder="https://..."/>
  </div>

  <hr class="sep" />

  <!-- Title -->
  <div class="form-group">
    <label>
      <input type="checkbox" id="p-showtitle" ${slide.showTitle ? "checked" : ""}/>
      Show Title
    </label>
    <input type="text" id="p-title" value="${escapeHtml(slide.titleText)}" />
  </div>
  <div class="form-row">
    <div class="form-group">
      <label>Color</label>
      <input type="color" id="p-titlecolor" value="${slide.titleColor}" />
    </div>
    <div class="form-group">
      <label>Size (px)</label>
      <div class="slider-row">
        <input type="range" id="p-titlesize" min="16" max="100" value="${slide.titleSize}" />
        <span id="p-titlesize-val">${slide.titleSize}</span>
      </div>
    </div>
  </div>

  <hr class="sep" />

  <!-- Subtitle -->
  <div class="form-group">
    <label>
      <input type="checkbox" id="p-showsubtitle" ${slide.showSubtitle ? "checked" : ""}/>
      Show Subtitle
    </label>
    <input type="text" id="p-subtitle" value="${escapeHtml(slide.subtitleText)}" />
  </div>
  <div class="form-group">
    <label>Subtitle Color</label>
    <input type="color" id="p-subtitlecolor" value="${slide.subtitleColor}" />
  </div>

  <hr class="sep" />

  <!-- Body text -->
  <div class="form-group">
    <label>
      <input type="checkbox" id="p-showbody" ${slide.showBody ? "checked" : ""}/>
      Show Body Text
    </label>
    <textarea id="p-body">${escapeHtml(slide.bodyText)}</textarea>
  </div>
  <div class="form-row">
    <div class="form-group">
      <label>Color</label>
      <input type="color" id="p-bodycolor" value="${slide.bodyColor}" />
    </div>
    <div class="form-group">
      <label>Size (px)</label>
      <div class="slider-row">
        <input type="range" id="p-bodysize" min="10" max="60" value="${slide.bodySize}" />
        <span id="p-bodysize-val">${slide.bodySize}</span>
      </div>
    </div>
  </div>

  <hr class="sep" />

  <!-- Bullets -->
  <div class="form-group">
    <label>
      <input type="checkbox" id="p-showbullets" ${slide.showBullets ? "checked" : ""}/>
      Show Bullet Points
    </label>
    <textarea id="p-bullets" placeholder="One bullet per line">${escapeHtml(slide.bullets.join("\n"))}</textarea>
  </div>

  <hr class="sep" />

  <!-- Code -->
  <div class="form-group">
    <label>
      <input type="checkbox" id="p-showcode" ${slide.showCode ? "checked" : ""}/>
      Show Code Block
    </label>
    <textarea id="p-code" placeholder="Paste code here..." style="font-family:monospace;font-size:12px">${escapeHtml(slide.codeText)}</textarea>
  </div>

  <hr class="sep" />

  <!-- Image -->
  <div class="form-group">
    <label>
      <input type="checkbox" id="p-showimage" ${slide.showImage ? "checked" : ""}/>
      Show Image
    </label>
    <input type="text" id="p-imageurl" value="${escapeHtml(slide.imageUrl)}" placeholder="https://..." />
  </div>

  <hr class="sep" />

  <!-- Style -->
  <div class="form-group">
    <label>Text Align</label>
    <select id="p-align">
      <option value="left"   ${slide.textAlign === "left" ? "selected" : ""}>Left</option>
      <option value="center" ${slide.textAlign === "center" ? "selected" : ""}>Center</option>
      <option value="right"  ${slide.textAlign === "right" ? "selected" : ""}>Right</option>
    </select>
  </div>
  <div class="form-group">
    <label>Font Family</label>
    <select id="p-font">
      <option value="Segoe UI, system-ui, sans-serif"       ${slide.fontFamily.startsWith("Segoe") ? "selected" : ""}>System (Segoe UI)</option>
      <option value="Georgia, serif"                        ${slide.fontFamily === "Georgia, serif" ? "selected" : ""}>Georgia (Serif)</option>
      <option value="'Courier New', monospace"              ${slide.fontFamily.includes("Courier") ? "selected" : ""}>Courier (Mono)</option>
      <option value="Impact, fantasy"                       ${slide.fontFamily === "Impact, fantasy" ? "selected" : ""}>Impact (Bold)</option>
    </select>
  </div>

  <hr class="sep" />

  <!-- Transition -->
  <div class="form-group">
    <label>Slide Transition</label>
    <select id="p-transition">
      <option value="fade"    ${slide.transition === "fade" ? "selected" : ""}>Fade</option>
      <option value="slide-r" ${slide.transition === "slide-r" ? "selected" : ""}>Slide Right</option>
      <option value="slide-l" ${slide.transition === "slide-l" ? "selected" : ""}>Slide Left</option>
      <option value="zoom"    ${slide.transition === "zoom" ? "selected" : ""}>Zoom</option>
      <option value="none"    ${slide.transition === "none" ? "selected" : ""}>None</option>
    </select>
  </div>
  `;

  elPropsBody.innerHTML = html;
  bindPropsEvents(slide);
}

function bindPropsEvents(slide) {
  const get = (id) => document.getElementById(id);

  function update(key, val) {
    STATE.slides[STATE.activeIdx][key] = val;
    refresh();
  }

  const wire = (id, key, transform) => {
    const el = get(id);
    if (!el) return;
    el.addEventListener("input", () =>
      update(key, transform ? transform(el.value) : el.value),
    );
  };
  const wireChk = (id, key) => {
    const el = get(id);
    if (!el) return;
    el.addEventListener("change", () => update(key, el.checked));
  };

  wire("p-layout", "layout");
  wire("p-title", "titleText");
  wire("p-subtitle", "subtitleText");
  wire("p-body", "bodyText");
  wire("p-code", "codeText");
  wire("p-imageurl", "imageUrl");
  wire("p-bgcolor", "bgColor");
  wire("p-titlecolor", "titleColor");
  wire("p-subtitlecolor", "subtitleColor");
  wire("p-bodycolor", "bodyColor");
  wire("p-align", "textAlign");
  wire("p-font", "fontFamily");
  wire("p-transition", "transition");
  wire("p-bggradient", "bgGradient");
  wire("p-bgimage", "bgImage");
  wire("p-titlesize", "titleSize", Number);
  wire("p-bodysize", "bodySize", Number);

  wireChk("p-showtitle", "showTitle");
  wireChk("p-showsubtitle", "showSubtitle");
  wireChk("p-showbody", "showBody");
  wireChk("p-showbullets", "showBullets");
  wireChk("p-showcode", "showCode");
  wireChk("p-showimage", "showImage");

  // Bullets textarea → array
  const bulletsEl = get("p-bullets");
  if (bulletsEl)
    bulletsEl.addEventListener("input", () => {
      STATE.slides[STATE.activeIdx].bullets = bulletsEl.value
        .split("\n")
        .filter((l) => l.trim());
      refresh();
    });

  // Live slider labels
  const tsEl = get("p-titlesize");
  const tsVal = get("p-titlesize-val");
  if (tsEl && tsVal)
    tsEl.addEventListener("input", () => (tsVal.textContent = tsEl.value));

  const bsEl = get("p-bodysize");
  const bsVal = get("p-bodysize-val");
  if (bsEl && bsVal)
    bsEl.addEventListener("input", () => (bsVal.textContent = bsEl.value));

  // BG type switcher
  const bgtEl = get("p-bgtype");
  if (bgtEl)
    bgtEl.addEventListener("change", () => {
      const v = bgtEl.value;
      get("p-bg-solid-row").style.display = v === "solid" ? "" : "none";
      get("p-bg-gradient-row").style.display = v === "gradient" ? "" : "none";
      get("p-bg-image-row").style.display = v === "image" ? "" : "none";
      update("bgType", v);
    });
}

// ─── Full refresh ────────────────────────────────────────────────────────────
function refresh() {
  renderSlideList();
  renderCanvas();
  renderProps();
  saveToStorage();
}

function selectSlide(idx) {
  STATE.activeIdx = idx;
  refresh();
}

// ─── Add / duplicate / delete ────────────────────────────────────────────────
function addSlide() {
  const s = defaultSlide();
  STATE.slides.push(s);
  STATE.activeIdx = STATE.slides.length - 1;
  refresh();
  // Scroll slide list to bottom
  elSlideList.scrollTop = elSlideList.scrollHeight;
}

function duplicateSlide(idx) {
  const copy = JSON.parse(JSON.stringify(STATE.slides[idx]));
  copy.id = crypto.randomUUID();
  STATE.slides.splice(idx + 1, 0, copy);
  STATE.activeIdx = idx + 1;
  refresh();
}

function deleteSlide(idx) {
  STATE.slides.splice(idx, 1);
  if (STATE.activeIdx >= STATE.slides.length)
    STATE.activeIdx = STATE.slides.length - 1;
  refresh();
}

// ─── Modal ────────────────────────────────────────────────────────────────────
function showModal(title, body, onOk, okLabel = "OK", dangerous = true) {
  $("modal-title").textContent = title;
  $("modal-body").textContent = body;
  $("modal-ok").textContent = okLabel;
  $("modal-ok").className = "btn " + (dangerous ? "btn-danger" : "btn-primary");
  $("modal-backdrop").classList.remove("hidden");
  const okBtn = $("modal-ok");
  const cancelBtn = $("modal-cancel");
  const close = () => $("modal-backdrop").classList.add("hidden");
  const handleOk = () => {
    close();
    onOk();
    okBtn.removeEventListener("click", handleOk);
    cancelBtn.removeEventListener("click", close);
  };
  okBtn.addEventListener("click", handleOk);
  cancelBtn.addEventListener("click", close);
}

function confirmDeleteSlide(idx) {
  showModal(
    "Delete Slide",
    `Delete slide ${idx + 1}? This cannot be undone.`,
    () => deleteSlide(idx),
  );
}

// ─── Viewer ───────────────────────────────────────────────────────────────────
function openViewer(startIdx = 0) {
  if (!STATE.slides.length) return;
  STATE.viewerIdx = startIdx;
  buildViewerStrip();
  showViewerSlide(STATE.viewerIdx);
  elViewerOverlay.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closeViewer() {
  elViewerOverlay.classList.add("hidden");
  document.body.style.overflow = "";
}

function buildViewerStrip() {
  elViewerStrip.innerHTML = "";
  STATE.slides.forEach((slide, i) => {
    const div = document.createElement("div");
    div.className = "vstrip-thumb" + (i === STATE.viewerIdx ? " active" : "");
    div.appendChild(renderMini(slide));
    div.addEventListener("click", () => goViewerSlide(i));
    elViewerStrip.appendChild(div);
  });
}

function showViewerSlide(idx) {
  const slide = STATE.slides[idx];
  if (!slide) return;

  const trans = slide.transition || "fade";
  elViewerSlide.className = "viewer-slide";
  applyBackground(elViewerSlide, slide);
  elViewerSlide.innerHTML = renderSlideHTML(slide);

  if (trans !== "none") {
    void elViewerSlide.offsetWidth; // force reflow
    elViewerSlide.classList.add(`trans-${trans}`);
  }

  elViewerCounter.textContent = `${idx + 1} / ${STATE.slides.length}`;

  // Update strip active
  elViewerStrip.querySelectorAll(".vstrip-thumb").forEach((el, i) => {
    el.classList.toggle("active", i === idx);
  });

  // Scroll strip to active
  const activeThumb = elViewerStrip.children[idx];
  if (activeThumb)
    activeThumb.scrollIntoView({ inline: "center", block: "nearest" });
}

function goViewerSlide(idx) {
  if (idx < 0 || idx >= STATE.slides.length) return;
  STATE.viewerIdx = idx;
  showViewerSlide(idx);
}

// ─── Export / Import ─────────────────────────────────────────────────────────
function exportPresentation() {
  const data = {
    title: STATE.title,
    slides: STATE.slides,
    transition: STATE.transition,
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download =
    (STATE.title || "presentation").replace(/[^a-z0-9_-]/gi, "_") + ".json";
  a.click();
  URL.revokeObjectURL(a.href);
}

function importPresentation(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target.result);
      STATE.title = data.title || "Imported";
      STATE.slides = (data.slides || []).map((s) =>
        Object.assign(defaultSlide(), s),
      );
      STATE.transition = data.transition || "fade";
      STATE.activeIdx = STATE.slides.length > 0 ? 0 : -1;
      elPresTitle.value = STATE.title;
      refresh();
    } catch (_) {
      alert("Invalid presentation file.");
    }
  };
  reader.readAsText(file);
}

// ─── New presentation ─────────────────────────────────────────────────────────
function newPresentation() {
  showModal(
    "New Presentation",
    "Start a new presentation? Unsaved changes will be lost.",
    () => {
      STATE.title = "Untitled Presentation";
      STATE.slides = [];
      STATE.activeIdx = -1;
      elPresTitle.value = STATE.title;
      refresh();
      addSlide();
    },
  );
}

// ─── Keyboard shortcuts ───────────────────────────────────────────────────────
document.addEventListener("keydown", (e) => {
  // Viewer navigation
  if (!elViewerOverlay.classList.contains("hidden")) {
    if (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === " ") {
      e.preventDefault();
      goViewerSlide(STATE.viewerIdx + 1);
    } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
      e.preventDefault();
      goViewerSlide(STATE.viewerIdx - 1);
    } else if (e.key === "Escape") {
      closeViewer();
    } else if (e.key === "Home") {
      goViewerSlide(0);
    } else if (e.key === "End") {
      goViewerSlide(STATE.slides.length - 1);
    }
    return;
  }

  // Admin shortcuts (no modifier needed unless in input)
  const tag = document.activeElement?.tagName?.toLowerCase();
  const inInput = tag === "input" || tag === "textarea" || tag === "select";
  if (inInput) return;

  if (e.key === "Delete" && STATE.activeIdx >= 0) {
    confirmDeleteSlide(STATE.activeIdx);
  }
  if (e.key === "n" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    addSlide();
  }
  if (e.key === "d" && (e.ctrlKey || e.metaKey) && STATE.activeIdx >= 0) {
    e.preventDefault();
    duplicateSlide(STATE.activeIdx);
  }
  if (e.key === "F5" || e.key === "p") {
    e.preventDefault();
    openViewer(Math.max(0, STATE.activeIdx));
  }
  if (e.key === "ArrowUp" && STATE.activeIdx > 0) {
    selectSlide(STATE.activeIdx - 1);
  }
  if (e.key === "ArrowDown" && STATE.activeIdx < STATE.slides.length - 1) {
    selectSlide(STATE.activeIdx + 1);
  }
});

// ─── Deck Library ─────────────────────────────────────────────────────────────
const DECKS_INDEX = "decks/index.json";
let _libraryIndex = null; // cached index

const elLibraryOverlay = $("library-overlay");
const elLibraryBody = $("library-body");
const elLibrarySearch = $("library-search");

async function fetchLibraryIndex() {
  if (_libraryIndex) return _libraryIndex;
  try {
    const res = await fetch(DECKS_INDEX);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    _libraryIndex = await res.json();
    return _libraryIndex;
  } catch (e) {
    return null;
  }
}

async function fetchDeck(path) {
  const res = await fetch("decks/" + path);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function openLibrary() {
  elLibraryOverlay.classList.remove("hidden");
  elLibrarySearch.value = "";
  renderLibrary("");
  setTimeout(() => elLibrarySearch.focus(), 80);
}

function closeLibrary() {
  elLibraryOverlay.classList.add("hidden");
}

async function renderLibrary(query) {
  elLibraryBody.innerHTML = '<p class="props-hint">Loading...</p>';
  const index = await fetchLibraryIndex();

  if (!index) {
    elLibraryBody.innerHTML = `
      <p class="lib-empty">
        [ERR] Could not load decks/index.json<br/>
        <span style="font-size:11px;color:var(--text-muted)">
          Run md2deck.py first, or open via a web server (not file://).
        </span>
      </p>`;
    return;
  }

  const q = query.trim().toLowerCase();
  const categories = index.categories || {};
  const catKeys = Object.keys(categories).sort();

  let totalVisible = 0;
  const html = catKeys
    .map((cat) => {
      const decks = (categories[cat] || []).filter(
        (d) => !q || d.title.toLowerCase().includes(q) || cat.includes(q),
      );
      if (!decks.length) return "";
      totalVisible += decks.length;

      const cards = decks
        .map(
          (d) => `
      <div class="lib-deck-card" data-path="${d.path}">
        <div class="lib-deck-name" title="${escapeHtml(d.title)}">${escapeHtml(d.title)}</div>
        <div class="lib-deck-meta">${d.slides} slides &nbsp;·&nbsp; ${escapeHtml(d.source)}</div>
        <div class="lib-deck-actions">
          <button class="btn btn-ghost lib-btn-edit"   data-path="${d.path}">Edit</button>
          <button class="btn btn-primary lib-btn-exec" data-path="${d.path}">[EXEC]</button>
        </div>
      </div>`,
        )
        .join("");

      return `
      <div class="lib-category">
        <div class="lib-category-label">${escapeHtml(cat)}</div>
        <div class="lib-deck-grid">${cards}</div>
      </div>`;
    })
    .join("");

  elLibraryBody.innerHTML = totalVisible
    ? html
    : `<p class="lib-empty">No decks match "${escapeHtml(q)}"</p>`;

  // Wire card buttons
  elLibraryBody.querySelectorAll(".lib-btn-edit").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      await libraryLoadDeck(btn.dataset.path, false);
    });
  });
  elLibraryBody.querySelectorAll(".lib-btn-exec").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      await libraryLoadDeck(btn.dataset.path, true);
    });
  });
  // Clicking the card itself = edit
  elLibraryBody.querySelectorAll(".lib-deck-card").forEach((card) => {
    card.addEventListener("click", async () => {
      await libraryLoadDeck(card.dataset.path, false);
    });
  });
}

async function libraryLoadDeck(path, presentImmediately) {
  try {
    const deck = await fetchDeck(path);
    STATE.title = deck.title || "Imported";
    STATE.slides = (deck.slides || []).map((s) =>
      Object.assign(defaultSlide(), s),
    );
    STATE.transition = deck.transition || "fade";
    STATE.activeIdx = STATE.slides.length > 0 ? 0 : -1;
    elPresTitle.value = STATE.title;
    document.title = `Presenter — ${STATE.title}`;
    saveToStorage();
    refresh();
    closeLibrary();
    if (presentImmediately) openViewer(0);
  } catch (e) {
    alert(`[ERR] Failed to load deck: ${e.message}`);
  }
}

// Search input live filter
elLibrarySearch.addEventListener("input", () =>
  renderLibrary(elLibrarySearch.value),
);

// Close on backdrop click
elLibraryOverlay.addEventListener("click", (e) => {
  if (e.target === elLibraryOverlay) closeLibrary();
});

// Close on Escape
document.addEventListener(
  "keydown",
  (e) => {
    if (e.key === "Escape" && !elLibraryOverlay.classList.contains("hidden")) {
      closeLibrary();
    }
  },
  true,
);

// ─── URL param: ?deck=decks/linux/cli.json ────────────────────────────────────
async function checkUrlDeckParam() {
  const params = new URLSearchParams(window.location.search);
  const deckParam = params.get("deck");
  if (!deckParam) return;
  // strip leading "decks/" if user included it
  const path = deckParam.replace(/^decks\//, "");
  try {
    const deck = await fetchDeck(path);
    STATE.title = deck.title || "Imported";
    STATE.slides = (deck.slides || []).map((s) =>
      Object.assign(defaultSlide(), s),
    );
    STATE.transition = deck.transition || "fade";
    STATE.activeIdx = STATE.slides.length > 0 ? 0 : -1;
    elPresTitle.value = STATE.title;
    document.title = `Presenter — ${STATE.title}`;
    refresh();
    // ?present=1 to auto-launch viewer
    if (params.get("present") === "1") openViewer(0);
  } catch (e) {
    console.warn("[Presenter] Could not load deck from URL param:", e.message);
  }
}

// ─── Event wiring ─────────────────────────────────────────────────────────────
$("btn-add-slide").addEventListener("click", addSlide);
$("btn-present").addEventListener("click", () =>
  openViewer(Math.max(0, STATE.activeIdx)),
);
$("btn-export").addEventListener("click", exportPresentation);
$("btn-new").addEventListener("click", newPresentation);
$("btn-import").addEventListener("click", () => $("file-import").click());
$("file-import").addEventListener("change", (e) => {
  if (e.target.files[0]) importPresentation(e.target.files[0]);
  e.target.value = "";
});

elPresTitle.addEventListener("input", () => {
  STATE.title = elPresTitle.value;
  saveToStorage();
  document.title = `Presenter — ${STATE.title}`;
});

$("v-prev").addEventListener("click", () => goViewerSlide(STATE.viewerIdx - 1));
$("v-next").addEventListener("click", () => goViewerSlide(STATE.viewerIdx + 1));
$("v-exit").addEventListener("click", closeViewer);

$("btn-library").addEventListener("click", openLibrary);
$("library-close").addEventListener("click", closeLibrary);

// ─── Init ─────────────────────────────────────────────────────────────────────
(function init() {
  const loaded = loadFromStorage();
  elPresTitle.value = STATE.title;
  document.title = `Presenter — ${STATE.title}`;

  if (!loaded || STATE.slides.length === 0) {
    // Seed with a welcome presentation
    STATE.slides = [
      defaultSlide({
        titleText: "// PRESENTER",
        subtitleText: "browser-native slide deck engine :: v1.0.0",
        bgType: "gradient",
        bgGradient:
          "linear-gradient(160deg,#020602 0%,#051505 40%,#020a02 100%)",
        titleColor: "#00ff41",
        subtitleColor: "#2a6b3a",
        titleSize: 52,
        fontFamily: "'Courier New', 'Fira Mono', monospace",
        transition: "zoom",
      }),
      defaultSlide({
        titleText: "> GETTING STARTED",
        subtitleText: "",
        showSubtitle: false,
        showBullets: true,
        bullets: [
          '[+]  Click "+ Slide" to inject a new slide',
          "[*]  Select a slide in the left panel to target it",
          "[~]  Edit content & style in the right panel",
          "[↕]  Drag slides to reorder the payload",
          "[▶]  Press [EXEC] or F5 to deploy the presentation",
          "[S]  Auto-saved to browser localStorage",
        ],
        bgType: "gradient",
        bgGradient: "linear-gradient(160deg,#030803 0%,#061206 100%)",
        titleColor: "#00ff41",
        bodyColor: "#7ab87a",
        textAlign: "left",
        layout: "top",
        fontFamily: "'Courier New', 'Fira Mono', monospace",
        transition: "slide-r",
      }),
      defaultSlide({
        titleText: "> KEYBINDINGS",
        showSubtitle: false,
        showBullets: true,
        bullets: [
          "← / →    ::  navigate slides",
          "F5 / P   ::  exec presentation",
          "Esc      ::  terminate viewer",
          "Ctrl+N   ::  inject new slide",
          "Ctrl+D   ::  clone slide",
          "Delete   ::  purge selected slide",
          "↑ / ↓   ::  traverse slide list",
        ],
        bgType: "gradient",
        bgGradient: "linear-gradient(160deg,#030803 0%,#04100a 100%)",
        titleColor: "#00ff41",
        bodyColor: "#7ab87a",
        textAlign: "left",
        layout: "top",
        fontFamily: "'Courier New', 'Fira Mono', monospace",
        transition: "slide-r",
      }),
      defaultSlide({
        titleText: "DEMO :: CODE SLIDE",
        subtitleText: "syntax-highlighted terminal block",
        showCode: true,
        showBody: false,
        codeText:
          '#!/usr/bin/env python3\n# grey-hat recon script\nimport socket, sys\n\ntarget = sys.argv[1]\nports  = range(1, 1025)\n\nfor port in ports:\n    s = socket.socket()\n    s.settimeout(0.5)\n    if s.connect_ex((target, port)) == 0:\n        print(f"[OPEN]  {target}:{port}")\n    s.close()',
        bgType: "gradient",
        bgGradient: "linear-gradient(160deg,#020602 0%,#040d04 100%)",
        titleColor: "#00ff41",
        subtitleColor: "#2a6b3a",
        fontFamily: "'Courier New', 'Fira Mono', monospace",
        layout: "top",
        transition: "fade",
      }),
    ];
    STATE.activeIdx = 0;
    saveToStorage();
  } else {
    STATE.activeIdx = 0;
  }

  refresh();
  checkUrlDeckParam();
})();
