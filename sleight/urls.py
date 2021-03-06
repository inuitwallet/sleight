"""sleight URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt

from sleight.views.exchange import index, exchange, register, graph
from sleight.views.private_api import GetBalances, PlaceOrder, GetOrders, CancelOrder, \
    GetTrades
from sleight.views.public_api import GetOrderBook, GetTicker

urlpatterns = [
    # admin site
    url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
    url(r'^jet/dashboard/', include('jet.dashboard.urls', 'jet-dashboard')),
    url(r'^admin', admin.site.urls),
    
    # user auth
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^register/', register, name='register'),

    # front end exchange
    url(r'^$', index, name='index'),
    url(r'^graph$', graph),
    url(r'^exchange/(?P<base_currency>\w+)/(?P<relative_currency>\w+)$', exchange),

    # private api
    url(r'^get_balances$', csrf_exempt(GetBalances.as_view())),
    url(r'^place_order$', csrf_exempt(PlaceOrder.as_view())),
    url(r'^get_orders$', csrf_exempt(GetOrders.as_view())),
    url(r'^cancel_order$', csrf_exempt(CancelOrder.as_view())),
    url(r'^get_trades$', csrf_exempt(GetTrades.as_view())),

    # public api
    url(
        r'^get_order_book/(?P<base_currency>\w+)/(?P<relative_currency>\w+)$',
        csrf_exempt(GetOrderBook.as_view())
    ),
    url(
        r'^get_ticker/(?P<base_currency>\w+)/(?P<relative_currency>\w+)$',
        csrf_exempt(GetTicker.as_view())
    ),

]
