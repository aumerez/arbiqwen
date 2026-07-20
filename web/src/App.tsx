import { useState } from 'react';
import { LoginScreen } from './components/LoginScreen';
import { AuthenticatedApp } from './components/AuthenticatedApp';
import { clearToken, getToken, setToken } from './session';

// Root: an in-memory access token gates the app. With no token the sign-in
// screen renders; after sign-in the read-only workspace renders. Sign out
// clears the in-memory token and returns to sign-in. Nothing is persisted.
export default function App() {
  const [token, setTokenState] = useState<string | null>(getToken());
  // Held in memory only (like the token) so the top bar can show the signed-in
  // identity the way the desktop does; cleared on sign out.
  const [email, setEmail] = useState('');

  if (!token) {
    return (
      <LoginScreen
        onSuccess={(next, signedInEmail) => {
          setToken(next);
          setTokenState(next);
          setEmail(signedInEmail);
        }}
      />
    );
  }

  return (
    <AuthenticatedApp
      email={email}
      onLogout={() => {
        clearToken();
        setTokenState(null);
        setEmail('');
      }}
    />
  );
}
