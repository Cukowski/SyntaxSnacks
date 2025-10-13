/* Minimal site JS — safe to keep or remove entirely
   - No form interception
   - No page swapping
   - Optional parallax if .bg-shapes exists
*/
(() => {
  const $  = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => root.querySelectorAll(sel);

  // --- Optional subtle mouse parallax for decorative shapes ---
  const shapes = $$('.shape');
  if (shapes.length) {
    document.addEventListener('mousemove', (e) => {
      const x = e.clientX / window.innerWidth;
      const y = e.clientY / window.innerHeight;
      shapes.forEach((shape, i) => {
        const speed = (i + 1) * 0.4;
        shape.style.transform =
          `translate(${(x - 0.5) * speed * 18}px, ${(y - 0.5) * speed * 18}px)`;
      });
    });
  }

  // --- Optional scroll parallax for a hero container ---
  const parallax = $('.bg-shapes');
  if (parallax) {
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const s = window.pageYOffset * 0.4;
        parallax.style.transform = `translateY(${s}px)`;
        ticking = false;
      });
    }, { passive: true });
  }

  // That’s all. If you don’t need parallax, you can even ship an empty file.
})();
