# from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db import connections
from collections import namedtuple
from rest_framework.decorators import api_view
from rest_framework.decorators import parser_classes
from rest_framework.parsers import JSONParser
import json
from rest_framework.response import Response
from rest_framework import status
from toscaparser.tosca_template import ToscaTemplate
from heat_translator_master.translator.shell import TranslatorShell
import random
import os
import zipfile
import StringIO
from wsgiref.util import FileWrapper
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import smart_str

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def index(request):
    cursor = connections['nfv'].cursor()
    sql = "SELECT User_Id, User_Type,First_Name FROM VNF_User"
    print 'sql:' + sql
    cursor.execute(sql)
    results = namedtuplefetchall(cursor)

    for row in results:
        print "User Id " + str(row.User_Id)
        print "User Type " + str(row.User_Type)
        row = cursor.fetchone()
    # print results[0][0]
    # print results[0].User_Id

    # data = cursor.fetchall()
    # for row in data :
    #     print row[0].User_Id
    #     row = cursor.fetchone()

    cursor.close()
    return HttpResponse("Hi... Neo is back...")


def login(request):
    return HttpResponse("Hello Login API...")


@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def loginHandler(request, userId='Ben', pwd=''):
    print 'userId:' + userId
    print 'pwd:' + pwd
    cursor = connections['nfv'].cursor()
    if request.method == 'GET':
        sql = "SELECT User_Type,First_Name,Last_Name FROM vnf_user where User_Id='" + userId + "' and Password='" + pwd + "'"
        print 'sql:' + sql
        cursor.execute(sql)
        results = namedtuplefetchall(cursor)
        for row in results:
            userRole = str(row.User_Type)
            userName = str(row.First_Name + ' ' + row.Last_Name)
            print "User Type " + userRole
            return JsonResponse({'UserRole': userRole, 'UserId': userId, 'UserName': userName})
    return JsonResponse({'UserRole': 'Invalid', 'UserId': userId})
            # elif request.method == 'POST':
            #     #return HttpResponse("Hello Login API post call response...")
            #     return Response({'received data': request.data})

#
# class loginHandler (views.APIView) :
#     def get(self, request, *args, **kwargs):
#         username = kwargs['username']
#         print 'Logged In User:'+username
#         return HttpResponse(username)


@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def approveCatalog(request, catalogId=''):
    d = json.loads(catalogId)
    for id in d:
        updateCatalog(id, "A")
    return JsonResponse({'status': 'success', 'catalogId': catalogId})

@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def rejectCatalog(request, catalogId=''):
    d = json.loads(catalogId)
    for id in d:
        updateCatalog(id, "R")
    return JsonResponse({'status': 'success', 'catalogId': catalogId})

@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def deleteCatalog(request, catalogId=''):
    cursor = connections['nfv'].cursor()
    sql = "delete from vnf_catalog where catalog_Id="+catalogId
    print 'sql:' + sql
    cursor.execute(sql)
    return JsonResponse({'status': 'deleted', 'catalogId': catalogId})

@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def deleteCatalogFiles(request):
    vnfDef = request.GET.get('vnfDefinition')
    vnfConfig = request.GET.get('Config')
    vnfParam = request.GET.get('ParameterValuePoint')
    catalogId = request.GET.get('catalogId')
    print vnfDef
    print vnfConfig
    print vnfParam
    cursor = connections['nfv'].cursor()
    sql = "SELECT * FROM vnf_catalog where catalog_Id=" + str(catalogId)
    cursor.execute(sql)
    results = namedtuplefetchall(cursor)

    for row in results:
        vnfDefPath = str(row.VNFD_Path)
        vnfConfigPath = str(row.VNF_Config_Path)
        vnfParamPath = str(row.VNF_Param_Path)
        vnfDefName = str(row.VNFD_Filename)
        vnfConfigName = str(row.VNF_Config_Filename)
        vnfParamName = str(row.VNF_Param_Filename)

    if vnfDef == 'true':
        if os.path.isfile(vnfDefPath):
            os.remove(vnfDefPath)
        sql='Update vnf_catalog set VNFD_Filename="None", VNFD_Path="None" where Catalog_Id=' + str(catalogId)
        cursor.execute(sql)
    if vnfConfig == 'true':
        if os.path.isfile(vnfConfigPath):
            os.remove(vnfConfigPath)
        sql='Update vnf_catalog set VNF_Config_Filename="None", VNF_Config_Path="None" where Catalog_Id=' + str(catalogId)
        cursor.execute(sql)
    if vnfParam == 'true':
        if os.path.isfile(vnfParamPath):
            os.remove(vnfParamPath)
        sql='Update vnf_catalog set VNFD_Param_Filename="None", VNF_Param_Path="None" where Catalog_Id=' + str(catalogId)
        cursor.execute(sql)


    return JsonResponse({'status': 'success', 'catalogId': catalogId})

@csrf_exempt
def translate(request):
    path = handle_uploaded_file(request.FILES['path'])
    #path = 'c:\\tosca_helloworld.yaml'
    obj = TranslatorShell()
    content = obj._translate('tosca', path, {}, True)
    os.remove(path)
    print path
    with open(path, 'a') as the_file:
        for line in content.splitlines():
            the_file.write(line+'\n')
    return JsonResponse({'status': 'success', 'content': content, 'path': path})

@csrf_exempt
def toscaValidate(request):
    path = handle_uploaded_file(request.FILES['path'])
    obj = ToscaTemplate(path, None, True)
    if obj.msg == 'success':
        return JsonResponse({'status': 'success', 'message': 'TOSCA Validation Successful', 'path' : path})
    else:
        return JsonResponse({'status': 'failed', 'message': obj.msg})

@csrf_exempt
def uploadImage(request):
    path = handle_uploaded_file(request.FILES['path'])
    return JsonResponse({'status': 'success', 'path': path})

def handle_uploaded_file(f):
    print f.name
    extension = f.name.split('.')[-1]
    filename = f.name +`random.random()` + '.' + extension
    path = '/home/rdk/' + filename
    with open(path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return path

def updateCatalog(catalogId, status):
    cursor = connections['nfv'].cursor()
    sql = "update vnf_catalog set status = '" + status + "' where catalog_Id=" + str(catalogId) + ""
    print 'sql:' + sql
    cursor.execute(sql)
    return JsonResponse({'status': 'success', 'catalogId': catalogId})

@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def create_vnf_catalog(request, catalogName, vmImageFile, vnfdFilename, catalogDesc='', vnfdCfgFilename='',
                       vnfdParamFilename='', vnfdFilePath='',vnfdCfgFilePath='', vnfdParamPath='', vmImagePath=''):
    print '\n' + 'Inside Create VNF Catalog...'
    print 'catalogName:' + catalogName
    print 'catalogDesc:' + catalogDesc
    print 'vmImageFile:' + vmImageFile
    print 'vnfdFilename:' + vnfdFilename
    print 'vnfdCfgFilename:' + vnfdCfgFilename
    print 'vnfdParamFilename:' + vnfdParamFilename

    cursor = connections['nfv'].cursor()
    status = 'P'
    if request.method == 'GET':
        sql = "INSERT INTO VNF_Catalog(Catalog_Name, Catalog_Desc,VM_Imagefile, VNFD_Filename, VNF_Config_Filename , VNF_Param_Filename, Status, VNFD_Path, VNF_Config_Path, VNF_Param_Path, VM_Image_Path) " + "VALUES ('" + catalogName + "','" + catalogDesc + "','" + vmImageFile + "','" + vnfdFilename + "','" + vnfdCfgFilename + "','" + vnfdParamFilename + "','" + status + "' ,'" + vnfdFilePath + "','" + vnfdCfgFilePath + "','" + vnfdParamPath + "','" + vmImagePath + "')"
        print 'sql:' + sql
        cursor.execute(sql)

        # Query to fetch Catalog_Id to the user
        retrieveSql = "SELECT Catalog_Id FROM VNF_Catalog where Catalog_Name='" + catalogName + "'";
        cursor.execute(retrieveSql)

        results = namedtuplefetchall(cursor)

        for row in results:
            catalogId = str(row.Catalog_Id)
            print "Catalog Id: " + catalogId
            return JsonResponse({'CatalogId': catalogId})


@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def list_vnf_catalog(request):
    print 'Inside VNF Catalog...'

    cursor = connections['nfv'].cursor()
    if request.method == 'GET':
        sql = "SELECT Catalog_Id, Catalog_Name, Catalog_Desc, VM_ImageFile, VNFD_Filename, VNF_Config_Filename , VNF_Param_Filename FROM VNF_Catalog where Status='P'"
        cursor.execute(sql)

        results = namedtuplefetchall(cursor)

        json_res = []

        for row in results:
            catalog_id = str(row.Catalog_Id)
            catalog_name = str(row.Catalog_Name)
            catalog_Desc = str(row.Catalog_Desc)
            vm_image_file = str(row.VM_ImageFile)
            vnfd_filename = str(row.VNFD_Filename)
            vnf_cfg_filename = str(row.VNF_Config_Filename)
            vnf_param_filename = str(row.VNF_Param_Filename)

            jsonobj = {'CatalogId': catalog_id, 'CatalogName': catalog_name, 'CatalogDesc': catalog_Desc,
                                'VM_ImageFile': vm_image_file, 'VNFD_Filename': vnfd_filename,
                                'VNF_Config_Filename': vnf_cfg_filename, 'VNF_Param_Filename': vnf_param_filename}

            #dataobj=[catalog_name,catalog_Desc,vm_image_file,vnfd_filename,vnf_cfg_filename,vnf_param_filename,catalog_id]

            json_res.append(jsonobj)
            #dataobj_res.append(dataobj)

    print 'JsonResponse:'+str(json_res)
    return JsonResponse(json_res, safe=False)


@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def list_enterprise_catalog(request):
    print 'Inside VNF Catalog...'

    cursor = connections['nfv'].cursor()
    if request.method == 'GET':
        sql = "SELECT Catalog_Id, Catalog_Name, Catalog_Desc, VM_ImageFile, VNFD_Filename, VNF_Config_Filename , VNF_Param_Filename FROM VNF_Catalog where Status='A'"
        cursor.execute(sql)

        results = namedtuplefetchall(cursor)

        json_res = []

        for row in results:
            catalog_id = str(row.Catalog_Id)
            catalog_name = str(row.Catalog_Name)
            catalog_Desc = str(row.Catalog_Desc)
            vm_image_file = str(row.VM_ImageFile)
            vnfd_filename = str(row.VNFD_Filename)
            vnf_cfg_filename = str(row.VNF_Config_Filename)
            vnf_param_filename = str(row.VNF_Param_Filename)

            jsonobj = {'CatalogId': catalog_id, 'CatalogName': catalog_name, 'CatalogDesc': catalog_Desc,
                       'VM_ImageFile': vm_image_file, 'VNFD_Filename': vnfd_filename,
                       'VNF_Config_Filename': vnf_cfg_filename, 'VNF_Param_Filename': vnf_param_filename}

            # dataobj=[catalog_name,catalog_Desc,vm_image_file,vnfd_filename,vnf_cfg_filename,vnf_param_filename,catalog_id]

            json_res.append(jsonobj)
            # dataobj_res.append(dataobj)

    print 'JsonResponse:' + str(json_res)
    return JsonResponse(json_res, safe=False)


@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def get_file_content(request, fileType, catalogId):
    print 'Inside get file name API...'
    cursor = connections['nfv'].cursor()
    if request.method == 'GET':
        if fileType == "vnfd":
            sql = "SELECT VNFD_Path FROM vnf_catalog where Catalog_Id=" + catalogId
            print'sql:' + sql
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)
            for row in results:
                vnfd_filename = str(row.VNFD_Path)
                print 'VNFD Path:' + vnfd_filename
                with open(vnfd_filename, 'r') as content_file:
                    content = content_file.read()
                print 'content:' + content
                return JsonResponse({'status': 'success', 'content': content}, safe=False)
        elif fileType == "vnf_cfg_filename":
            sql = "SELECT VNF_Config_Path FROM vnf_catalog where Catalog_Id=" + catalogId
            print'sql:' + sql
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)
            for row in results:
                vnf_cfg_filename = str(row.VNF_Config_Path)
                print 'VNFD Config Path:' + vnf_cfg_filename
                with open(vnf_cfg_filename, 'r') as content_file:
                    content = content_file.read()
                print 'content:' + content
                return JsonResponse({'status': 'success', 'content': content}, safe=False)
        elif fileType == "vnf_param":
            sql = "SELECT VNF_Param_Path FROM vnf_catalog where Catalog_Id=" + catalogId
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)
            for row in results:
                vnf_param_path = str(row.VNF_Param_Path)
                print 'VNFD Param Path:' + vnf_param_path
                with open(vnf_param_path, 'r') as content_file:
                    content = content_file.read()
                print 'content:' + content
                return JsonResponse({'status': 'success', 'content': content}, safe=False)


@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def upload_vnf_file(request, catalogId, vnfdFilename='', vnfdFilePath='', vnfdCfgFilename='', vnfdCfgFilePath='',
                    vnfdParamFilename='', vnfdParamPath=''):
    print 'Inside upload_vnf_file...'
    cursor = connections['nfv'].cursor()
    if request.method == 'GET':
        sql = "update vnf_catalog set VNFD_Filename='" + vnfdFilename + "',VNFD_Path='" + vnfdFilePath + "',VNF_Config_Filename='" + vnfdCfgFilename + "',VNF_Config_Path='" + vnfdCfgFilePath + "',VNF_Param_Filename='" + vnfdParamFilename + "',VNF_Param_Path='" + vnfdParamPath + "' where Catalog_Id='" + catalogId + "'"
        print 'sql:' + sql
        cursor.execute(sql)
        print 'uploaded successfully...'
    return JsonResponse({'CatalogId': catalogId, 'status': 'success'})


@api_view(['GET', 'POST'])
def download_file(request):
    print "here is it"
    vnfDef = request.GET.get('vnfDefinition')
    vnfConfig = request.GET.get('Config')
    vnfParam = request.GET.get('ParameterValuePoint')
    catalogId = request.GET.get('catalogId')

    s = StringIO.StringIO()
    zf = zipfile.ZipFile(s, "w")

    cursor = connections['nfv'].cursor()
    sql = "SELECT * FROM vnf_catalog where catalog_Id=" + str(catalogId)
    cursor.execute(sql)
    results = namedtuplefetchall(cursor)

    for row in results:
        vnfDefPath = str(row.VNFD_Path)
        vnfConfigPath = str(row.VNF_Config_Path)
        vnfParamPath = str(row.VNF_Param_Path)
        vnfDefName = str(row.VNFD_Filename)
        vnfConfigName = str(row.VNF_Config_Filename)
        vnfParamName = str(row.VNF_Param_Filename)

    if vnfDef == 'true':
        if os.path.isfile(vnfDefPath):
            zf.write(vnfDefPath)
    if vnfConfig == 'true':
        if os.path.isfile(vnfConfigPath):
            zf.write(vnfConfigPath)
    if vnfParam == 'true':
        if os.path.isfile(vnfParamPath):
            zf.write(vnfParamPath)

    zf.close()


    response = HttpResponse(s.getvalue(),content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str("files.zip")

    return response