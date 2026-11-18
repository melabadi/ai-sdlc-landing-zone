// The guide's one script: open a screenshot in a lightbox instead of leaving the page. Without it, the link still
// opens the full-size image.
(() => {
  const links = document.querySelectorAll('a.shot-link');
  if (!links.length || typeof HTMLDialogElement !== 'function') return;

  const dialog = document.createElement('dialog');
  dialog.className = 'lightbox';
  dialog.setAttribute('aria-label', 'Screenshot');
  const close = document.createElement('button');
  close.type = 'button';
  close.className = 'lightbox-close';
  close.setAttribute('aria-label', 'Close the screenshot');
  close.textContent = '×';
  const scroller = document.createElement('div');
  scroller.className = 'lightbox-scroll';
  const image = document.createElement('img');
  image.alt = '';
  scroller.append(image);
  dialog.append(close, scroller);
  document.body.append(dialog);

  links.forEach((link) => {
    link.addEventListener('click', (event) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      const thumb = link.querySelector('img');
      image.src = link.href;
      image.alt = thumb ? thumb.alt : '';
      dialog.showModal();
      scroller.scrollTop = 0;
      close.focus();
    });
  });
  close.addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener('close', () => image.removeAttribute('src'));
})();
