import { useEffect, useState } from "react";
import { Show, useAuth } from "@clerk/react";
import { setupInterceptor } from "./libs/api.ts";
import Nav from "./components/Nav.tsx";
import Hero from "./components/Hero.tsx";
import Footer from "./components/Footer.tsx";
import Workspace from "./chat/Workspace.tsx";

function LandingPage() {
  return (
    <div className="relative min-h-screen text-ink">
      {/* deep-space canvas + drifting starfield, fixed behind everything */}
      <div className="space-canvas" aria-hidden="true" />
      <div className="space-vignette" aria-hidden="true" />
      <div
        className="starfield starfield-bright starfield-drift pointer-events-none fixed inset-[-10%] -z-[1]"
        aria-hidden="true"
      />

      <Nav />
      <main>
        <Hero />
      </main>
      <Footer />
    </div>
  );
}

function App() {
  const { getToken, isSignedIn, isLoaded } = useAuth();
  // Gate the workspace until the auth interceptor is installed, so its
  // first API calls (list repos, etc.) always carry a bearer token.
  const [apiReady, setApiReady] = useState(false);

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    const cleanup = setupInterceptor(getToken);
    // Interceptor is live; allow the workspace to make authenticated calls.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setApiReady(true);
    return () => {
      cleanup();
      setApiReady(false);
    };
  }, [isLoaded, isSignedIn, getToken]);

  // Signed-in users go through: connect a repo -> watch it index -> chat.
  // Everyone else sees the marketing landing page.
  return (
    <Show when="signed-out" fallback={apiReady ? <Workspace /> : <BootScreen />}>
      <LandingPage />
    </Show>
  );
}

function BootScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-paper">
      <span className="h-6 w-6 animate-spin rounded-full border-2 border-white/15 border-t-white/70" />
    </div>
  );
}

export default App;
