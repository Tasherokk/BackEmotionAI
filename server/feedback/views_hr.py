from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from feedback.permissions import IsHR
from feedback.services import hr_stats

class HrOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def get(self, request):
        q = request.query_params
        data = hr_stats.overview(
            from_s=q.get("from"),
            to_s=q.get("to"),
            event_id=q.get("event_id"),
            department=q.get("department"),
        )
        return Response(data)

class HrTimelineView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def get(self, request):
        q = request.query_params
        data = hr_stats.timeline(
            from_s=q.get("from"),
            to_s=q.get("to"),
            group_by=q.get("group_by", "day"),
            event_id=q.get("event_id"),
            department=q.get("department"),
        )
        return Response(data)

class HrByUserView(APIView):
    permission_classes = [IsAuthenticated, IsHR]

    def get(self, request):
        q = request.query_params
        data = hr_stats.by_user(
            from_s=q.get("from"),
            to_s=q.get("to"),
            limit=q.get("limit", 20),
            event_id=q.get("event_id"),
            department=q.get("department"),
        )
        return Response(data)
