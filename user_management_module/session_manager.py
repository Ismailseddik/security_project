import time

# Time (in seconds) after which the session is considered expired due to inactivity
SESSION_TIMEOUT = 600  # 10 minutes

class Session:
    def __init__(self, username):
        self.username = username
        self.login_time = time.time()
        self.last_active = time.time()

    def update_activity(self):
        """Call this whenever the user performs an action."""
        self.last_active = time.time()

    def is_expired(self):
        """Returns True if the session has been inactive for too long."""
        return (time.time() - self.last_active) > SESSION_TIMEOUT

    def logout(self):
        """Logs the session out explicitly (manual logout)."""
        print(f"[!] User '{self.username}' has been logged out.")
        return True

    def get_duration(self):
        """Returns how long the session has been active (in seconds)."""
        return int(time.time() - self.login_time)

    def __str__(self):
        return f"Session(username={self.username}, active_for={self.get_duration()}s)"
