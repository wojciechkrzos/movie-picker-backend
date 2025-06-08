# authentication/serializers.py
from rest_framework import serializers
from .models import User, Question, Answer, UserStreamingService
from movie.serializers import StreamingServiceSerializer


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question', 'available_answers', 'created_at']


class AnswerSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = ['id', 'question', 'answer', 'created_at']


class UserStreamingServiceSerializer(serializers.ModelSerializer):
    streaming_service = StreamingServiceSerializer(read_only=True)

    class Meta:
        model = UserStreamingService
        fields = ['streaming_service']


class UserStreamingServiceUpdateSerializer(serializers.Serializer):
    """Serializer for updating user's streaming services"""
    streaming_service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of streaming service IDs to associate with the user"
    )

    def validate_streaming_service_ids(self, value):
        """Validate that all streaming service IDs exist"""
        from movie.models import StreamingService
        existing_services = StreamingService.objects.filter(id__in=value).count()
        if existing_services != len(value):
            raise serializers.ValidationError("One or more streaming service IDs are invalid.")
        return value

    def update(self, instance, validated_data):
        """Update user's streaming services"""
        streaming_service_ids = validated_data.get('streaming_service_ids', [])

        # Clear existing streaming services and set new ones
        instance.streaming_services.set(streaming_service_ids)

        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    streaming_services = UserStreamingServiceSerializer(
        source='userstreamingservice_set', many=True, read_only=True
    )
    quiz_answers = AnswerSerializer(source='answer_set', many=True, read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'streaming_services', 'quiz_answers', 'created_at']


class QuizAnswersSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            required=['question_id', 'answer']
        )
    )

    def validate_answers(self, value):
        """Validate that all question IDs exist"""
        question_ids = [answer['question_id'] for answer in value]
        existing_questions = Question.objects.filter(id__in=question_ids).count()

        if existing_questions != len(question_ids):
            raise serializers.ValidationError("One or more question IDs are invalid.")

        return value
