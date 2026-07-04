import { useEffect } from "react";
import { Show, useAuth } from "@clerk/react";
import { setupInterceptor } from "./libs/api.ts";
import Nav from "./components/Nav.tsx";
import Hero from "./components/Hero.tsx";
import Footer from "./components/Footer.tsx";
import ChatPage from "./chat/ChatPage.tsx";

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

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) return;
    const cleanup = setupInterceptor(getToken);
    return cleanup;
  }, [isLoaded, isSignedIn, getToken]);

  // Signed-in users are dropped straight into the chat workspace;
  // everyone else sees the marketing landing page.
  return (
    <Show when="signed-out" fallback={<ChatPage />}>
      <LandingPage />
    </Show>
  );
}

export default App;
