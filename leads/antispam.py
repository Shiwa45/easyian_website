"""
Invisible ("hidden") captcha for the lead form. No puzzles for real visitors — several
silent checks that bots fail:

1. Honeypot   – a field hidden from humans; bots that fill every input reveal themselves.
2. Time trap  – the form carries a signed timestamp; posts faster than a human can type
                (or replayed hours later) are rejected.
3. Proof of work – the browser must solve a small SHA-256 puzzle tied to a signed, one-time
                challenge. It only starts after a real interaction (focus / key / touch) and
                takes a fraction of a second. Scripts that just POST the form can't pass it.
4. One-time challenge – each challenge can be used once (replay protection).
5. Rate limit – max N submissions per IP per hour.
6. Link filter – messages stuffed with links are rejected.
7. Optional Cloudflare Turnstile (invisible) when TURNSTILE_* keys are set.
"""
import hashlib
import json
import secrets
import time
import urllib.parse
import urllib.request

from django.conf import settings
from django.core import signing
from django.core.cache import cache

SALT = "easyian.leads.challenge"
POW_DIFFICULTY = 3  # number of leading hex zeros → ~4,096 hashes on average (≈0.1–0.4 s in a browser)


class SpamDetected(Exception):
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def new_challenge():
    """Signed token containing a random nonce and the time the form was rendered."""
    nonce = secrets.token_hex(12)
    return signing.dumps({"n": nonce, "t": int(time.time())}, salt=SALT, compress=False)


def _decode(token):
    try:
        data = signing.loads(token, salt=SALT, max_age=settings.LEAD_MAX_FORM_AGE_SECONDS)
    except signing.SignatureExpired:
        raise SpamDetected("expired-form")
    except signing.BadSignature:
        raise SpamDetected("bad-signature")
    return data


def verify_pow(challenge, solution):
    if not solution or not str(solution).isdigit() or len(str(solution)) > 12:
        return False
    digest = hashlib.sha256(f"{challenge}:{solution}".encode()).hexdigest()
    return digest.startswith("0" * POW_DIFFICULTY)


def verify_turnstile(token, ip):
    if not settings.TURNSTILE_SECRET_KEY:
        return True
    if not token:
        return False
    body = urllib.parse.urlencode({
        "secret": settings.TURNSTILE_SECRET_KEY, "response": token, "remoteip": ip or "",
    }).encode()
    try:
        req = urllib.request.Request("https://challenges.cloudflare.com/turnstile/v0/siteverify", data=body)
        with urllib.request.urlopen(req, timeout=6) as resp:
            return bool(json.loads(resp.read().decode()).get("success"))
    except Exception:
        # If Cloudflare is unreachable, don't lose a genuine lead: the other checks still apply.
        return True


def check_rate_limit(ip):
    if not ip:
        return
    key = f"lead-rate:{ip}"
    count = cache.get(key, 0)
    if count >= settings.LEAD_RATE_LIMIT_PER_HOUR:
        raise SpamDetected("rate-limited")
    cache.set(key, count + 1, 60 * 60)


def run_checks(request, data):
    """Raise SpamDetected(reason) if the submission looks automated."""
    if data.get("website") or data.get("fax_number"):
        raise SpamDetected("honeypot")

    challenge = data.get("challenge", "")
    payload = _decode(challenge)
    age = time.time() - payload.get("t", 0)
    if age < settings.LEAD_MIN_SUBMIT_SECONDS:
        raise SpamDetected("too-fast")

    if not verify_pow(challenge, data.get("pow", "")):
        raise SpamDetected("no-proof-of-work")

    used_key = f"lead-used:{payload.get('n')}"
    if not cache.add(used_key, 1, settings.LEAD_MAX_FORM_AGE_SECONDS):
        raise SpamDetected("replayed")

    ip = client_ip(request)
    if not verify_turnstile(data.get("cf-turnstile-response", ""), ip):
        raise SpamDetected("turnstile-failed")

    message = data.get("message", "") or ""
    links = message.lower().count("http://") + message.lower().count("https://") + message.lower().count("www.")
    if links > settings.LEAD_MAX_LINKS_IN_MESSAGE:
        raise SpamDetected("too-many-links")

    check_rate_limit(ip)
