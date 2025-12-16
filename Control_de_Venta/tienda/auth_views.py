from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Cliente


def _user_role(user: User) -> str:
    if user.is_superuser or user.groups.filter(name='Admin').exists():
        return 'admin'
    return 'client'


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Registra un cliente: crea User + Cliente y retorna tokens + role."""
    email = (request.data.get('correo') or request.data.get('email') or '').strip()
    nombre = (request.data.get('nombre') or request.data.get('name') or '').strip()
    password = (request.data.get('password') or '').strip()

    if not email or not password:
        return Response({'error': 'correo y password son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    username = email.lower()
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password, first_name=nombre[:30])

    # Crear Cliente asociado
    Cliente.objects.get_or_create(rut=username[:12], defaults={'nombre': nombre or username, 'correo': email})

    # Generar tokens
    refresh = RefreshToken.for_user(user)
    role = _user_role(user)
    return Response({'access': str(refresh.access_token), 'refresh': str(refresh), 'role': role}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Autentica y retorna tokens + role. Si username='admin' o grupo Admin => role=admin."""
    identifier = (request.data.get('username') or request.data.get('email') or request.data.get('correo') or '').strip()
    password = (request.data.get('password') or '').strip()
    if not identifier or not password:
        return Response({'error': 'usuario/correo y password requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    username = identifier.lower()
    user = authenticate(username=username, password=password)
    if not user:
        # Intento adicional: si enviaron email distinto del username, buscarlo
        try:
            found = User.objects.filter(email=identifier).first()
            if found:
                user = authenticate(username=found.username, password=password)
        except Exception:
            pass

    if not user:
        return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    role = _user_role(user)
    return Response({'access': str(refresh.access_token), 'refresh': str(refresh), 'role': role}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Retorna datos básicos del usuario autenticado y su rol."""
    user = request.user
    role = _user_role(user)
    return Response({
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': role,
    }, status=status.HTTP_200_OK)
