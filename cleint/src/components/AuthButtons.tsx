import { Show, SignInButton, SignUpButton, UserButton } from "@clerk/react";
import type { ReactNode } from "react";
import { Arrow } from "./icons";

type Variant = "primary" | "secondary" | "ghost";
type Size = "md" | "lg";

const buttonClass = (variant: Variant, size: Size = "md") => {
  const base =
    "group inline-flex items-center justify-center gap-2 rounded-full font-medium tracking-tight whitespace-nowrap transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2 focus-visible:ring-offset-paper cursor-pointer disabled:opacity-50";
  const sizes: Record<Size, string> = {
    md: "h-10 px-5 text-sm",
    lg: "h-12 px-7 text-[0.95rem]",
  };
  const variants: Record<Variant, string> = {
    // starlight button: near-white on the void, glowing on hover
    primary:
      "bg-white text-[#050609] border border-white hover:-translate-y-0.5 active:translate-y-0 shadow-[0_0_0_1px_rgba(255,255,255,0.15)] hover:shadow-[0_12px_40px_-10px_rgba(255,255,255,0.45)]",
    // glass panel button
    secondary:
      "glass text-ink hover:border-white/40 hover:bg-white/[0.06] hover:-translate-y-0.5 active:translate-y-0",
    ghost:
      "bg-transparent text-ink border border-white/12 hover:border-white/35 hover:bg-white/[0.04] hover:-translate-y-0.5 active:translate-y-0",
  };
  return `${base} ${sizes[size]} ${variants[variant]}`;
};

export function SignUp({
  variant = "primary",
  size = "md",
  children,
  withArrow = false,
}: {
  variant?: Variant;
  size?: Size;
  children?: ReactNode;
  withArrow?: boolean;
}) {
  return (
    <SignUpButton mode="modal">
      <button className={buttonClass(variant, size)}>
        {children ?? "Sign Up"}
        {withArrow && (
          <Arrow className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
        )}
      </button>
    </SignUpButton>
  );
}

export function SignIn({
  variant = "secondary",
  size = "md",
  children,
}: {
  variant?: Variant;
  size?: Size;
  children?: ReactNode;
}) {
  return (
    <SignInButton mode="modal">
      <button className={buttonClass(variant, size)}>{children ?? "Sign In"}</button>
    </SignInButton>
  );
}

export function AuthCluster({ size = "md" }: { size?: Size }) {
  return (
    <Show
      when="signed-out"
      fallback={
        <div className="flex items-center gap-3">
          <span className="mono-label hidden sm:inline">Signed in</span>
          <UserButton />
        </div>
      }
    >
      <div className="flex items-center gap-2.5">
        <SignIn variant="ghost" size={size} />
        <SignUp variant="primary" size={size} />
      </div>
    </Show>
  );
}
