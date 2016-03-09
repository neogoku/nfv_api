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
    url(r'^toscaTranslate', views.translate),
    url(r'^displayFile/(?P<fileType>.+)/(?P<catalogId>.+)', views.get_file_content),
    url(
        r'^uploadFile/(?P<catalogId>.+)/(?P<vnfdFilename>.+)/(?P<vnfdFilePath>.+)/(?P<vnfdCfgFilename>.+)/(?P<vnfdCfgFilePath>.+)/(?P<vnfdParamFilename>.+)/(?P<vnfdParamPath>.+)',
        views.upload_vnf_file),
    url(r'^deleteCatalogFiles', views.deleteCatalogFiles),
    url(r'^downloadFile', views.download_file),
    url(r'^listEnterpriseCatalog', views.list_enterprise_catalog),

    # upload_vnf_file(request,catalogId,vnfdFilename='', vnfdFilePath='',vnfdCfgFilename='',vnfdCfgFilePath='',vnfdParamFilename='', vnfdParamPath=''):
    # url(r'^$',views.login,name='login'),
    # url(r'^login/', views.loginHandler),
]
