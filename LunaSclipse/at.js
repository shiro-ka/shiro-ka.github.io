// 端末幅でボタンコンテナの内容を切り替え
async function loadButtonContainer() {
  const container = document.querySelector('.script-button-container');
  if (!container) return;
  let file = window.innerWidth < 768
  ? 'button-container-mobile.html'
  : 'button-container-pc.html';
  const res = await fetch(file);
  container.innerHTML = await res.text();
}
window.addEventListener('DOMContentLoaded', loadButtonContainer);
window.addEventListener('resize', loadButtonContainer);