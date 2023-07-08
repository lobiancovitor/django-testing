
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

# Create your views here.


from django.views.generic import ListView

from .models import Membership, UserMembership, Subscription

import stripe

def profile_view(request):
    print(get_user_subscription(request))
    user_membership = get_user_membership(request)
    user_subscription = get_user_subscription(request)
    context = {
        'user_membership': user_membership,
        'user_subscription': user_subscription
    }
    return render(request, "memberships/profile.html", context)


def get_user_membership(request):
    user_membership_qs = UserMembership.objects.filter(user=request.user)
    if user_membership_qs.exists():
        return user_membership_qs.first()
    return None


def get_user_subscription(request):
    user_subscription_qs = Subscription.objects.filter(
        user_membership=get_user_membership(request))
    if user_subscription_qs.exists():
        user_subscription = user_subscription_qs.first()
        return user_subscription
    return 'Professional'

def get_selected_membership(request):
    membership_type = request.session['selected_membership_type']
    selected_membershi_qs = Membership.objects.filter(membership_type=membership_type)

    if selected_membershi_qs.exists():
        return selected_membershi_qs.first()
    return None

class MembershipSelectView(ListView):
    model = Membership

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        current_membership = get_user_membership(self.request)
        context['current_membership'] = str(current_membership.membership_type)
        return context
    
    def post(self, request, **kwargs):
        selected_membership = request.POST.get('membership_type')
        
        user_membership = get_user_membership(request)
        user_subscription = get_user_subscription(request)

        selected_membershi_qs = Membership.objects.filter(membership_type=selected_membership)

        if selected_membershi_qs.exists():
            selected_membership = selected_membershi_qs.first()

        # VALIDATION

        if user_membership.membership_type == selected_membership:
            if user_subscription != None:
                messages.info(request, "You already have this membership. Your next payment is due {}".format('get value from stripe'))

                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        return HttpResponseRedirect(reverse('memberships:payment'))
    
def PaymentView(request):
    user_membership = get_user_membership(request)
    try: 
        selected_membership = get_selected_membership(request)
    except:
        return redirect(reverse('memberships:select'))

    publishKey = settings.STRIPE_PUBLISHABLE_KEY

    if request.method == 'POST':
        try:
            token = request.POST['stripeToken']

            customer = stripe.Customer.retrieve(user_membership.stripe_customer_id)
            customer.source = token # 4242424242424242
            customer.save()

            subscription = stripe.Subscription.create(
                customer=user_membership.stripe_customer_id,
                items=[
                    { "plan": selected_membership.stripe_plan_id },
                ],
                source=token
            )

            return redirect(reverse('memberships:update-transactions',
                                    kwargs={
                                        'subscription_id': subscription.id
                                    }))

        except:
            messages.info(request, "An error has occurred, investigate it in the console")



    context = {
        'publishKey': publishKey,
        'selected_membership': selected_membership
    }

    return render(request, 'memberships/membership_payment.html', context)

def updateTransactions(request, subscription_id):
    user_membership = get_user_membership(request)
    selected_membership = get_selected_membership(request)

    user_membership.membership_type = selected_membership
    user_membership.save()

    sub, created = Subscription.objects.get_or_create(user_membership=user_membership)
    sub.stripe_subscription_id = subscription_id
    sub.active = True
    sub.save()

    try:
        del request.session['selected_membership_type']
    except:
        pass
    messages.info(request, 'successfully created {} membership').format(selected_membership)
    return redirect ('/courses')

def cancelSubscription(request):
    user_sub = get_user_subscription(request)

    if user_sub.active == False:
        messages.info(request, "You dont have an active membership")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    sub = stripe.Subscription.retrieve(user_sub.stripe_subscription_id)
    sub.delete()

    user_sub.active = False
    user_sub.save()

    free_membership = Membership.objects.filter(membership_type='Free').first()
    user_membership = get_user_membership(request)
    user_membership.membership_type = free_membership
    user_membership.sabe()

    messages.info(request, "Successfully canceled membership. An email has been sent")

    return redirect('/memberships')