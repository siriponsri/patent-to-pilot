// Tiny DOM builder. All content is set through text nodes/attributes; the app
// never assigns innerHTML, so source text and user notes stay inert.

export function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === 'class') el.className = v;
    else if (k === 'value') el.value = v;
    else if (k === 'checked' || k === 'selected' || k === 'disabled') el[k] = Boolean(v);
    else el.setAttribute(k, v === true ? '' : String(v));
  }
  append(el, children);
  return el;
}

function append(el, children) {
  for (const c of children) {
    if (c === null || c === undefined || c === false) continue;
    if (Array.isArray(c)) append(el, c);
    else el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
}

/** Human date-time; Gregorian calendar in both locales so years never shift silently. */
export function fmtTime(locale, iso) {
  if (!iso) return null;
  try {
    return new Intl.DateTimeFormat(locale === 'th' ? 'th-TH-u-ca-gregory' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(iso));
  } catch { return iso; }
}

let seq = 0;
export const uid = (p = 'id') => `${p}-${++seq}`;

/** Labelled form control. */
export function field(label, control, help) {
  const id = control.id || (control.id = uid('f'));
  const helpId = help ? `${id}-help` : null;
  if (helpId) control.setAttribute('aria-describedby', helpId);
  return h('div', { class: 'field' }, h('label', { for: id }, label), control, help ? h('p', { class: 'help', id: helpId }, help) : null);
}

export function copyButton(text, t) {
  const btn = h('button', { type: 'button', class: 'btn btn-small', 'aria-label': `${t('source.copy')}: ${text}` }, t('source.copy'));
  btn.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(text); btn.textContent = t('source.copied'); } catch { btn.textContent = '—'; }
  });
  return btn;
}

/** Start a browser download. Claims only that the download started. */
export function download(filename, text, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([text], { type: `${type};charset=utf-8` }));
  const a = h('a', { href: url, download: filename, hidden: true });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
}
