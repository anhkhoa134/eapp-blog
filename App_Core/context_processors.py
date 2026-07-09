import logging

from App_Core.forms import ContactForm
from App_Account.models import Profile
from App_Core.models import Contact
from App_Post.models import Subject
from App_Product.models import Cart, Category, Order
from App_Product.cart_access import commerce_behavior, get_cart_for_request

logger = logging.getLogger(__name__)


def cart(request):
    cart = None
    profile = None
    categories = []
    subjects = []
    form_contact = None
    commerce_config = None
    unread_contacts_count = 0
    new_orders_count = 0

    try:
        form_contact = ContactForm()
        commerce_config = commerce_behavior()

        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
            profile = Profile.objects.filter(user=request.user).first()

            if request.user.username == 'quanly':
                unread_contacts_count = Contact.objects.filter(is_read=False).count()
                new_orders_count = Order.objects.filter(is_read=False).count()
        elif commerce_config.allow_guest_cart:
            cart = get_cart_for_request(request)

        categories = Category.objects.prefetch_related('subcategories')
        subjects = Subject.objects.all()

    except Exception:
        logger.exception("Context processor error")
        form_contact = ContactForm() if not form_contact else form_contact
        commerce_config = commerce_config or commerce_behavior()

    return {
        'cart': cart,
        'profile': profile,
        'categories': categories,
        'subjects': subjects,
        'form_contact': form_contact,
        'unread_contacts_count': unread_contacts_count,
        'new_orders_count': new_orders_count,
        'commerce_config': commerce_config,
    }
