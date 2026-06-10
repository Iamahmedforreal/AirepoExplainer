import type { ReactNode } from "react";

type SectionProps = {
  id?: string;
  label?: string;
  title?: ReactNode;
  intro?: ReactNode;
  children?: ReactNode;
  className?: string;
  align?: "left" | "center";
};

export default function Section({
  id,
  label,
  title,
  intro,
  children,
  className = "",
  align = "left",
}: SectionProps) {
  const centered = align === "center";
  return (
    <section
      id={id}
      className={`relative border-t border-line px-6 py-20 sm:px-10 md:py-28 ${className}`}
    >
      <div className="mx-auto w-full max-w-6xl">
        {(label || title || intro) && (
          <div
            className={`mb-12 md:mb-16 ${
              centered ? "mx-auto max-w-2xl text-center" : "max-w-2xl"
            }`}
          >
            {label && (
              <div
                className={`mono-label mb-5 flex items-center gap-2 ${
                  centered ? "justify-center" : ""
                }`}
              >
                <span className="not-italic text-ink" aria-hidden="true">
                  &#10095;
                </span>
                <span>{label}</span>
              </div>
            )}
            {title && (
              <h2 className="text-balance text-3xl sm:text-4xl md:text-[2.75rem]">
                {title}
              </h2>
            )}
            {intro && (
              <p className="mt-5 text-base leading-relaxed text-muted sm:text-lg">
                {intro}
              </p>
            )}
          </div>
        )}
        {children}
      </div>
    </section>
  );
}
