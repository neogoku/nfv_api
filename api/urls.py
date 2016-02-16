from django.conf.urls import url

from . import views

urlpatterns = [
    # url(r'^$',views.index,name='index'),
    url(r'^loginHandler/(?P<userId>.+)/(?P<pwd>.+)', views.loginHandler),
    # url(r'^$',views.login,name='login'),
    # url(r'^login/', views.loginHandler),
]
