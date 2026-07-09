import logging

from App_Core.forms import ContactForm
from App_Account.models import Profile
from App_Core.models import Contact
from App_Post.models import Subject
from App_Product.models import Cart, Category, Order

logger = logging.getLogger(__name__)


def cart(request):
    cart = None
    profile = None
    categories = []
    subjects = []
    form_contact = None
    unread_contacts_count = 0
    new_orders_count = 0

    try:
        form_contact = ContactForm()

        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
            profile = Profile.objects.filter(user=request.user).first()

            if request.user.username == 'quanly':
                unread_contacts_count = Contact.objects.filter(is_read=False).count()
                new_orders_count = Order.objects.filter(is_read=False).count()

        categories = Category.objects.prefetch_related('subcategories')
        subjects = Subject.objects.all()

    except Exception:
        logger.exception("Context processor error")
        form_contact = ContactForm() if not form_contact else form_contact

    return {
        'cart': cart,
        'profile': profile,
        'categories': categories,
        'subjects': subjects,
        'form_contact': form_contact,
        'unread_contacts_count': unread_contacts_count,
        'new_orders_count': new_orders_count,
    }
