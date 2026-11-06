"use client";

import { useEffect, useState } from "react";
import { persistTheme, readTheme } from "@/lib/theme";

const CHOICES = [
  { id: "light", title: "Light", body: "Off-white canvas and warm ink." },
  { id: "dark", title: "Dark", body: "Ink canvas and off-white type." },
];

export default function ThemeToggle({ className = "" }) {
  const [theme, setTheme] = useState(null);

  useEffect(() => {
    Promise.resolve().then(() => setTheme(readTheme()));
  }, []);

  const dark = theme === "dark";

  const toggle = () => {
    const next = dark ? "light" : "dark";
    persistTheme(next);
    setTheme(next);
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      title={dark ? "Light theme" : "Dark theme"}
      className={`grid size-9 place-items-center rounded-full text-muted transition-colors hover:bg-strong hover:text-ink ${className}`}
    >
      {theme === null ? (
        <span className="size-4" />
      ) : dark ? (
        // Light mode icon by Freepik on Flaticon: https://www.flaticon.com/free-icon/light-mode_17648604
        <span
          className="size-5 bg-current"
          style={{
            WebkitMaskImage: "url(/light-mode-17648604.png)",
            maskImage: "url(/light-mode-17648604.png)",
            WebkitMaskRepeat: "no-repeat",
            maskRepeat: "no-repeat",
            WebkitMaskPosition: "center",
            maskPosition: "center",
            WebkitMaskSize: "contain",
            maskSize: "contain",
          }}
          aria-hidden="true"
        />
      ) : (
        <svg className="size-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path d="M17.293 13.293A8 8 0 0 1 6.707 2.707a8.001 8.001 0 1 0 10.586 10.586Z" />
        </svg>
      )}
    </button>
  );
}

export function ThemePicker() {
  const [theme, setTheme] = useState(null);

  useEffect(() => {
    Promise.resolve().then(() => setTheme(readTheme()));
  }, []);

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {CHOICES.map((choice) => {
        const selected = theme === choice.id;
        return (
          <button
            key={choice.id}
            type="button"
            onClick={() => {
              persistTheme(choice.id);
              setTheme(choice.id);
            }}
            aria-pressed={selected}
            className={`rounded-2xl border p-5 text-left transition-colors ${
              selected ? "border-ink bg-card ring-1 ring-ink" : "border-hairline bg-card hover:shadow-soft"
            }`}
          >
            <p className="text-sm font-medium text-ink">{choice.title}</p>
            <p className="mt-1 text-sm text-muted">{choice.body}</p>
          </button>
        );
      })}
    </div>
  );
}
