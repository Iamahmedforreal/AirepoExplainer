import { useEffect } from "react";
import { useAuth } from "@clerk/react";
import { setupInterceptor } from "./libs/api.ts";
import Nav from "./components/Nav";
import Hero from "./components/Hero";
import Features from "./components/Features";
import CodeGraphExample from "./components/CodeGraphExample";
import HowItWorks from "./components/HowItWorks";
import Audience from "./components/Audience";
import WhyCodeGrok from "./components/WhyCodeGrok";
import CTA from "./components/CTA";
import Footer from "./components/Footer";

function App() {
  const { getToken, isSignedIn, isLoaded } = useAuth();

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) return;
    const cleanup = setupInterceptor(getToken);
    return cleanup;
  }, [isLoaded, isSignedIn, getToken]);

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
        <Features />
        <CodeGraphExample />
        <HowItWorks />
        <Audience />
        <WhyCodeGrok />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}

export default App;
