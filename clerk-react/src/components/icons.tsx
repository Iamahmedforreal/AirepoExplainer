import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const base = {
  width: 24,
  height: 24,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export const LogoMark = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M8 6 3 12l5 6" />
    <path d="m16 6 5 6-5 6" />
    <path d="M13.5 4.5 10.5 19.5" strokeWidth={1.2} />
  </svg>
);

export const Graph = (props: IconProps) => (
  <svg {...base} {...props}>
    <circle cx="5" cy="6" r="2.2" />
    <circle cx="19" cy="6" r="2.2" />
    <circle cx="12" cy="18" r="2.4" />
    <path d="M6.7 7.6 10.6 16M17.3 7.6 13.4 16M7 6h10" />
  </svg>
);

export const Parse = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M9 8 5 12l4 4M15 8l4 4-4 4" />
  </svg>
);

export const Index = (props: IconProps) => (
  <svg {...base} {...props}>
    <ellipse cx="12" cy="6" rx="7" ry="3" />
    <path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6" />
    <path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
  </svg>
);

export const Brain = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-1.5 5.6A3 3 0 0 0 6 18a3 3 0 0 0 3 2V4Z" />
    <path d="M15 4a3 3 0 0 1 3 3 3 3 0 0 1 1.5 5.6A3 3 0 0 1 18 18a3 3 0 0 1-3 2V4Z" />
    <path d="M9 9h1.5M9 13h1.5M15 9h-1.5M15 13h-1.5" strokeWidth={1.2} />
  </svg>
);

export const Link = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M10 14a3.5 3.5 0 0 0 5 0l3-3a3.5 3.5 0 0 0-5-5l-1.5 1.5" />
    <path d="M14 10a3.5 3.5 0 0 0-5 0l-3 3a3.5 3.5 0 0 0 5 5L12.5 16.5" />
  </svg>
);

export const Search = (props: IconProps) => (
  <svg {...base} {...props}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="m20 20-3.6-3.6" />
  </svg>
);

export const Trace = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M4 18V8a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2Z" />
    <path d="M8 13h3M8 16h6" strokeWidth={1.2} />
  </svg>
);

export const Layers = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="m12 3 9 5-9 5-9-5 9-5Z" />
    <path d="m3 13 9 5 9-5" />
  </svg>
);

export const Bolt = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />
  </svg>
);

export const Arrow = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
);

export const Check = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="m4 12 5 5L20 6" />
  </svg>
);

export const Quote = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M7 7h4v6c0 2.2-1.8 4-4 4M13 7h4v6c0 2.2-1.8 4-4 4" />
  </svg>
);

export const Moon = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M20 14.5A8 8 0 0 1 9.5 4a7 7 0 1 0 10.5 10.5Z" />
    <path d="M17 3.5v3M15.5 5h3" strokeWidth={1.2} />
  </svg>
);

export const Sun = (props: IconProps) => (
  <svg {...base} {...props}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
  </svg>
);

export const Github = (props: IconProps) => (
  <svg {...base} {...props}>
    <path d="M9 19c-4 1.3-4-2-6-2.5M15 21v-3.4a3 3 0 0 0-.8-2.3c2.7-.3 5.5-1.3 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.3 4.3 0 0 0-.1-3.2s-1-.3-3.4 1.3a11.6 11.6 0 0 0-6 0C6.5 1 5.5 1.3 5.5 1.3a4.3 4.3 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 7.7c0 4.6 2.8 5.7 5.5 6a3 3 0 0 0-.8 2.3V21" />
  </svg>
);
