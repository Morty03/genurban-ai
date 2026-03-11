// src/utils/displayBase64.js
export function openDataUrl(dataUrl) {
  const w = window.open("");
  if (!w) return alert("Popup blocked — allow popups for this site.");
  const img = w.document.createElement("img");
  img.src = dataUrl;
  img.style.maxWidth = "100%";
  img.style.height = "auto";
  w.document.body.style.margin = "0";
  w.document.body.appendChild(img);
}
