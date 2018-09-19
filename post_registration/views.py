from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from social_django.models import UserSocialAuth
from eventbrite import Eventbrite


@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView, LoginRequiredMixin):

    """ This is the index view. Here we display all the banners that the user
    has created """

    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        token = get_auth_token(self.request.user)
        eventbrite = Eventbrite(token)
        context['events'] = eventbrite.get('/users/me/events/')['events']
        # import ipdb; ipdb.set_trace()
        return context


def get_auth_token(user):

    """
    This method will receive an user and
    return its repesctive social_auth token
    """
    try:
        token = user.social_auth.get(
            provider='eventbrite'
        ).access_token
    except UserSocialAuth.DoesNotExist:
        print('UserSocialAuth does not exists!')
    return token