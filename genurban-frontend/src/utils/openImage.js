export function openImage(dataUrl) {
  const w = window.open("");
  const img = w.document.createElement("img");
  img.src = dataUrl;
  img.style.maxWidth = "100%";
  img.style.height = "auto";
  w.document.body.appendChild(img);
}
