from django.conf.urls import url

from . import views

urlpatterns = [
    # url(r'^$',views.index,name='index'),
    url(r'^loginHandler/(?P<userId>.+)/(?P<pwd>.+)', views.loginHandler),
    url(r'^approve/(?P<catalogId>.+)', views.approveCatalog),
    url(r'^delete/(?P<catalogId>.+)', views.deleteCatalog),
    url(r'^reject/(?P<catalogId>.+)', views.rejectCatalog),
    url(r'^toscaValidate', views.toscaValidate),
    url(r'^uploadImage', views.uploadImage),
    url(r'^create/(?P<catalogName>.+)/(?P<catalogDesc>.+)/(?P<vmImageFile>.+)/(?P<vnfdFilename>.+)/(?P<vnfdCfgFilename>.+)/(?P<vnfdParamFilename>.+)/(?P<vnfdFilePath>.+)/(?P<vnfdCfgFilePath>.+)/(?P<vnfdParamPath>.+)/(?P<vmImagePath>.+)',views.create_vnf_catalog),
    url(r'^listCatalog', views.list_vnf_catalog),
    url(r'^translate', views.translate),
    # url(r'^$',views.login,name='login'),
    # url(r'^login/', views.loginHandler),
]
