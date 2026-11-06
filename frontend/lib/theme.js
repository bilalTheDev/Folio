export const THEME_KEY = "folio-theme";

export const THEME_SCRIPT = `(()=>{try{var s=localStorage.getItem("folio-theme");var d=s==="dark"||(s!=="light"&&matchMedia("(prefers-color-scheme: dark)").matches);document.documentElement.classList.toggle("dark",d)}catch(e){}})()`;

export function applyTheme(theme) {
  document.documentElement.classList.toggle("dark", theme === "dark");
}

export function readTheme() {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === "dark" || stored === "light") return stored;
  } catch {
    /* private mode */
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function persistTheme(theme) {
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* private mode */
  }
  applyTheme(theme);
}
