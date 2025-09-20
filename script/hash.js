/* ハッシュに対応したhtmlの読み込み(なにもない場合はhome.html) */
function loadHashContent() {
  const hash = location.hash.replace('#', '');
  const containers = document.getElementsByClassName('script-hash-container');
  if (containers.length === 0) return;
  const isMobile = window.innerWidth <= 768;
  const dir = isMobile ? 'hash-mobile' : 'hash-pc';
  const file = hash ? `${dir}/${hash}.html` : `${dir}/home.html`;
  fetch(file)
    .then(res => res.text())
    .then(html => {
      for (const el of containers) {
        el.innerHTML = html;
      }
    });
}
window.addEventListener('DOMContentLoaded', loadHashContent);
window.addEventListener('hashchange', loadHashContent);