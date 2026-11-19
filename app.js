'use strict';
document.documentElement.classList.add('js');
// Native controls remain usable without JavaScript. Tabs only hide content after setup.
document.querySelectorAll('[data-tabs]').forEach(group => {
  const buttons = [...group.querySelectorAll('[role="tab"]')];
  const activate = button => {
    buttons.forEach(tab => {
      const selected = tab === button;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
      const panel = document.getElementById(tab.getAttribute('aria-controls'));
      panel.hidden = !selected;
      if (!selected) panel.querySelectorAll('video').forEach(video => video.pause());
    });
  };
  buttons.forEach((button, index) => {
    button.addEventListener('click', () => activate(button));
    button.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % buttons.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + buttons.length) % buttons.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = buttons.length - 1;
      if (next !== undefined) {
        event.preventDefault();
        activate(buttons[next]);
        buttons[next].focus();
      }
    });
  });
  activate(buttons[0]);
});
const videos = [...document.querySelectorAll('video')];
videos.forEach(video => video.addEventListener('play', () => {
  videos.forEach(other => { if (other !== video) other.pause(); });
}));
document.addEventListener('visibilitychange', () => {
  if (document.hidden) videos.forEach(video => video.pause());
});
const figureDialog = document.getElementById('figure-dialog');
const expandedFigure = document.getElementById('expanded-figure');
if (typeof figureDialog.showModal === 'function') {
  document.querySelectorAll('.zoomable').forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    expandedFigure.src = link.href;
    expandedFigure.alt = link.querySelector('img').alt;
    figureDialog.showModal();
  }));
  document.getElementById('close-figure').addEventListener('click', () => figureDialog.close());
  figureDialog.addEventListener('click', event => {
    const box = figureDialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) figureDialog.close();
  });
}
const copyButton = document.getElementById('copy-citation');
copyButton.addEventListener('click', async () => {
  const citation = document.getElementById('bibtex').textContent;
  let copied = false;
  try {
    if (!navigator.clipboard) throw new Error('Clipboard API unavailable');
    await navigator.clipboard.writeText(citation);
    copied = true;
  } catch {
    const area = document.createElement('textarea');
    area.value = citation;
    area.style.position = 'fixed';
    area.style.left = '-9999px';
    document.body.append(area);
    area.select();
    try { copied = document.execCommand('copy'); } catch { copied = false; }
    area.remove();
    copyButton.focus();
  }
  copyButton.textContent = copied ? 'Copied ✓' : 'Select text to copy';
  document.getElementById('copy-status').textContent = copied ? 'Citation copied to clipboard.' : 'Copy unavailable. Please select and copy the citation text.';
  setTimeout(() => { copyButton.textContent = 'Copy BibTeX'; }, 2500);
});
if ('IntersectionObserver' in window) {
  const navLinks = [...document.querySelectorAll('.nav-links a')];
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) navLinks.forEach(link => {
        const active = link.hash === '#' + entry.target.id;
        link.classList.toggle('active', active);
        if (active) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    });
  }, {rootMargin:'-15% 0px -65% 0px'});
  navLinks.forEach(link => observer.observe(document.querySelector(link.hash)));
}
