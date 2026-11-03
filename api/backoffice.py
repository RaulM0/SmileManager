"""Minimal operational backoffice; no clinical record endpoints."""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import DatabaseError, IntegrityError, connection
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import generics, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from DiagnosticosIA.models import AIAnalysisRun
from Citas.models import Cita
from Pacientes.models import Paciente
from Usuarios.models import AuditEvent
from .policies import IsSystemAdmin, has_backoffice_assignment
from .services.backoffice import AdministrativeAccountProtected, create_user, set_user_active
from .throttles import ExpensiveThrottle

User = get_user_model()
USER_FIELDS = ('id', 'username', 'email', 'is_active', 'is_staff', 'date_joined', 'last_login')


class Pagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_active', 'is_staff', 'date_joined', 'last_login')
        read_only_fields = fields


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    backoffice_access = serializers.BooleanField(default=False)

    def to_internal_value(self, data):
        if hasattr(data, 'keys'):
            unknown = set(data.keys()) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({'detail': 'Se enviaron campos no permitidos.'})
        return super().to_internal_value(data)

    def validate_username(self, value):
        try:
            User._meta.get_field('username').run_validators(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages) from exc
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con este nombre.')
        return value

    def validate(self, attrs):
        candidate = User(username=attrs['username'], email=attrs['email'], first_name=attrs['first_name'], last_name=attrs['last_name'])
        try:
            validate_password(attrs['password'], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages}) from exc
        return attrs


class UserDetailSerializer(UserSerializer):
    backoffice_assigned = serializers.SerializerMethodField()
    administrative_account = serializers.SerializerMethodField()
    patient_count = serializers.IntegerField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('backoffice_assigned', 'administrative_account', 'patient_count')
        read_only_fields = fields

    def get_backoffice_assigned(self, user):
        if not hasattr(user, '_backoffice_assigned'):
            user._backoffice_assigned = has_backoffice_assignment(user)
        return user._backoffice_assigned

    def get_administrative_account(self, user):
        return user.is_staff or user.is_superuser or self.get_backoffice_assigned(user)


class AuditSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True, allow_null=True)
    class Meta:
        model = AuditEvent
        fields = ('id', 'timestamp', 'actor_id', 'actor_username', 'action', 'resource_type', 'resource_id', 'outcome', 'request_id')
        read_only_fields = fields


class RunSerializer(serializers.ModelSerializer):
    potentially_stale = serializers.SerializerMethodField()
    class Meta:
        model = AIAnalysisRun
        fields = ('id', 'status', 'requested_by_id', 'requested_at', 'started_at', 'completed_at', 'model_name', 'model_version', 'failure_category', 'request_id', 'potentially_stale')
        read_only_fields = fields

    def get_potentially_stale(self, run):
        return run.status == AIAnalysisRun.RUNNING and run.started_at < stale_cutoff()


def stale_cutoff():
    return timezone.now() - timedelta(seconds=max(1, getattr(settings, 'BACKOFFICE_AI_STALE_SECONDS', 3600)))


def date_filters(queryset, params, field):
    for key, lookup in (('from', 'gte'), ('to', 'lte')):
        if params.get(key):
            value = serializers.DateField().run_validation(params[key])
            queryset = queryset.filter(**{f'{field}__date__{lookup}': value})
    return queryset


@method_decorator(never_cache, name='dispatch')
class AdminAPIView(APIView):
    permission_classes = [IsSystemAdmin]


@method_decorator(never_cache, name='dispatch')
class AdminList(generics.ListAPIView):
    permission_classes = [IsSystemAdmin]
    pagination_class = Pagination


class Dashboard(AdminAPIView):
    def get(self, request):
        users = User.objects.aggregate(active=Count('id', filter=Q(is_active=True)), inactive=Count('id', filter=Q(is_active=False)))
        runs = AIAnalysisRun.objects.aggregate(running=Count('id', filter=Q(status='RUNNING')), failed=Count('id', filter=Q(status='FAILED')), stale=Count('id', filter=Q(status='RUNNING', started_at__lt=stale_cutoff())))
        patients = Paciente.objects.filter(estatus='A').count()
        today = timezone.localdate()
        appointments = Cita.objects.aggregate(today=Count('id', filter=Q(fecha=today)), upcoming=Count('id', filter=Q(fecha__gt=today, estatus='P')))
        recent = AuditEvent.objects.filter(action__in=('USER_CREATED', 'BACKOFFICE_ACCESS_GRANTED', 'USER_ACTIVATED', 'USER_DEACTIVATED', 'BACKOFFICE_PATIENT_UPDATE', 'BACKOFFICE_HISTORY_UPDATE', 'BACKOFFICE_ODONTOGRAM_UPDATE', 'BACKOFFICE_APPOINTMENT_COMPLETED', 'BACKOFFICE_APPOINTMENT_CANCELLED')).select_related('actor').only('id', 'timestamp', 'actor_id', 'actor__username', 'action', 'resource_type', 'resource_id', 'outcome', 'request_id').order_by('-timestamp', '-pk')[:5]
        return Response({'users': users, 'ai': runs, 'patients_active': patients, 'appointments': appointments, 'recent_admin_events': AuditSerializer(recent, many=True).data})


class Users(AdminList):
    serializer_class = UserSerializer
    def get_queryset(self):
        qs = User.objects.only(*USER_FIELDS).order_by('username', 'pk')
        term = self.request.query_params.get('search', '').strip()[:150]
        if term:
            qs = qs.filter(Q(username__icontains=term) | Q(email__icontains=term))
        state = self.request.query_params.get('state', '')
        if state not in ('', 'active', 'inactive'):
            raise serializers.ValidationError({'state': 'Estado no válido.'})
        return qs.filter(is_active=state == 'active') if state else qs


class CreateUser(AdminAPIView):
    throttle_classes = [ExpensiveThrottle]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = create_user(actor=request.user, request_id=request._request.request_id, **serializer.validated_data)
        except IntegrityError:
            raise serializers.ValidationError({'username': ['No fue posible crear el usuario con ese nombre.']})
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@method_decorator(never_cache, name='dispatch')
class UserDetail(generics.RetrieveAPIView):
    permission_classes = [IsSystemAdmin]
    serializer_class = UserDetailSerializer
    queryset = User.objects.only(*USER_FIELDS, 'is_superuser').annotate(patient_count=Count('pacientes'))


class UserActivation(AdminAPIView):
    throttle_classes = [ExpensiveThrottle]
    def post(self, request, pk, operation):
        if operation not in ('activate', 'deactivate'):
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            user = set_user_active(actor=request.user, user_id=pk, active=operation == 'activate', request_id=request._request.request_id)
        except AdministrativeAccountProtected:
            return Response({'detail': 'El estado de las cuentas administrativas se gestiona fuera de esta pantalla.'}, status=status.HTTP_409_CONFLICT)
        return Response(UserSerializer(user).data)


class AuditList(AdminList):
    serializer_class = AuditSerializer
    def get_queryset(self):
        qs = date_filters(AuditEvent.objects.select_related('actor').only('id', 'timestamp', 'actor_id', 'actor__username', 'action', 'resource_type', 'resource_id', 'outcome', 'request_id'), self.request.query_params, 'timestamp')
        for name in ('action', 'resource_type', 'outcome', 'request_id'):
            if self.request.query_params.get(name):
                value = self.request.query_params[name][:150]
                if name == 'request_id':
                    value = serializers.UUIDField().run_validation(value)
                qs = qs.filter(**{name: value})
        if self.request.query_params.get('actor'):
            actor = serializers.IntegerField(min_value=1).run_validation(self.request.query_params['actor'])
            qs = qs.filter(actor_id=actor)
        return qs.order_by('-timestamp', '-pk')


@method_decorator(never_cache, name='dispatch')
class AuditDetail(generics.RetrieveAPIView):
    permission_classes = [IsSystemAdmin]
    serializer_class = AuditSerializer
    queryset = AuditEvent.objects.select_related('actor').only('id', 'timestamp', 'actor_id', 'actor__username', 'action', 'resource_type', 'resource_id', 'outcome', 'request_id')


class Runs(AdminList):
    serializer_class = RunSerializer
    def get_queryset(self):
        qs = date_filters(AIAnalysisRun.objects.all(), self.request.query_params, 'requested_at')
        for field in ('status', 'model_version', 'failure_category'):
            if self.request.query_params.get(field):
                qs = qs.filter(**{field: self.request.query_params[field][:150]})
        return qs.order_by('-requested_at', '-pk')


@method_decorator(never_cache, name='dispatch')
class RunDetail(generics.RetrieveAPIView):
    permission_classes = [IsSystemAdmin]
    serializer_class = RunSerializer
    queryset = AIAnalysisRun.objects.all()


class System(AdminAPIView):
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
            db = 'ok'
        except DatabaseError:
            db = 'unavailable'
        return Response({'application': 'ok', 'database': db, 'ai': 'not_checked'})
