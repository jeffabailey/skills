# Browser Recipes

Small page scripts for the review-usability walkthrough. Each returns compact JSON, which costs far less than an accessibility snapshot (often 60,000+ characters on a long page). Paste the function body into the browser tool's script runner (`evaluate_script`, `javascript_tool`, or Playwright's `page.evaluate`).

## Viewport size (record in the report header)

```js
() => ({ w: innerWidth, h: innerHeight, dpr: devicePixelRatio, url: location.href })
```

Record width **and** height. The desktop "first screen" check depends on height: a maximized window with browser chrome often has an inner height near 600-700px, not 800+.

## Where the main content starts

```js
() => {
  const main = document.querySelector('main, article, [role=main]') || document.body;
  const first = main.querySelector('p, pre, ol, ul, table') || main;
  const top = Math.round(first.getBoundingClientRect().top + scrollY);
  return { top, screens: +(top / innerHeight).toFixed(2), vh: innerHeight, tag: first.tagName };
}
```

## Keyboard: is the target reachable and is focus visible?

Synthetic `Tab` events from a script do not move focus, and some tools (Chrome DevTools `press_key`) attach a full snapshot to every key press. So check reach from the tab order instead of pressing Tab repeatedly:

```js
(sel) => {
  const el = document.querySelector(sel);
  if (!el) return { found: false };
  const tabbable = [...document.querySelectorAll('a[href],button,input,select,textarea,[tabindex]')]
    .filter(e => e.tabIndex >= 0 && !e.disabled && e.offsetParent !== null);
  el.focus();
  const cs = getComputedStyle(el);
  return { found: true, index: tabbable.indexOf(el), of: tabbable.length,
           focused: document.activeElement === el,
           outline: cs.outlineStyle + ' ' + cs.outlineWidth, boxShadow: cs.boxShadow };
}
```

`index` is how many Tab presses it takes from the top of the page. Compare the focused style with the unfocused one to judge visibility. Use one real key press only when you must confirm behavior, on the shortest page that shows it, or with a tool whose key action returns no snapshot (for example Claude in Chrome's `computer` key action).

## Keyboard shortcuts (`/`, `Ctrl+K`)

Dispatch the key from a script instead of a tool key press:

```js
() => {
  const before = location.href;
  document.dispatchEvent(new KeyboardEvent('keydown', { key: '/', code: 'Slash', bubbles: true }));
  return { before, activeTag: document.activeElement.tagName, activeId: document.activeElement.id };
}
```

A shortcut may **navigate** (for example `/` opening `/search/`), which destroys the script context and surfaces as "Execution context was destroyed". That is a result, not a tool failure: read `location.href` in a fresh call and record "shortcut navigates to <URL>".

## Render errors outside code samples

Searching the whole page for `Error:` false-positives on articles that show error messages in code blocks. Scan only text outside `pre` and `code`:

```js
() => {
  const pat = /Syntax error|Parse error|Unsupported markdown|Error:/;
  const hits = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode;
    if (n.parentElement.closest('pre, code, script, style')) continue;
    if (pat.test(n.textContent)) hits.push(n.parentElement.tagName + ': ' + n.textContent.trim().slice(0, 80));
  }
  return hits.slice(0, 10);
}
```

Also check `svg` elements inside diagram containers for an error class (Mermaid renders `.error-icon` / `aria-roledescription="error"`).

## Back button (bfcache vs real restore)

1. `() => { window.__probe = 1; return location.href; }`
2. Navigate away, then go Back.
3. `() => ({ probe: window.__probe ?? null, url: location.href, scrollY })` — a surviving probe means the back/forward cache served the page, so the page's own restore code did not run.
4. Reload, and read the same state again. Report both results.

## Phone viewport when resizing fails

```js
() => { window.open(location.href, 'phone', 'popup,width=390,height=844'); return true; }
```

Then switch the tool to the new page and run the viewport recipe to record the actual size.
