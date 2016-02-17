from django.conf.urls import url

from . import views

urlpatterns = [
    # url(r'^$',views.index,name='index'),
    url(r'^loginHandler/(?P<userId>.+)/(?P<pwd>.+)', views.loginHandler),
    url(
        r'^create/(?P<catalogName>.+)/(?P<catalogDesc>.+)/(?P<vmImageFile>.+)/(?P<vnfdFilename>.+)/(?P<vnfdCfgFilename>.+)/(?P<vnfdParamFilename>.+)',
        views.create_vnf_catalog),
    url(r'^listCatalog', views.list_vnf_catalog),
    # url(r'^$',views.login,name='login'),
    # url(r'^login/', views.loginHandler),
]
