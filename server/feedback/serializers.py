from rest_framework import serializers

class FeedbackPhotoRequestSerializer(serializers.Serializer):
    file = serializers.ImageField()
    event_id = serializers.IntegerField(required=False)
