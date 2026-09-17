from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes


def health_check(request):
    return JsonResponse({'status': 'ok'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return JsonResponse({
        'authenticated': True,
        'user_id': str(request.user.id),
        'email': request.user.email,
    })