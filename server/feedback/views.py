from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Feedback
from .serializers import FeedbackPhotoRequestSerializer
from .services.emotion_ai import analyze_face

class FeedbackPhotoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = FeedbackPhotoRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        img = ser.validated_data["file"]
        event_id = ser.validated_data.get("event_id")

        # 1) дергаем AI
        ai = analyze_face(img)

        # 2) сохраняем в БД
        fb = Feedback.objects.create(
            user=request.user,
            emotion=ai.get("emotion", "unknown"),
            confidence=float(ai.get("confidence", 0.0)),
            probs=ai.get("probs", {}),
            top3=ai.get("top3", []),
            face_box=ai.get("face_box"),
            event_id=event_id,
            department=getattr(request.user, "department", "") or "",  # если поля нет — просто ""
        )

        # 3) ответ мобилке
        return Response({
            "id": fb.id,
            "emotion": fb.emotion,
            "confidence": fb.confidence,
            "top3": fb.top3,
            "face_box": fb.face_box,
            "probs": fb.probs,
        }, status=status.HTTP_201_CREATED)
