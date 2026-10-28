import hashlib
import time
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from core.models import Service

from . import antispam
from .models import BlockedSubmission, Lead


def solve(challenge):
    n = 0
    while True:
        if hashlib.sha256(f"{challenge}:{n}".encode()).hexdigest().startswith("0" * antispam.POW_DIFFICULTY):
            return str(n)
        n += 1


@override_settings(LEAD_MIN_SUBMIT_SECONDS=3)
class LeadFormTests(TestCase):
    def setUp(self):
        cache.clear()
        Service.objects.create(title="CRM Software", slug="crm-software", short_description="x")

    def payload(self, **extra):
        # pretend the form was rendered 10 seconds ago
        with mock.patch("leads.antispam.time.time", return_value=time.time() - 10):
            challenge = antispam.new_challenge()
        data = {"name": "Ravi Kumar", "phone": "+91 98765 43210", "email": "ravi@example.com",
                "company": "Acme", "interests": ["crm-software"], "message": "Need a CRM",
                "challenge": challenge, "pow": solve(challenge), "source_page": "/about/",
                "website": "", "fax_number": ""}
        data.update(extra)
        return data

    def post(self, data, ajax=True):
        headers = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"} if ajax else {}
        return self.client.post("/lead/submit/", data, **headers)

    def test_valid_lead_is_saved(self):
        r = self.post(self.payload())
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.json()["ok"])
        lead = Lead.objects.get()
        self.assertEqual(lead.interests, "crm-software")
        self.assertEqual(lead.source_page, "/about/")

    def test_honeypot_blocked_silently(self):
        r = self.post(self.payload(website="http://spam.example"))
        self.assertTrue(r.json()["ok"])  # bot sees success
        self.assertEqual(Lead.objects.count(), 0)
        self.assertEqual(BlockedSubmission.objects.get().reason, "honeypot")

    def test_missing_proof_of_work_blocked(self):
        r = self.post(self.payload(pow=""))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)
        self.assertEqual(BlockedSubmission.objects.get().reason, "no-proof-of-work")

    def test_too_fast_blocked(self):
        challenge = antispam.new_challenge()  # rendered "now"
        r = self.post(self.payload(challenge=challenge, pow=solve(challenge)))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(BlockedSubmission.objects.get().reason, "too-fast")

    def test_tampered_challenge_blocked(self):
        data = self.payload()
        data["challenge"] = data["challenge"][:-2] + "xx"
        r = self.post(data)
        self.assertEqual(BlockedSubmission.objects.get().reason, "bad-signature")

    def test_replay_blocked(self):
        data = self.payload()
        self.post(data)
        self.post(data)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(BlockedSubmission.objects.get().reason, "replayed")

    def test_link_spam_blocked(self):
        r = self.post(self.payload(message="http://a.com http://b.com www.c.com"))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Lead.objects.count(), 0)

    @override_settings(LEAD_RATE_LIMIT_PER_HOUR=2)
    def test_rate_limit(self):
        for _ in range(3):
            self.post(self.payload())
        self.assertEqual(Lead.objects.count(), 2)
        self.assertEqual(BlockedSubmission.objects.get().reason, "rate-limited")

    def test_invalid_phone_returns_errors(self):
        r = self.post(self.payload(phone="123"))
        self.assertEqual(r.status_code, 400)
        self.assertIn("phone", r.json()["errors"])
        self.assertIn("challenge", r.json())

    def test_non_ajax_success_redirects(self):
        r = self.post(self.payload(), ajax=False)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r["Location"].startswith("/about/"))
