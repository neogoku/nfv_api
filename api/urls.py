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
    url(r'^create', views.create_vnf_catalog),
    url(r'^listCatalog', views.list_vnf_catalog),
    url(r'^toscaTranslate', views.translate),
    url(r'^displayFile/(?P<fileType>.+)/(?P<catalogId>.+)', views.get_file_content),
    url(r'^uploadFile', views.upload_vnf_file),
    url(r'^deleteCatalogFiles', views.deleteCatalogFiles),
    url(r'^downloadFile', views.download_file),
    url(r'^listEnterpriseCatalog', views.list_enterprise_catalog),
    url(r'^listInstances', views.listInstances),
    url(r'^listHypervisors', views.listHypervisors),
    url(r'^migrateVM',views.migrateVM),

    # upload_vnf_file(request,catalogId,vnfdFilename='', vnfdFilePath='',vnfdCfgFilename='',vnfdCfgFilePath='',vnfdParamFilename='', vnfdParamPath=''):
    # url(r'^$',views.login,name='login'),
    # url(r'^login/', views.loginHandler),
]
