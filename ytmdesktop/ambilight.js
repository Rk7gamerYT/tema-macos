// Brilho ambiente (estilo youtube-ambilight) atrás do player do YouTube Music.
// Copia o vídeo, ou a capa quando é só música, para um canvas pequeno e borrado
// atrás do player. Roda dentro da página (injetado pela cópia corrigida do app).
// Desligar: bash ~/tema-macos/ytmdesktop/aplicar.sh --sem-ambilight
(() => {
  if (window.__macAmbilight) return;
  window.__macAmbilight = true;

  const W = 64, H = 36, FPS = 15;
  const canvas = document.createElement("canvas");
  canvas.id = "mac-ambilight";
  canvas.width = W;
  canvas.height = H;
  Object.assign(canvas.style, {
    position: "fixed", pointerEvents: "none", zIndex: "0", opacity: "0",
    filter: "blur(48px) saturate(170%) brightness(1.1)", transition: "opacity .6s ease",
    borderRadius: "40px"
  });
  const ctx = canvas.getContext("2d", { alpha: false });

  function source() {
    const page = document.querySelector("ytmusic-player-page");
    const player = page && page.querySelector("ytmusic-player");
    if (!player) return null;
    const r = player.getBoundingClientRect();
    if (r.width < 80 || r.height < 80 || r.bottom < 0 || r.top > innerHeight) return null;
    const video = player.querySelector("video");
    const songOnly = player.getAttribute("playback-mode") === "ATV_PREFERRED" || !video || video.readyState < 2;
    if (!songOnly && video.videoWidth) return { r, player, el: video };
    const img = player.querySelector("#song-image img, #thumbnail img, img");
    if (img && img.complete && img.naturalWidth) return { r, player, el: img };
    return null;
  }

  let last = 0;
  function tick(t) {
    requestAnimationFrame(tick);
    if (document.hidden || t - last < 1000 / FPS) return;
    last = t;
    const s = source();
    if (!s) { canvas.style.opacity = "0"; return; }
    if (canvas.parentNode !== s.player.parentNode) {
      s.player.parentNode.insertBefore(canvas, s.player);
      if (getComputedStyle(s.player).position === "static") s.player.style.position = "relative";
      s.player.style.zIndex = "1";
    }
    const pad = 0.12;
    Object.assign(canvas.style, {
      left: `${s.r.left - s.r.width * pad}px`, top: `${s.r.top - s.r.height * pad}px`,
      width: `${s.r.width * (1 + 2 * pad)}px`, height: `${s.r.height * (1 + 2 * pad)}px`
    });
    try { ctx.drawImage(s.el, 0, 0, W, H); } catch { return; }
    canvas.style.opacity = "0.6";
  }
  requestAnimationFrame(tick);
})();
