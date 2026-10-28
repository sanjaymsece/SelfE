from datetime import date, datetime, time, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction

from apps.accounts.models import User, UserPreference
from apps.analytics.models import PostInsight
from apps.comment_intelligence.models import Comment
from apps.social_accounts.models import Post, SocialAccount
from apps.workspaces.models import MembershipRole, Workspace, WorkspaceMembership

# ---------------------------------------------------------------------------
# Deterministic demo definitions. All metrics are simulated; no Meta API is
# contacted. Slot weights create repeatable performance patterns by weekday/hour.
# ---------------------------------------------------------------------------

DEMO_USERS = [
    {
        "email": "maya@example.com",
        "full_name": "Maya Chen",
        "workspace_name": "Green Fork Kitchen",
        "workspace_slug": "green-fork-kitchen",
        "niche": "plant-based cooking and sustainable eating",
        "timezone": "America/New_York",
        "goals": [
            "Grow a loyal community of home cooks",
            "Increase saves on practical recipe posts",
            "Turn weekly viewers into newsletter subscribers",
        ],
        "preferred_language": "en",
        "tone": "warm and practical",
        "content_style": "educational",
        "target_audience": "busy home cooks who want affordable plant-based meals",
        "keywords": ["meal prep", "pantry staples", "budget cooking", "seasonal produce"],
        "slot_weights": {
            (6, 10): 1.80,  # Sunday 10:00
            (2, 18): 1.55,  # Wednesday 18:00
            (5, 9): 1.35,   # Saturday 09:00
            (1, 12): 1.15,  # Tuesday 12:00
        },
        "accounts": [
            {
                "platform": "instagram",
                "handle": "@greenforkkitchen",
                "display_name": "Green Fork Kitchen",
                "follower_count": 48200,
            },
            {
                "platform": "tiktok",
                "handle": "@greenforkkitchen",
                "display_name": "Green Fork Kitchen",
                "follower_count": 22750,
            },
        ],
        "posts": [
            ("gfk-01", 0, 6, 10, 1, "reel", "Crispy chickpeas three ways — the snack that disappears before dinner."),
            ("gfk-02", 1, 6, 10, 2, "carousel", "A week of plant-based lunches for under $35. Save this grocery list."),
            ("gfk-03", 0, 6, 10, 3, "reel", "The 15-minute miso noodles I make when the fridge looks empty."),
            ("gfk-04", 1, 2, 18, 1, "carousel", "Five pantry swaps that quietly cut your grocery bill."),
            ("gfk-05", 0, 2, 18, 2, "reel", "Tofu skeptics: try this sesame crust before you decide."),
            ("gfk-06", 1, 2, 18, 3, "image", "A colourful bowl is not a personality. But this one is close."),
            ("gfk-07", 0, 5, 9, 2, "reel", "Farmers market haul + what I actually cook with it."),
            ("gfk-08", 1, 5, 9, 4, "carousel", "Freezer-friendly breakfasts for chaotic mornings."),
            ("gfk-09", 0, 1, 12, 1, "image", "Lunch prep shortcut: roast once, eat three different ways."),
            ("gfk-10", 1, 1, 12, 3, "reel", "The tahini dressing ratio I wish I knew sooner."),
            ("gfk-11", 0, 3, 20, 2, "carousel", "Six seasonal vegetables that are cheaper right now."),
            ("gfk-12", 1, 0, 8, 4, "image", "Monday reset: a five-ingredient soup that feels like a hug."),
            ("gfk-13", 0, 4, 17, 6, "reel", "What I eat in a day when I have zero cooking energy."),
            ("gfk-14", 1, 0, 8, 10, "carousel", "The beginner's plant-based pantry, without the expensive extras."),
            ("gfk-15", 0, 2, 18, 16, "reel", "One-pot coconut lentils — cheap, cozy, and freezer-friendly."),
            ("gfk-16", 1, 6, 10, 20, "carousel", "Readers asked for easy breakfasts. Here are five."),
        ],
        "comments": [
            ("gfk-c01", "gfk-01", "sofia.cooks", "What brand of tahini do you use? Mine always turns out bitter.", 2, 12, 14),
            ("gfk-c02", "gfk-01", "plantedbythesea", "This is the third recipe of yours I've saved this week. The crispy chickpeas worked!", 1, 9, 6),
            ("gfk-c03", "gfk-02", "budgetbowls", "I run a small weekly meal-prep newsletter. Would you be open to collaborating on a budget lunch feature?", 1, 18, 3),
            ("gfk-c04", "gfk-02", "marcus.eats", "The grocery list link is broken for me — can you re-share it?", 1, 8, 16),
            ("gfk-c05", "gfk-04", "tinykitchennotes", "The swaps are helpful, but the text on slide 3 is hard to read on my phone.", 2, 7, 11),
            ("gfk-c06", "gfk-04", "elena.grows", "I tried the chickpea pasta swap and my kids did not notice. Huge win.", 1, 10, 2),
            ("gfk-c07", "gfk-05", "tofuquestion", "How do you get the crust to stay crispy after adding the sauce?", 1, 13, 9),
            ("gfk-c08", "gfk-06", "rainydayramen", "This colour palette is everything. What camera do you use?", 1, 5, 4),
            ("gfk-c09", "gfk-07", "localharvestco", "We're a local farm co-op and would love to host a collab at the market. Check your DMs!", 2, 20, 1),
            ("gfk-c10", "gfk-09", "mealprepmaya", "Could you share a printable version of this plan?", 1, 6, 8),
            ("gfk-c11", "gfk-11", "greenishthumb", "My kale always goes slimy before Friday. Any storage tips?", 1, 11, 7),
            ("gfk-c12", "gfk-12", "notacookyet", "Made this tonight and it was so easy. Thank you for keeping it simple.", 1, 4, 5),
            ("gfk-c13", "gfk-13", "dailybite", "Honestly this felt like an ad and not like your usual recipes.", 2, 3, 15),
            ("gfk-c14", "gfk-14", "spammy_deals", "🔥🔥 FREE GROWTH — DM us for 10k followers instantly!!", 1, 1, 2),
        ],
    },
    {
        "email": "arjun@example.com",
        "full_name": "Arjun Patel",
        "workspace_name": "Momentum Fitness",
        "workspace_slug": "momentum-fitness",
        "niche": "strength training for busy professionals",
        "timezone": "Asia/Kolkata",
        "goals": [
            "Book more one-to-one coaching calls",
            "Build trust with beginner lifters",
            "Increase shares of form-focused Reels",
        ],
        "preferred_language": "en",
        "tone": "direct and encouraging",
        "content_style": "coaching",
        "target_audience": "desk-based professionals who want to get stronger in 3 sessions a week",
        "keywords": ["strength training", "busy professionals", "beginner lifting", "recovery"],
        "slot_weights": {
            (1, 6): 1.80,   # Tuesday 06:00
            (3, 6): 1.65,   # Thursday 06:00
            (6, 19): 1.40,  # Sunday 19:00
            (0, 7): 1.20,   # Monday 07:00
        },
        "accounts": [
            {
                "platform": "instagram",
                "handle": "@momentumfit",
                "display_name": "Momentum Fitness",
                "follower_count": 63100,
            },
            {
                "platform": "tiktok",
                "handle": "@momentumfit",
                "display_name": "Momentum Fitness",
                "follower_count": 31500,
            },
        ],
        "posts": [
            ("mf-01", 0, 1, 6, 1, "reel", "Three lifts, three sessions, zero guesswork. Start here."),
            ("mf-02", 1, 1, 6, 2, "carousel", "Your warm-up is not optional. Here is the five-minute version."),
            ("mf-03", 0, 1, 6, 3, "reel", "Stop chasing soreness. Chase repeatable reps."),
            ("mf-04", 1, 3, 6, 1, "reel", "The desk-worker deadlift checklist I use with every client."),
            ("mf-05", 0, 3, 6, 2, "carousel", "Three recovery habits that beat another rest day."),
            ("mf-06", 1, 3, 6, 3, "image", "Consistency is quieter than motivation. That is the point."),
            ("mf-07", 0, 6, 19, 1, "reel", "Sunday reset: plan three workouts in under ten minutes."),
            ("mf-08", 1, 6, 19, 3, "carousel", "Your first month of strength training, mapped out."),
            ("mf-09", 0, 0, 7, 2, "reel", "If your lower back hurts during rows, check this setup."),
            ("mf-10", 1, 0, 7, 4, "image", "A short workout still counts. Ten focused minutes."),
            ("mf-11", 0, 2, 12, 2, "carousel", "Progressive overload without living in the gym."),
            ("mf-12", 1, 4, 18, 4, "reel", "The one gym habit that changed my energy at work."),
            ("mf-13", 0, 5, 8, 6, "image", "Rest days are part of the plan, not a break from it."),
            ("mf-14", 1, 1, 6, 10, "carousel", "Beginner questions I answer every single week."),
            ("mf-15", 0, 3, 6, 16, "reel", "Three common squat mistakes — and the cue that fixes them."),
            ("mf-16", 1, 1, 6, 20, "carousel", "A realistic strength plan for a packed calendar."),
        ],
        "comments": [
            ("mf-c01", "mf-01", "liftwithlea", "How many days a week should I run this if I also play football twice a week?", 1, 12, 10),
            ("mf-c02", "mf-01", "corporatecam", "Started the three-session plan this month. My knee pain is finally settling down.", 1, 10, 4),
            ("mf-c03", "mf-02", "physio_sam", "I'm a sports physio and would love to collaborate on a desk-posture series. Open to a call?", 2, 16, 2),
            ("mf-c04", "mf-02", "newdadlifts", "The video is good but I can't see the foot position from this angle.", 2, 7, 11),
            ("mf-c05", "mf-04", "maya.runs", "Do you coach people remotely? I'm in a different timezone.", 1, 19, 5),
            ("mf-c06", "mf-04", "strongandsteady", "This cue fixed my setup immediately. Shared it with my whole team.", 1, 5, 3),
            ("mf-c07", "mf-05", "nightshiftnina", "What would you change for someone who works night shifts?", 1, 9, 7),
            ("mf-c08", "mf-07", "plannerpete", "The three-workout template is exactly what I needed. Can I get it as a PDF?", 1, 8, 12),
            ("mf-c09", "mf-08", "universitygym", "We run a student fitness society and would love to host a beginner lifting workshop with you.", 2, 21, 3),
            ("mf-c10", "mf-09", "deskbounddan", "I feel this mostly on one side. Should I reduce the weight?", 1, 6, 8),
            ("mf-c11", "mf-11", "progressnotperfect", "Small increments have been a game changer. Thanks for keeping it practical.", 1, 3, 2),
            ("mf-c12", "mf-12", "quicklunch", "This felt more like a supplement pitch than your usual coaching advice.", 2, 4, 13),
            ("mf-c13", "mf-13", "restdayrebel", "Needed this reminder. I always feel guilty taking a day off.", 1, 2, 5),
            ("mf-c14", "mf-14", "cash_growth_fast", "💰💰 Make $500/day from home — click the link in our bio!", 1, 1, 9),
        ],
    },
]


def _aware_local(reference: date, weekday: int, hour: int, weeks_ago: int, tz: ZoneInfo):
    """Most recent occurrence of weekday/hour at least `weeks_ago` weeks back."""
    offset = (reference.weekday() - weekday) % 7
    local_date = reference - timedelta(days=offset, weeks=weeks_ago - 1)
    return datetime.combine(local_date, time(hour=hour), tzinfo=tz)


def _insight_metrics(*, index: int, day_index: int, base_views: int, base_rate: float):
    jitter = 1 + (((index * 11 + day_index * 7) % 9) - 4) / 100
    decay = max(0.08, 0.56 ** day_index)
    views = max(20, int(base_views * decay * jitter))
    reach = max(1, int(views * 0.64))
    daily_rate = max(0.5, base_rate * (1 + (((index + day_index * 3) % 7) - 3) * 0.015))
    engagement = max(1, int(reach * daily_rate / 100))
    likes = int(engagement * 0.76)
    comments = int(engagement * 0.10)
    shares = int(engagement * 0.08)
    saves = max(0, engagement - likes - comments - shares)
    return {
        "views": views,
        "reach": reach,
        "likes": likes,
        "comments": comments,
        "shares": shares,
        "saves": saves,
    }


@transaction.atomic
def seed_demo_data(reference_date: date | None = None) -> dict:
    reference = reference_date or date.today()
    password = settings.DEMO_PASSWORD

    for dataset in DEMO_USERS:
        user, _ = User.objects.get_or_create(
            email=dataset["email"],
            defaults={"full_name": dataset["full_name"]},
        )
        user.full_name = dataset["full_name"]
        user.set_password(password)
        user.save(update_fields=["full_name", "password"])

        workspace, _ = Workspace.objects.get_or_create(
            slug=dataset["workspace_slug"],
            defaults={"name": dataset["workspace_name"], "created_by": user},
        )
        workspace.name = dataset["workspace_name"]
        workspace.niche = dataset["niche"]
        workspace.timezone = dataset["timezone"]
        workspace.created_by = workspace.created_by or user
        workspace.save()

        WorkspaceMembership.objects.get_or_create(
            workspace=workspace,
            user=user,
            defaults={"role": MembershipRole.OWNER},
        )
        UserPreference.objects.update_or_create(
            user=user,
            defaults={
                "niche": dataset["niche"],
                "goals": dataset["goals"],
                "preferred_language": dataset["preferred_language"],
                "tone": dataset["tone"],
                "content_style": dataset["content_style"],
                "target_audience": dataset["target_audience"],
                "keywords": dataset["keywords"],
            },
        )

        accounts = []
        for account_data in dataset["accounts"]:
            account, _ = SocialAccount.objects.update_or_create(
                workspace=workspace,
                platform=account_data["platform"],
                handle=account_data["handle"],
                defaults={
                    "display_name": account_data["display_name"],
                    "follower_count": account_data["follower_count"],
                    "is_simulated": True,
                },
            )
            accounts.append(account)

        tz = ZoneInfo(dataset["timezone"])
        posts_by_external = {}
        for index, (external_id, account_index, weekday, hour, weeks_ago, media_type, caption) in enumerate(
            dataset["posts"]
        ):
            local_published = _aware_local(reference, weekday, hour, weeks_ago, tz)
            account = accounts[account_index]
            post, _ = Post.objects.update_or_create(
                social_account=account,
                external_id=external_id,
                defaults={
                    "workspace": workspace,
                    "caption": caption,
                    "media_type": media_type,
                    "permalink": f"https://simulated.example/{workspace.slug}/{external_id}",
                    "published_at": local_published.astimezone(dt_timezone.utc),
                    "is_simulated": True,
                },
            )
            posts_by_external[external_id] = post

            slot_weight = dataset["slot_weights"].get((weekday, hour), 1.0)
            base_rate = 3.2 + slot_weight * 2.0 + ((index * 3) % 5) * 0.25
            base_views = int((1800 + (index * 263) % 2600) * (0.9 + slot_weight * 0.18))

            local_date = local_published.date()
            expected_insight_dates = []
            for day_index in range(10):
                insight_date = local_date + timedelta(days=day_index)
                if insight_date > reference:
                    break
                expected_insight_dates.append(insight_date)
                metrics = _insight_metrics(
                    index=index,
                    day_index=day_index,
                    base_views=base_views,
                    base_rate=base_rate,
                )
                PostInsight.objects.update_or_create(
                    post=post,
                    date=insight_date,
                    defaults={"workspace": workspace, **metrics},
                )
            # Re-seeding with a different reference date must not leave stale
            # insight rows outside the deterministic demo window.
            PostInsight.objects.filter(post=post).exclude(
                date__in=expected_insight_dates
            ).delete()

        for (
            external_id,
            post_external,
            author,
            text,
            likes,
            days_after,
            hour,
        ) in dataset["comments"]:
            post = posts_by_external[post_external]
            local_post_date = post.published_at.astimezone(tz).date()
            comment_date = min(local_post_date + timedelta(days=days_after), reference)
            commented_at = datetime.combine(
                comment_date, time(hour=hour), tzinfo=tz
            ).astimezone(dt_timezone.utc)
            Comment.objects.update_or_create(
                workspace=workspace,
                external_id=external_id,
                defaults={
                    "post": post,
                    "author_username": author,
                    "text": text,
                    "commented_at": commented_at,
                    "like_count": likes,
                    "sentiment": "unknown",
                    "intent": "unknown",
                    "is_question": False,
                    "is_collaboration_opportunity": False,
                    "confidence": None,
                    "analysis_summary": "",
                    "analyzed_at": None,
                    "is_simulated": True,
                },
            )

    return {
        "users": User.objects.filter(
            email__in=[dataset["email"] for dataset in DEMO_USERS]
        ).count(),
        "workspaces": Workspace.objects.filter(
            slug__in=[dataset["workspace_slug"] for dataset in DEMO_USERS]
        ).count(),
        "social_accounts": SocialAccount.objects.filter(
            workspace__slug__in=[dataset["workspace_slug"] for dataset in DEMO_USERS]
        ).count(),
        "posts": Post.objects.filter(
            workspace__slug__in=[dataset["workspace_slug"] for dataset in DEMO_USERS]
        ).count(),
        "post_insights": PostInsight.objects.filter(
            workspace__slug__in=[dataset["workspace_slug"] for dataset in DEMO_USERS]
        ).count(),
        "comments": Comment.objects.filter(
            workspace__slug__in=[dataset["workspace_slug"] for dataset in DEMO_USERS]
        ).count(),
        "reference_date": reference.isoformat(),
    }
