from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Feedback
from .serializers import FeedbackPhotoRequestSerializer
from .services.emotion_ai import analyze_face

class FeedbackPhotoView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=FeedbackPhotoRequestSerializer,
        parameters=[
            OpenApiParameter(
                name='event_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description='Optional event ID to associate with feedback',
                allow_blank=True
            ),
        ],
        responses={
            201: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "emotion": {"type": "string"},
                        "confidence": {"type": "number"},
                        "top3": {"type": "array", "items": {"type": "string"}},
                        "face_box": {"type": "object"},
                        "probs": {"type": "object"},
                    }
                },
                description="Feedback created successfully"
            ),
            400: OpenApiResponse(description="Invalid data or no face detected"),
            503: OpenApiResponse(description="AI service unavailable"),
        },
        description="Upload a photo to analyze facial emotions and create feedback. The photo should contain a clear face. Event ID is optional."
    )
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
            company=request.user.company,
            department=request.user.department,
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
