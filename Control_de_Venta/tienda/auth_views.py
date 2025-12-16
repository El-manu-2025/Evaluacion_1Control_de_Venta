from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
import logging
import time

from .models import Cliente
import secrets
import string
import logging


def _user_role(user: User) -> str:
    if user.is_superuser or user.groups.filter(name='Admin').exists():
        return 'admin'
    return 'client'


def _generate_unique_username(base: str) -> str:
    """Return an available username based on base, appending a short suffix if needed."""
    base = (base or 'user').lower()[:140]  # leave room for suffix
    candidate = base
    if not User.objects.filter(username=candidate).exists():
        return candidate
    # Try numeric suffixes first
    for i in range(1, 100):
        candidate = f"{base}-{i}"
        if not User.objects.filter(username=candidate).exists():
            return candidate
    # Fallback: random 4 chars suffix
    for _ in range(20):
        suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
        candidate = f"{base}-{suffix}"
        if not User.objects.filter(username=candidate).exists():
            return candidate
    # In worst case, return base with long random
    suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return f"{base}-{suffix}"


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Registra un cliente (User + Cliente) y retorna tokens + role.
    Acepta: correo/email, nombre/name (opcional), username (opcional), password.
    """
    email = (request.data.get('correo') or request.data.get('email') or '').strip()
    nombre = (request.data.get('nombre') or request.data.get('name') or '').strip()
    username_in = (request.data.get('username') or '').strip()
    password = (request.data.get('password') or '').strip()

    if not email or not password:
        return Response({'error': 'correo y password son requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    # Validación mínima de contraseña
    if len(password) < 8:
        return Response(
            {
                'error': 'La contraseña debe tener al menos 8 caracteres',
                'field': 'password',
                'min_length': 8,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Si el email ya está registrado, avisar conflicto explícito
    if User.objects.filter(email=email).exists():
        return Response({'error': 'El correo ya está registrado', 'field': 'email'}, status=status.HTTP_409_CONFLICT)

    # Username base a partir del input o del email
    username_base = (username_in or email).split('@')[0].lower()
    username = _generate_unique_username(username_base)

    try:
        user = User.objects.create_user(username=username, email=email, password=password, first_name=nombre[:30])
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creando usuario: {e}")
        return Response({'error': 'No se pudo crear el usuario'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Crear Cliente asociado con RUT numérico válido (10 dígitos)
    try:
        rut = ''.join(secrets.choice(string.digits) for _ in range(10))
        # Garantizar unicidad por si acaso
        for _ in range(5):
            if not Cliente.objects.filter(rut=rut).exists():
                break
            rut = ''.join(secrets.choice(string.digits) for _ in range(10))
        Cliente.objects.create(rut=rut, nombre=nombre or username, correo=email)
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error creando Cliente asociado: {e}")
        # Continuar: el login funciona aunque no se cree el registro de Cliente.

    refresh = RefreshToken.for_user(user)
    role = _user_role(user)
    return Response({'access': str(refresh.access_token), 'refresh': str(refresh), 'role': role, 'username': user.username}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Autentica y retorna tokens + role. Si username='admin' o grupo Admin => role=admin."""
    identifier = (request.data.get('username') or request.data.get('email') or request.data.get('correo') or '').strip()
    password = (request.data.get('password') or '').strip()
    if not identifier or not password:
        return Response({'error': 'usuario/correo y password requeridos'}, status=status.HTTP_400_BAD_REQUEST)

    username = identifier.lower()
    start = time.monotonic()
    try:
        user = authenticate(username=username, password=password)
    except Exception as e:
        logging.getLogger(__name__).error(f"Auth error: {e}")
        return Response({'error': 'Servicio no disponible'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
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
    dur = (time.monotonic() - start)
    if dur > 5:
        logging.getLogger(__name__).warning(f"Login slow: {dur:.2f}s for user {username}")

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
