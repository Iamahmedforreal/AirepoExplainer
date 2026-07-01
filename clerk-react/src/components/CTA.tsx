import { SignUp, SignIn } from "./AuthButtons";

export default function CTA() {
  return (
    <section className="grain relative overflow-hidden border-t border-white/5 px-6 py-28 sm:px-10 md:py-36">
      <div className="starfield pointer-events-none absolute inset-0" />
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(60% 70% at 50% 50%, rgba(255,255,255,0.06), transparent 70%)",
        }}
      />

      <div className="glass-strong relative mx-auto flex max-w-2xl flex-col items-center rounded-3xl px-8 py-14 text-center shadow-[0_50px_120px_-60px_rgba(0,0,0,0.9)] sm:px-14">
        <span className="mono-label mb-6">Understand any codebase in minutes</span>

        <h2 className="text-balance text-4xl sm:text-5xl">
          Stop reading code.
          <br />
          Start understanding it.
        </h2>

        <p className="mt-6 max-w-lg text-balance text-lg text-muted">
          Create an account, paste a GitHub URL, and CodeGrok maps the whole
          repository — then you chat with it to learn how anything works.
        </p>

        <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
          <SignUp variant="primary" size="lg" withArrow>
            Create account
          </SignUp>
          <SignIn variant="ghost" size="lg">
            Sign in
          </SignIn>
        </div>
      </div>
    </section>
  );
}
