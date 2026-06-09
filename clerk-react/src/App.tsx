import { useEffect } from "react";
import { useAuth } from "@clerk/react";
import { setupInterceptor } from "./libs/api.ts";
import Nav from "./components/Nav";
import Hero from "./components/Hero";
import WhatIs from "./components/WhatIs";
import HowItWorks from "./components/HowItWorks";
import AgentSystem from "./components/AgentSystem";
import WhyCodeGrok from "./components/WhyCodeGrok";
import ExampleQuestions from "./components/ExampleQuestions";
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
    <div className="min-h-screen bg-paper text-ink">
      <Nav />
      <main>
        <Hero />
        <WhatIs />
        <HowItWorks />
        <AgentSystem />
        <WhyCodeGrok />
        <ExampleQuestions />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}

export default App;
