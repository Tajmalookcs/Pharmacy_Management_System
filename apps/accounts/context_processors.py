from .models import Counter


def main_counter(request):
    if request.user.is_authenticated:
        mc = Counter.objects.filter(is_main=True, is_active=True).first()
        return {'main_counter': mc}
    return {'main_counter': None}
