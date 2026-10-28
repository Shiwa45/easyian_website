"""
Fill the database with the starter content from the Easyian design.

    python manage.py seed_site            # creates anything that is missing
    python manage.py seed_site --reset    # wipes the starter models and re-creates them

Everything created here is editable afterwards in the admin.
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from blog.models import Category, Post, Tag
from core.models import (FAQ, Highlight, Industry, Integration, Page, PricingPlan, Service,
                         SiteSettings)

SERVICES = [
    dict(title="CRM Software", slug="crm-software", icon="chart", color="yellow",
         short_description="Pipelines, lead routing, follow-ups and reports that your sales floor actually opens every morning.",
         features="Lead capture from web, ads & portals\nRound-robin & load-based assignment\nFollow-up reminders & dispositions\nAgent and source performance reports",
         good_for="Sales & telecalling teams of any size", cta_label="Book a CRM demo",
         description="<p>A CRM shaped around how phone-first teams really work: leads come in, get assigned fairly, "
                     "are called, followed up and reported on — without spreadsheets in between.</p>"),
    dict(title="AI Agents", slug="ai-agents", icon="bot", color="teal",
         short_description="Voice and chat agents that qualify leads, answer FAQs, book callbacks and summarise every conversation.",
         features="Inbound & outbound voice calls\nWhatsApp & website chat\nCall transcripts & sentiment\nSuggested next steps per lead",
         good_for="High lead volume, repetitive queries", cta_label="See an AI agent live",
         description="<p>Voice and chat agents that answer, qualify and book — then drop a clean summary into the CRM "
                     "so your team picks up exactly where the agent left off.</p>"),
    dict(title="Website Development", slug="website-development", icon="monitor", color="sky",
         short_description="Fast, conversion-first websites and web apps — with lead forms that drop straight into your CRM.",
         features="Custom design & development\nLanding pages for ad campaigns\nLead forms synced to CRM\nHosting, SEO basics & upkeep",
         good_for="Brands that need leads, not just a homepage", cta_label="Start a website project",
         description="<p>Fast, mobile-first websites and web apps designed to convert visitors, with every form wired "
                     "into your CRM and dialer queues.</p>"),
    dict(title="Predictive Autodialer", slug="predictive-autodialer", icon="phone", color="coral",
         short_description="Dials ahead of your agents, filters out no-answers and busy tones, and hands over only live conversations.",
         features="Predictive, progressive & preview modes\nAnswer detection & smart retries\nDND filtering & call recording\nLive floor monitoring",
         good_for="Outbound floors with long call lists", cta_label="Book a dialer demo",
         description="<p>Our predictive autodialer dials ahead of your agents, filters no-answers, busy tones and "
                     "voicemail, and connects only live people — so more of the day is spent talking.</p>"),
    dict(title="VoIP Setup", slug="voip-setup", icon="wifi", color="peach",
         short_description="SIP trunks, IVR menus, call routing, queues and recording — configured, tested and looked after.",
         features="SIP trunk & number setup\nIVR menus & call routing\nQueues, ring groups & recording\nSoftphones & desk phone config",
         good_for="Offices moving off desk phones", cta_label="Plan my VoIP setup",
         description="<p>End-to-end business telephony: SIP trunks, numbers, IVR menus, queues and recording — "
                     "configured, tested and maintained by our team.</p>"),
    dict(title="DialSathi", slug="dialsathi", icon="mobile", color="mint",
         short_description="Our SIM-based mobile dialer CRM for telecalling teams — auto-dial queues right on Android.",
         features="Android auto-dial queues\nIndiaMART, Meta & Google Ads leads\nWhatsApp templates & recording\nGST billing, HRMS & AI add-ons",
         good_for="Telecalling teams using mobile SIMs", cta_label="Explore DialSathi",
         external_url="https://dialsathi.com"),
]

PAGES = [
    dict(key="home", eyebrow="SaaS · AI agents · Voice — built in India", heading="Your sales floor,",
         heading_highlight="on autopilot.",
         subheading="Easyian builds the software that dials, talks, tracks and sells — CRM, AI agents, predictive "
                    "dialers, VoIP and websites, all wired together so your team just closes.",
         primary_cta_label="Book a free demo", primary_cta_url="/about/#lead-form",
         secondary_cta_label="Explore services", secondary_cta_url="/services/",
         meta_title="Easyian — CRM, AI Agents, Predictive Dialer & VoIP in India",
         meta_description="Easyian builds SaaS CRM, AI voice & chat agents, predictive autodialers, VoIP setups and "
                          "websites for Indian sales and telecalling teams."),
    dict(key="services", eyebrow="Services", heading="Pick a layer. Or stack them all.",
         subheading="Every Easyian service works alone — and clicks into the others. Start with a CRM, add AI agents "
                    "next quarter, switch on the predictive dialer when your floor grows.",
         meta_title="Services — CRM, AI Agents, Dialer, VoIP & Websites",
         meta_description="Explore Easyian services: SaaS CRM, AI voice and chat agents, predictive autodialer, "
                          "VoIP setup and website development."),
    dict(key="dialsathi", eyebrow="An Easyian product · Made in India", heading="DialSathi —",
         heading_highlight="your team’s calling buddy.",
         subheading="A SIM-based mobile dialer CRM for Indian telecalling teams. Leads arrive from every source, the "
                    "Android app auto-dials them in turn, and every call, recording and WhatsApp follow-up lands on the lead.",
         primary_cta_label="Book a free demo", primary_cta_url="#lead-form",
         secondary_cta_label="See pricing", secondary_cta_url="#pricing",
         meta_title="DialSathi — Mobile SIM Dialer CRM for Telecalling Teams",
         meta_description="DialSathi is a SIM-based Android auto-dialer CRM with lead intake, call recording, "
                          "WhatsApp follow-up and GST billing. Plans from ₹12,999/year."),
    dict(key="about", eyebrow="About Easyian", heading="We make complicated sales tech feel easy.",
         subheading="Easyian Tech OPC Private Limited is an Indian software company building SaaS CRM, AI agents, "
                    "predictive dialers, VoIP systems and websites — plus DialSathi, our mobile dialer CRM.",
         meta_title="About Easyian & Contact — Book a Demo",
         meta_description="Meet Easyian Tech OPC Private Limited and book a free demo of our CRM, AI agents, "
                          "predictive dialer and VoIP solutions."),
    dict(key="blog", heading="The Easyian Blog",
         subheading="Guides on CRM, predictive dialers, AI agents and running a better sales floor.",
         meta_title="Blog — CRM, Dialer & AI Agent Guides",
         meta_description="Practical guides on CRM, predictive dialers, AI agents, VoIP and telecalling for Indian sales teams."),
]

HIGHLIGHTS = {
    "home_flow": [
        ("Lead lands", "From your website, ads or portals into the CRM.", "sky"),
        ("AI qualifies", "An AI agent calls or chats and scores intent.", "teal"),
        ("Dialer connects", "Hot leads go to agents over your VoIP lines.", "coral"),
        ("CRM tracks", "Recording, notes and follow-ups saved to the lead.", "yellow"),
        ("Deal won", "Reports show who closed, what worked, what’s next.", "mint"),
    ],
    "home_ai": [
        ("Inbound & outbound voice calls", "", "teal"),
        ("WhatsApp & website chat", "", "yellow"),
        ("Transcripts, sentiment & next steps in your CRM", "", "coral"),
    ],
    "home_why": [
        ("Software + telephony, one team", "No juggling a CRM vendor, a dialer vendor and a telecom vendor. We do all three.", "coral"),
        ("Made for Indian sales floors", "GST invoicing, DND checks, lakh & crore — built in, not bolted on.", "yellow"),
        ("AI where it saves time", "Summaries, sentiment and next steps on every call — so managers coach, not chase.", "teal"),
    ],
    "process": [
        ("Discover", "We map your leads, calls and team roles — what works today and what leaks.", "yellow"),
        ("Configure", "CRM fields, dialer campaigns, VoIP lines and AI scripts set up for your flow.", "sky"),
        ("Launch", "Agents trained, data imported, first calls dialled — together.", "teal"),
        ("Grow", "Ongoing support, new modules and reports as your floor scales.", "coral"),
    ],
    "about_values": [
        ("Easy first", "If an agent needs a manual to make a call, we haven’t finished the job.", "coral"),
        ("Whole stack", "Software, telephony and AI from one team — one number to call when something breaks.", "teal"),
        ("Built in India", "GST, DND rules, regional languages and lakh-crore numbers come standard.", "sky"),
    ],
    "dialsathi_features": [
        ("Lead intake", "IndiaMART, Meta Lead Ads, Click-to-WhatsApp, Google Ads, your website and webhooks — one named batch per source per day, duplicates removed.", "yellow"),
        ("Fair lead distribution", "Round robin, equal split or least loaded, with optional per-agent caps. Overflow stays unassigned and is reported.", "sky"),
        ("Android auto-dialer", "Start a queue once and the app dials each lead in turn. Filter by status, source, tags or follow-ups due; DND numbers are skipped.", "teal"),
        ("Click-to-call & recording", "Calls via Exotel, MCUBE, Knowlarity or the agent’s own SIM — timed, recorded and attached to the lead.", "coral"),
        ("WhatsApp follow-up", "Approved templates to one lead or a filtered list via Interakt, AiSensy, Wati or Gupshup — with delivery and read status.", "mint"),
        ("Reports & live floor", "Agent performance, lead sources, call analytics, conversion funnel and a live view of who’s on a call.", "peach"),
    ],
    "dialsathi_addons": [
        ("AI Suite", "Transcripts, call summaries, mood and suggested next steps for each call.", "teal"),
        ("Sales & Billing", "Quotation → sales order → GST invoice, receivables ageing and Tally export.", "yellow"),
        ("HRMS", "Attendance from dialer sessions, leave, expenses, incentives and payroll.", "sky"),
        ("Recruitment", "Jobs, candidates, interviews, scorecards and offers that become employees.", "coral"),
    ],
    "dialsathi_points": [
        ("Auto-dial queues on Android", "", "teal"),
        ("IndiaMART, Meta & Google Ads leads", "", "yellow"),
        ("Call recording & WhatsApp templates", "", "coral"),
        ("GST billing, HRMS & AI add-ons", "", "sky"),
    ],
}
ICONS = {"dialsathi_features": ["users", "spark", "mobile", "phone", "mail", "chart"],
         "dialsathi_addons": ["bot", "rupee", "users", "spark"],
         "about_values": ["spark", "shield", "pin"]}

PLANS = [
    dict(name="Growth", price="₹12,999", period="/year", users_label="Up to 10 users", cta_label="Start with Growth", order=1),
    dict(name="Enterprise", price="₹17,999", period="/year", users_label="Up to 20 users", cta_label="Go Enterprise",
         is_highlighted=True, order=2),
]
INTEGRATIONS = ["IndiaMART", "Meta Ads", "Google Ads", "WhatsApp", "Exotel", "MCUBE", "Knowlarity", "Interakt",
                "AiSensy", "Wati", "Gupshup", "MSG91", "Razorpay", "Tally"]
INDUSTRIES = ["Real estate", "Education & admissions", "Loans & insurance", "B2B on IndiaMART"]

FAQS = [
    ("home", "What does Easyian do?", "We build and set up SaaS CRM, AI voice and chat agents, predictive autodialers, VoIP telephony and websites for teams that sell by phone — plus DialSathi, our mobile dialer CRM."),
    ("home", "Can I start with just one service?", "Yes. Each service works on its own and connects to the others when you’re ready."),
    ("home", "How do I get a demo?", "Fill in the form on our contact page and our team will call you back to schedule a walkthrough."),
    ("dialsathi", "Is the DialSathi app available on iPhone?", "The agent app is Android-only. Managers use the web dashboard from any device."),
    ("dialsathi", "Do the prices include GST?", "No — plan prices exclude GST."),
    ("dialsathi", "What if my team has more than 20 users?", "We offer custom plans for larger floors. Ask us through the demo form."),
]

POSTS = [
    dict(title="Predictive vs progressive vs preview dialing: which mode fits your team?",
         category="Dialers", tags=["predictive dialer", "telecalling"],
         excerpt="A plain-English guide to the three main auto-dialer modes and when each one makes sense.",
         content="<p>Auto-dialers save agents from typing numbers, but not every mode suits every team. Here’s how the three common modes differ.</p>"
                 "<h2>Preview dialing</h2><p>The agent sees the lead’s details first and clicks to call. It’s slower, but ideal for high-value or complex conversations.</p>"
                 "<h2>Progressive dialing</h2><p>The dialer calls the next lead as soon as an agent becomes free. One line per agent, no abandoned calls.</p>"
                 "<h2>Predictive dialing</h2><p>The dialer calls several numbers per available agent, predicting how many will answer, and passes only live calls through. Best for large lists and outbound floors focused on talk time.</p>"
                 "<h2>How to choose</h2><ul><li>Small list, high-value leads → preview</li><li>Steady list, compliance-sensitive → progressive</li><li>Big list, many agents → predictive</li></ul>"),
    dict(title="Why your telecalling team should move from Excel to a CRM",
         category="CRM", tags=["crm", "telecalling"],
         excerpt="Spreadsheets work until leads start slipping. Here are the signs it’s time for a calling CRM.",
         content="<p>Most teams start with a shared spreadsheet. It works — until it doesn’t.</p>"
                 "<h2>Signs you’ve outgrown Excel</h2><ul><li>Two agents call the same lead</li><li>Follow-ups are forgotten</li><li>Nobody knows which lead source converts</li></ul>"
                 "<h2>What a calling CRM changes</h2><p>Leads are assigned automatically, every call and recording is saved to the lead, and reminders surface follow-ups on time. Managers finally see agent and source performance without building reports by hand.</p>"),
]


class Command(BaseCommand):
    help = "Create starter website content (services, pages, highlights, pricing, FAQs, sample blog posts)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete starter content first and re-create it.")
        parser.add_argument("--no-posts", action="store_true", help="Skip the sample blog posts.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            for model in (Service, Page, Highlight, PricingPlan, Integration, Industry, FAQ):
                model.objects.all().delete()

        site = SiteSettings.load()
        site.save()

        for i, data in enumerate(SERVICES):
            Service.objects.get_or_create(slug=data["slug"], defaults={**data, "order": i})
        for data in PAGES:
            Page.objects.get_or_create(key=data["key"], defaults=data)
        for section, rows in HIGHLIGHTS.items():
            if Highlight.objects.filter(section=section).exists():
                continue
            icons = ICONS.get(section, [])
            for i, (title, text, color) in enumerate(rows):
                Highlight.objects.create(section=section, title=title, text=text, color=color, order=i,
                                         icon=icons[i] if i < len(icons) else "")
        if not PricingPlan.objects.exists():
            for data in PLANS:
                PricingPlan.objects.create(**data)
        if not Integration.objects.exists():
            for i, name in enumerate(INTEGRATIONS):
                Integration.objects.create(name=name, order=i)
        if not Industry.objects.exists():
            for i, name in enumerate(INDUSTRIES):
                Industry.objects.create(name=name, order=i)
        if not FAQ.objects.exists():
            for i, (page, q, a) in enumerate(FAQS):
                FAQ.objects.create(page=page, question=q, answer=a, order=i)

        if not opts["no_posts"] and not Post.objects.exists():
            for i, data in enumerate(POSTS):
                cat, _ = Category.objects.get_or_create(name=data["category"])
                post = Post.objects.create(
                    title=data["title"], excerpt=data["excerpt"], content=data["content"], category=cat,
                    status=Post.Status.PUBLISHED, is_featured=(i == 0),
                    published_at=timezone.now() - timezone.timedelta(days=i * 3),
                )
                for name in data["tags"]:
                    tag, _ = Tag.objects.get_or_create(name=name)
                    post.tags.add(tag)
            for name in ("AI Agents", "VoIP"):
                Category.objects.get_or_create(name=name)

        self._og_image()
        self.stdout.write(self.style.SUCCESS("Starter content ready. Edit everything at /admin/."))

    def _og_image(self):
        """Create a default 1200×630 share image if it doesn't exist."""
        target = Path(settings.BASE_DIR) / "static" / "img" / "og-default.png"
        if target.exists():
            return
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            return
        img = Image.new("RGB", (1200, 630), "#FFF3E6")
        d = ImageDraw.Draw(img)
        d.ellipse((760, 90, 1180, 510), fill="#FFD8B8")
        d.rounded_rectangle((860, 190, 1080, 410), radius=48, fill="#FF7A59")
        d.rounded_rectangle((80, 80, 180, 180), radius=30, fill="#FF7A59")
        try:
            big = ImageFont.truetype("DejaVuSans-Bold.ttf", 76)
            mid = ImageFont.truetype("DejaVuSans.ttf", 34)
        except OSError:
            big = mid = ImageFont.load_default()
        d.text((210, 92), "Easyian", fill="#1F2B3D", font=big)
        d.text((80, 260), "CRM · AI Agents · Predictive Dialer", fill="#1F2B3D", font=mid)
        d.text((80, 315), "VoIP · Websites · DialSathi", fill="#1F2B3D", font=mid)
        d.text((80, 470), "Built in India", fill="#C4401F", font=mid)
        img.save(target)
