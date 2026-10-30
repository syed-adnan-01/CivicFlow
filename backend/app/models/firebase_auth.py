"""
Firebase Authentication Integration Note:
QueueLess 2.3 delegates citizen phone OTP verification and session token refresh
to Firebase Authentication. No database tables are maintained for custom OTP challenges
or custom refresh tokens. See app.models.user and app.integrations.firebase_admin.
"""
