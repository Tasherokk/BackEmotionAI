from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg

from .models import Feedback
from .serializers import FeedbackSerializer


class MyFeedbackView(APIView):
    """История моих feedback'ов"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Пагинация
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        feedbacks = (
            Feedback.objects
            .filter(user=request.user)
            .select_related('event', 'company', 'department')
            .order_by('-created_at')[offset:offset+limit]
        )
        
        serializer = FeedbackSerializer(feedbacks, many=True)
        
        total = Feedback.objects.filter(user=request.user).count()
        
        return Response({
            'results': serializer.data,
            'total': total,
            'limit': limit,
            'offset': offset
        })


class MyStatsView(APIView):
    """Моя личная статистика"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from datetime import datetime, date
        
        # Фильтры по датам
        from_s = request.query_params.get('from')
        to_s = request.query_params.get('to')
        
        qs = Feedback.objects.filter(user=request.user)
        
        if from_s:
            d_from = datetime.strptime(from_s, "%Y-%m-%d").date()
            qs = qs.filter(created_at__date__gte=d_from)
        
        if to_s:
            d_to = datetime.strptime(to_s, "%Y-%m-%d").date()
            qs = qs.filter(created_at__date__lte=d_to)
        
        # Основные метрики
        total = qs.count()
        avg_conf = qs.aggregate(v=Avg("confidence"))["v"] or 0.0
        
        # Распределение эмоций
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
        
        return Response({
            "total": total,
            "avg_confidence": float(avg_conf),
            "top_emotion": top_emotion,
            "emotions": emo_counts,
            "filters": {"from": from_s, "to": to_s},
        })
