import { QuietAtmosphere } from "@/components/ui/Atmosphere";

export default function Page({ eyebrow, title, description, actions, children, width = "max-w-4xl" }) {
  return (
    <div className="min-h-0 flex-1 overflow-y-auto">
      <div className="relative overflow-hidden">
        <QuietAtmosphere />
        <div className={`relative mx-auto ${width} px-6 pt-16 pb-8 sm:px-8`}>
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="max-w-2xl">
              {eyebrow && <p className="caption-upper text-muted">{eyebrow}</p>}
              <h1 className={`display-md text-ink ${eyebrow ? "mt-3" : ""}`}>{title}</h1>
              {description && <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-body">{description}</p>}
            </div>
            {actions}
          </div>
        </div>
      </div>
      <div className={`relative mx-auto ${width} px-6 pb-20 sm:px-8`}>{children}</div>
    </div>
  );
}
