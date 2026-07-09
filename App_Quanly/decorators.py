from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def quanly_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.username == 'quanly':
            return view_func(request, *args, **kwargs)

        messages.success(request, "Dùng tài khoản quản lý.")
        request.session['quanly_url'] = request.path
        return redirect('account:login')

    return wrapper

