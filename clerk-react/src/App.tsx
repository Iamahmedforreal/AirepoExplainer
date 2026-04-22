import './App.css'
import { Show, SignInButton, SignUpButton, UserButton , useAuth ,  } from '@clerk/react'
import { useEffect } from "react";
import { setupInterceptor } from "./libs/api.ts";



function App() {
  const { getToken, isSignedIn, isLoaded } = useAuth();
  

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) return;

    const cleanup = setupInterceptor(getToken);
    return cleanup;

  }, [isLoaded, isSignedIn, getToken]);

  
  return (
    <>
      <header>
        <Show when="signed-out">
          <SignInButton />
          <SignUpButton />
        </Show>
        <Show when="signed-in">
          <UserButton />
        </Show>
      </header>
    </>
  )
}

export default App