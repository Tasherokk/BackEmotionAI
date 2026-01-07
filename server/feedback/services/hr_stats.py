from collections import defaultdict
from datetime import datetime, date
from django.db.models import Count, Avg
from django.db.models.functions import TruncDay, TruncMonth
from feedback.models import Feedback

def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()

def _base_qs(from_s: str | None, to_s: str | None, event_id: str | None, department: str | None):
    qs = Feedback.objects.all()
    d_from = _parse_date(from_s)
    d_to = _parse_date(to_s)

    if d_from:
        qs = qs.filter(created_at__date__gte=d_from)
    if d_to:
        qs = qs.filter(created_at__date__lte=d_to)
    if event_id:
        qs = qs.filter(event_id=int(event_id))
    if department:
        qs = qs.filter(department=department)

    return qs

def overview(from_s=None, to_s=None, event_id=None, department=None) -> dict:
    qs = _base_qs(from_s, to_s, event_id, department)

    total = qs.count()
    avg_conf = qs.aggregate(v=Avg("confidence"))["v"] or 0.0

    emo_counts = list(
        qs.values("emotion")
          .annotate(count=Count("id"))
          .order_by("-count")
    )

    if total > 0:
        for x in emo_counts:
            x["percent"] = round(x["count"] * 100.0 / total, 2)
        top_emotion = emo_counts[0]["emotion"]
    else:
        top_emotion = None

    return {
        "total": total,
        "avg_confidence": float(avg_conf),
        "top_emotion": top_emotion,
        "emotions": emo_counts,  # [{emotion,count,percent}]
        "filters": {"from": from_s, "to": to_s, "event_id": event_id, "department": department},
    }

def timeline(from_s=None, to_s=None, group_by="day", event_id=None, department=None) -> dict:
    qs = _base_qs(from_s, to_s, event_id, department)

    trunc = TruncDay("created_at") if group_by == "day" else TruncMonth("created_at")

    rows = (
        qs.annotate(bucket=trunc)
          .values("bucket", "emotion")
          .annotate(count=Count("id"))
          .order_by("bucket")
    )

    # pivot: bucket -> {emotion: count}
    buckets = defaultdict(dict)
    for r in rows:
        b = r["bucket"].date().isoformat() if group_by == "day" else r["bucket"].date().replace(day=1).isoformat()
        buckets[b][r["emotion"]] = r["count"]

    series = [{"bucket": k, "emotions": v} for k, v in sorted(buckets.items(), key=lambda x: x[0])]

    return {
        "group_by": group_by,
        "series": series,
        "filters": {"from": from_s, "to": to_s, "event_id": event_id, "department": department},
    }

def by_user(from_s=None, to_s=None, limit=20, event_id=None, department=None) -> dict:
    qs = _base_qs(from_s, to_s, event_id, department)

    rows = (
        qs.values("user_id", "user__username", "user__name")
          .annotate(total=Count("id"), avg_conf=Avg("confidence"))
          .order_by("-total")[: int(limit)]
    )

    # топ эмоция на юзера (простая версия через доп. запросы по каждому — ок для MVP)
    result = []
    for r in rows:
        top = (
            qs.filter(user_id=r["user_id"])
              .values("emotion")
              .annotate(count=Count("id"))
              .order_by("-count")
              .first()
        )
        who = (r["user__name"] or "").strip() or r["user__username"]
        result.append({
            "user_id": r["user_id"],
            "name": who,
            "username": r["user__username"],
            "total": r["total"],
            "avg_confidence": float(r["avg_conf"] or 0.0),
            "top_emotion": top["emotion"] if top else None,
        })

    return {"users": result, "filters": {"from": from_s, "to": to_s, "event_id": event_id, "department": department}}
