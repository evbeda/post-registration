from post_registration.settings import get_env_variable

# Webhook related settings
URL_LOCAL = get_env_variable('URL_LOCAL')
URL_ENDPOINT = URL_LOCAL + '/webhook-point/'
WH_ACTIONS = 'order.placed'
