import re

from django.core.exceptions import ValidationError


COMMON_WEAK_PASSWORDS = {
    "123",
    "1234",
    "12345",
    "123456",
    "1234567",
    "12345678",
    "123456789",
    "1234567890",
    "000000",
    "111111",
    "654321",
    "87654321",
    "abc",
    "abcd",
    "abcde",
    "abcdef",
    "abcdefg",
    "abcdefgh",
    "abc123",
    "123abc",
    "qwerty",
    "qwerty123",
    "asdfgh",
    "zxcvbn",
    "password",
    "password1",
    "password123",
    "admin",
    "admin123",
    "matkhau",
    "matkhau123",
    "letmein",
    "welcome",
    "welcome123",
    "test",
    "test123",
}

KEYBOARD_SEQUENCES = (
    "qwertyuiop",
    "asdfghjkl",
    "zxcvbnm",
)


def _normalise(password):
    return str(password).strip().casefold()


def _is_repeated_pattern(password):
    if len(password) < 6:
        return False

    if len(set(password)) <= 2:
        return True

    for size in range(1, len(password) // 2 + 1):
        if len(password) % size == 0:
            pattern = password[:size]
            if pattern * (len(password) // size) == password:
                return True
    return False


def _contains_ordered_sequence(password, min_length=4):
    for token in re.findall(r"[a-z]+|\d+", password):
        if len(token) < min_length:
            continue

        for start in range(0, len(token) - min_length + 1):
            chunk = token[start:start + min_length]
            steps = [ord(chunk[index + 1]) - ord(chunk[index]) for index in range(len(chunk) - 1)]
            if all(step == 1 for step in steps) or all(step == -1 for step in steps):
                return True
    return False


def _contains_keyboard_sequence(password, min_length=4):
    for sequence in KEYBOARD_SEQUENCES:
        for start in range(0, len(sequence) - min_length + 1):
            chunk = sequence[start:start + min_length]
            if chunk in password or chunk[::-1] in password:
                return True
    return False


def _contains_user_info(password, user=None, username=None):
    values = []

    if username:
        values.append(username)

    if user and getattr(user, "is_authenticated", False):
        values.extend([
            getattr(user, "username", ""),
            getattr(user, "email", ""),
            getattr(user, "first_name", ""),
            getattr(user, "last_name", ""),
        ])

    for value in values:
        normalised_value = _normalise(value)
        if len(normalised_value) >= 4 and normalised_value in password:
            return True
    return False


def get_password_strength_errors(password, user=None, username=None):
    if not password:
        return []

    errors = []
    normalised_password = _normalise(password)

    if len(password) < 8:
        errors.append("Mật khẩu phải từ 8 ký tự trở lên.")

    if normalised_password in COMMON_WEAK_PASSWORDS:
        errors.append('Mật khẩu không được quá đơn giản như "123", "abc", "password".')

    if str(password).isdigit():
        errors.append("Mật khẩu không được toàn bộ là số.")

    if _is_repeated_pattern(normalised_password):
        errors.append("Mật khẩu không được lặp lại một ký tự hoặc một mẫu quá đơn giản.")

    if _contains_ordered_sequence(normalised_password):
        errors.append('Mật khẩu không được chứa chuỗi liên tiếp dễ đoán như "1234" hoặc "abcd".')

    if _contains_keyboard_sequence(normalised_password):
        errors.append('Mật khẩu không được chứa chuỗi bàn phím dễ đoán như "qwerty" hoặc "asdf".')

    if _contains_user_info(normalised_password, user=user, username=username):
        errors.append("Mật khẩu không được chứa tên tài khoản hoặc thông tin cá nhân.")

    return errors


def validate_strong_password(password, user=None, username=None):
    errors = get_password_strength_errors(password, user=user, username=username)
    if errors:
        raise ValidationError(errors)
