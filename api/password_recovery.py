from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.password_recovery import InvalidReset, confirm_reset, request_reset
from .throttles import PasswordResetAccountThrottle, PasswordResetConfirmThrottle, PasswordResetIPThrottle
from .views import _auth_origin_allowed

MESSAGE = 'Si existe una cuenta elegible asociada a ese correo, recibirás instrucciones para restablecer tu contraseña.'
INVALID_LINK = 'El enlace no es válido, ha caducado o ya fue utilizado. Solicita uno nuevo.'


class ResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254, trim_whitespace=True)


class ResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': ['Las contraseñas no coinciden.']})
        return attrs


@method_decorator(never_cache, name='dispatch')
class PasswordResetRequest(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetIPThrottle, PasswordResetAccountThrottle]

    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_reset(serializer.validated_data['email'], request._request.request_id)
        return Response({'message': MESSAGE})


@method_decorator(never_cache, name='dispatch')
class PasswordResetConfirm(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetConfirmThrottle]

    def post(self, request):
        if not _auth_origin_allowed(request):
            return Response({'detail': 'Origen no permitido.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        try:
            confirm_reset(values['uid'], values['token'], values['new_password'], request._request.request_id)
        except InvalidReset:
            return Response({'detail': INVALID_LINK, 'code': 'invalid_reset'}, status=status.HTTP_400_BAD_REQUEST)
        except DjangoValidationError as exc:
            return Response({'new_password': exc.messages}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Tu contraseña se actualizó correctamente.'})
