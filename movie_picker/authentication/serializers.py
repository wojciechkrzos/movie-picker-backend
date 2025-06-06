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
        
        if existing_questions != len(set(question_ids)):
            raise serializers.ValidationError("Some question IDs do not exist")
        
        return value
