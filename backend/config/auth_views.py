from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([SessionAuthentication])
@ensure_csrf_cookie
def me(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Not authenticated.'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({'id': request.user.id, 'username': request.user.username})


# DRF's APIView.as_view() applies csrf_exempt automatically, so unauthenticated
# POSTs work without a token. CSRF is only enforced by SessionAuthentication
# for already-authenticated sessions.
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    username = request.data.get('username', '')
    password = request.data.get('password', '')
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({'detail': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
    login(request, user)
    return Response({'id': user.id, 'username': user.username})


@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({'detail': 'Logged out.'})
