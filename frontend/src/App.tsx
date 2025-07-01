import React, { useState, useEffect } from "react";

interface User {
  id: string;
  email: string;
  name: string;
  picture: string;
}

interface OAuthMessage {
  type: "OAUTH_SUCCESS";
  user: User;
}

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    // Listen for OAuth callback messages
    const handleMessage = (event: MessageEvent<OAuthMessage>) => {
      if (event.origin !== "http://localhost:8000") return;

      if (event.data.type === "OAUTH_SUCCESS") {
        setUser(event.data.user);
        setLoading(false);
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const handleLogin = async (): Promise<void> => {
    setLoading(true);

    try {
      // Get the auth URL from backend
      const response = await fetch("http://localhost:8000/auth/google/login");
      const data = await response.json();

      // Open popup window for OAuth
      const popup = window.open(
        data.auth_url,
        "oauth",
        "width=500,height=600,scrollbars=yes,resizable=yes"
      );

      // Check if popup was closed without completing OAuth
      const checkClosed = setInterval(() => {
        if (popup && popup.closed) {
          clearInterval(checkClosed);
          setLoading(false);
        }
      }, 1000);
    } catch (error: unknown) {
      console.error("Login error:", error);
      setLoading(false);
    }
  };

  const handleLogout = (): void => {
    setUser(null);
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>OAuth Demo App</h1>

      {!user ? (
        <div>
          <h2>Please log in</h2>
          <button onClick={handleLogin} disabled={loading}>
            {loading ? "Logging in..." : "Login with Google"}
          </button>
        </div>
      ) : (
        <div>
          <h2>Welcome!</h2>
          <div
            style={{
              border: "1px solid #ccc",
              padding: "15px",
              margin: "10px 0",
            }}
          >
            <h3>User Profile</h3>
            <p>
              <strong>Name:</strong> {user.name}
            </p>
            <p>
              <strong>Email:</strong> {user.email}
            </p>
            <p>
              <strong>ID:</strong> {user.id}
            </p>
            {user.picture && (
              <div>
                <strong>Profile Picture:</strong>
                <br />
                <img src={user.picture} alt="Profile" width="50" height="50" />
              </div>
            )}
          </div>
          <button onClick={handleLogout}>Logout</button>
        </div>
      )}
    </div>
  );
}

export default App;
