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
import requests

def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def index(request):
    cursor = connections['nfv'].cursor()
    sql = "SELECT User_Id, User_Type,First_Name FROM vnf_user"
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
    vm_image_url=''
    vnfDefName=''
    cursor = connections['nfv'].cursor()
    print '1'
    for id in d:
        print '12'
        sql = 'select * from vnf_catalog where Catalog_Id='+str(id)

        cursor.execute(sql)
        results = namedtuplefetchall(cursor)
        for row in results:
            vnfDefPath = str(row.VNFD_Path)
            vnfConfigPath = str(row.VNF_Config_Path)
            vnfParamPath = str(row.VNF_Param_Path)
            vnfDefName = str(row.VNFD_Filename)
            vnfConfigName = str(row.VNF_Config_Filename)
            vnfParamName = str(row.VNF_Param_Filename)
            vm_image_url = str(row.VM_Image_Path)

        vnfd_heat_path = 'None'
        vnd_config_heat_path = 'None'
        vnf_param_heat_path = 'None'
        if vnfDefPath!= 'None':
            vnfd_heat_path = translate_local(vnfDefPath, vnfDefName)
            vnfd_heat_path = vnfd_heat_path.replace("\\", "\\\\")
        if vnfConfigPath!= 'None':
            vnd_config_heat_path = translate_local(vnfConfigPath, vnfConfigName)
            vnd_config_heat_path = vnd_config_heat_path.replace("\\", "\\\\")
        if vnfParamPath!= 'None':
            vnf_param_heat_path = translate_local(vnfParamPath, vnfParamName)
            vnf_param_heat_path = vnf_param_heat_path.replace("\\", "\\\\")


        sql = "update vnf_catalog set status = 'A', VNFD_Path_Heat='"+vnfd_heat_path+"', VNF_Config_Heat='"+vnd_config_heat_path+"', VNF_Param_Heat='"+vnf_param_heat_path+"' where catalog_Id=" + str(id) + ""
        print 'sql:' + sql
        cursor.execute(sql)
        cursor.close()

    print 'Invoking Openstack Auth API......'
    for row in results:
      env_ip = str(row.env_ip)
      user = str(row.user)
      password = str(row.password)
      tenant = str(row.tenant)

      data = {"auth": {"tenantName":tenant, "passwordCredentials": {"username": user, "password": password}}}
      headers = {'Content-type': 'application/json','Accept':'application/json'}
      data_json = json.dumps(data)
      response = requests.post('http://'+ env_ip +':35357/v2.0/tokens', data=data_json, headers=headers)
      print(response.text)
      response = response.json()
      auth_token = response["access"]["token"]["id"]
      print auth_token

      print 'Invoking List All tenants......'

    # List all Tenants
      headers = {'Content-type': 'application/json','Accept':'application/json','X-Auth-Token': auth_token}
      response = requests.get('http://'+ env_ip +':35357/v2.0/tenants' , headers=headers)

      tenant_response = response.json()
      tenant_details = tenant_response["tenants"]

      print str(tenant_details)
      tenant_id = ''
      for tenant in tenant_details:
        if tenant["name"] == 'demo':
            tenant_id = tenant["id"]


    imageFormat = 'raw'
    containerFormat = 'bare'
    print vm_image_url
    print vnfDefName
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-Auth-Token': auth_token,
               'x-glance-api-copy-from': vm_image_url, 'x-image-meta-name': vnfDefName, 'x-image-meta-disk_format': imageFormat,
               'x-image-meta-container_format': containerFormat}
    response = requests.post('http://' + env_ip + ':9292/v1/images', headers=headers)
    print response.status_code
    print response.json()

    retrieveSQL = "select vnfd_content from vnf_catalog where catalog_Id='"+catalogId+"'"
    cursor.execute(retrieveSQL)
    vnfdcontent= cursor.fetchone()[0]
    print 'vnfdcontent:' + vnfdcontent
    print 'vnfDefName:'+vnfDefName
    status = CreateVnfdTemplate(vnfDefName,vnfdcontent,env_ip,user,tenant,password,auth_token,catalogId)
    print 'Status of create vnfd template:'+status
        #updateCatalog(id, "A")
    return JsonResponse({'status': 'success', 'catalogId': catalogId})

def CreateVnfdTemplate(vnfdname,vnfdcontent,ip,user,tenant,password,auth_token,catalogId):
    print 'Inside createVNFD Template'
    print vnfdname
    print vnfdcontent
    yaml_string = '';
    for line in vnfdcontent.splitlines():
        print line
        line = line.rstrip('\n')
        yaml_string = yaml_string + line + '\\r\\n';
        # data = f.read().replace('\n','')
    print 'YAML_String:' + yaml_string

    ###Creation the VNFD template
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-Auth-Token': auth_token}
    payload = {
	    "auth": {
		"tenantName": tenant,
		"passwordCredentials": {
		    "username": user,
		    "password": password
		}
	    },
	    "vnfd": {
		"service_types": [
		    {
		        "service_type": "vnfd"
		    }
		],
		"mgmt_driver": "noop",
		"infra_driver": "heat",
		"attributes": {
		    "vnfd": vnfdcontent
		},
		"name": vnfdname
	    }
	}
    print '*********************************************************'
    print json.dumps(payload)
    print '*********************************************************'
    print payload

    response = requests.post('http://' + ip + ':8888/v1.0/vnfds', data=json.dumps(payload), headers=headers)


    if response.status_code == 201:
        vnfd_create_response = response.json()
        vnfd_template_id = vnfd_create_response["vnfd"]["id"]
        print "vnfd_template_id:" + str(vnfd_template_id)
        print "vnfd_create_response:" + str(vnfd_create_response)

        cursor = connections['nfv'].cursor()
        updateSql="update vnf_catalog set vnfd_template_id='"+vnfd_template_id+"' where catalog_id='"+catalogId+"'"
        print 'update VNF template sql:'+updateSql
        cursor.execute(updateSql)
        return "success"
    else:
        return "failure"

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

def translate_local(path, file):
    #path = 'c:\\tosca_helloworld.yaml'
    filename, file_extension = os.path.splitext(file)
    filename += `random.random()` + '_heat.yaml'
    obj = TranslatorShell()
    content = obj._translate('tosca', path, {}, True)
    targetpath = 'c:\\folder\\' + filename
    #targetpath = '/home/rdk/files/' + filename
    print path
    with open(targetpath, 'a') as the_file:
        for line in content.splitlines():
            the_file.write(line+'\n')
    return targetpath

@csrf_exempt
def toscaValidate(request):
    path = handle_uploaded_file(request.FILES['path'])
    #obj = ToscaTemplate(path, None, True)
    return JsonResponse({'status': 'success', 'message': 'TOSCA Validation Successful', 'path' : path})
    # if obj.msg == 'success':
    #     return JsonResponse({'status': 'success', 'message': 'TOSCA Validation Successful', 'path' : path})
    # else:
    #     return JsonResponse({'status': 'failed', 'message': obj.msg})

@csrf_exempt
def uploadImage(request):
    path = handle_uploaded_file(request.FILES['path'])
    return JsonResponse({'status': 'success', 'path': path})

#def handle_uploaded_file(f):
#    print f.name
#    extension = f.name.split('.')[-1]
#    filename = f.name +`random.random()` + '.' + extension
#    #path = '/home/rdk/files/' + filename
#    path = 'c:\\folder\\' + filename
#    with open(path, 'wb+') as destination:
#        for chunk in f.chunks():
#            destination.write(chunk)
#    return path

def handle_uploaded_file(f):

     print f.name

     #extension = f.name.split('.')[-1]
     #filename = f.name +`random.random()` + '.' + extension
      #path = '/home/rdk/files/' + filename
     path = 'c:\\folder\\' + f.name
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
def create_vnf_catalog(request, ):
    print '\n' + 'Inside Create VNF Catalog...'
    received_json_data = json.loads(request.body)
    catalogName = received_json_data['vnfName']
    catalogDesc = received_json_data['vnfDesc']
    vmImageFile = received_json_data['imgLoc']
    vnfdFilename = received_json_data['vnfDefinitionName']
    vnfdCfgFilename = received_json_data['configName']
    vnfdParamFilename = received_json_data['parameterValuePointName']
    vnfdFilePath = received_json_data['vnfDefinitionPath']
    vnfdCfgFilePath = received_json_data['configPath']
    vnfdParamPath = received_json_data['parameterValuePointPath']
    vmImagePath = received_json_data['imagePath']
    vmImageName = received_json_data['imageName']


    vnfdFilePath = str(vnfdFilePath).replace("\\", "\\\\")
    vnfdCfgFilePath = str(vnfdCfgFilePath).replace("\\", "\\\\")
    vnfdParamPath = str(vnfdParamPath).replace("\\", "\\\\")
    vmImagePath = str(vmImagePath).replace("\\", "\\\\")

    cursor = connections['nfv'].cursor()
    status = 'P'
    sql = "INSERT INTO vnf_catalog(Catalog_Name, Catalog_Desc,VM_Imagefile, VNFD_Filename, VNF_Config_Filename , VNF_Param_Filename, Status, VNFD_Path, VNF_Config_Path, VNF_Param_Path, VM_Image_Path) " + "VALUES ('" + catalogName + "','" + catalogDesc + "','" + vmImageFile + "','" + vnfdFilename + "','" + vnfdCfgFilename + "','" + vnfdParamFilename + "','" + status + "' ,'" + vnfdFilePath + "','" + vnfdCfgFilePath + "','" + vnfdParamPath + "','" + vmImagePath + "')"
    print 'sql:' + sql
    cursor.execute(sql)

    # Query to fetch Catalog_Id to the user
    retrieveSql = "SELECT Catalog_Id FROM vnf_catalog where Catalog_Name='" + catalogName + "'";
    print retrieveSql
    cursor.execute(retrieveSql)
    results = namedtuplefetchall(cursor)

    catalogId= ''
    for row in results:
        catalogId = str(row.Catalog_Id)
        print "Catalog Id: " + catalogId

    envDetailsSql ="SELECT * from vnf_env where id=1"
    cursor.execute(envDetailsSql)
    results = namedtuplefetchall(cursor)

    print 'Invoking Openstack Auth API......'
    for row in results:
      env_ip = str(row.env_ip)
      user = str(row.user)
      password = str(row.password)
      tenant = str(row.tenant)

      data = {"auth": {"tenantName":tenant, "passwordCredentials": {"username": user, "password": password}}}
      headers = {'Content-type': 'application/json','Accept':'application/json'}
      data_json = json.dumps(data)
      response = requests.post('http://'+ env_ip +':35357/v2.0/tokens', data=data_json, headers=headers)
      print(response.text)
      response = response.json()
      auth_token = response["access"]["token"]["id"]
      print auth_token

      print 'Invoking List All tenants......'

    # List all Tenants
      headers = {'Content-type': 'application/json','Accept':'application/json','X-Auth-Token': auth_token}
      response = requests.get('http://'+ env_ip +':35357/v2.0/tenants' , headers=headers)

      tenant_response = response.json()
      tenant_details = tenant_response["tenants"]

      print str(tenant_details)
      tenant_id = ''
      for tenant in tenant_details:
        if tenant["name"] == 'demo':
            tenant_id = tenant["id"]

      headers = {'X-Auth-Token': auth_token}
      print 'vmImagePath:'+ str(vmImagePath)
      data = open(vmImagePath, 'rb').read()
      url ="http://"+ env_ip +":8080/v1/AUTH_"+tenant_id+"/nfv/"+vmImageName
      r = requests.put(url, data=data, headers=headers)
      print r.status_code
      print r.content

      print 'Updating the swift object URL inside the vnf_catalog'
      updateImagePathSql = "update vnf_catalog set vm_image_path='"+url+"' where catalog_id="+catalogId
      print 'updateImagePathSql:'+ updateImagePathSql
      cursor.execute(updateImagePathSql)

    if vnfdFilePath != 'None':
     print 'vnfdFilePath:'+vnfdFilePath
     vnfData = getFileContent(vnfdFilePath)
     updateSql = "update vnf_catalog set vnfd_content =%s where catalog_Id=%s";
     args = (vnfData,catalogId)
     cursor.execute(updateSql,args)
    if vnfdParamPath != 'None':
     print 'vnfdParamPath:' +vnfdParamPath
     vnfdParamData = getFileContent(vnfdParamPath)
     updateSql = "update vnf_catalog set vnf_param_content =%s where catalog_Id=%s";
     args = (vnfdParamData,catalogId)
     cursor.execute(updateSql,args)
    if vnfdCfgFilePath != 'None':
     print 'vnfdCfgFilePath:' +vnfdCfgFilePath
     vnfdCfgData = getFileContent(vnfdCfgFilePath)
     updateSql = "update vnf_catalog set vnf_cfg_content =%s where catalog_Id=%s";
     args = (vnfdCfgData,catalogId)
     cursor.execute(updateSql,args)

    return JsonResponse({'CatalogId': catalogId})


def getFileContent(filename):
 with open(filename, 'rb') as f:
  filecontent = f.read()
  return filecontent

def write_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(data)

@api_view(['GET', 'POST'])
@parser_classes((JSONParser,))
def list_vnf_catalog(request):
    print 'Inside VNF Catalog...'

    cursor = connections['nfv'].cursor()
    if request.method == 'GET':
        sql = "SELECT Catalog_Id, Catalog_Name, Catalog_Desc, VM_ImageFile, VNFD_Filename, VNF_Config_Filename , VNF_Param_Filename FROM vnf_catalog where Status='P'"
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
        sql = "SELECT Catalog_Id, Catalog_Name, Catalog_Desc, VM_ImageFile, VNFD_Filename, VNF_Config_Filename , VNF_Param_Filename, vnfd_template_id FROM vnf_catalog where Status='A'"
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
            vnfd_template_id = str(row.vnfd_template_id)
            jsonobj = {'CatalogId': catalog_id, 'CatalogName': catalog_name, 'CatalogDesc': catalog_Desc,
                       'VM_ImageFile': vm_image_file, 'VNFD_Filename': vnfd_filename,
                       'VNF_Config_Filename': vnf_cfg_filename, 'VNF_Param_Filename': vnf_param_filename, 'vnfd_template_id': vnfd_template_id}

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
def upload_vnf_file(request):
    received_json_data = json.loads(request.body)

    catalogId = received_json_data['vnfId']
    vnfdFilename = received_json_data['vnfDefinitionName']
    vnfdCfgFilename = received_json_data['configName']
    vnfdParamFilename = received_json_data['parameterValuePointName']
    vnfdFilePath = received_json_data['vnfDefinitionPath']
    vnfdCfgFilePath = received_json_data['configPath']
    vnfdParamPath = received_json_data['parameterValuePointPath']

    vnfdFilePath = str(vnfdFilePath).replace("\\", "\\\\")
    vnfdCfgFilePath = str(vnfdCfgFilePath).replace("\\", "\\\\")
    vnfdParamPath = str(vnfdParamPath).replace("\\", "\\\\")

    print 'Inside upload_vnf_file...'
    sql = "update vnf_catalog set "

    cursor = connections['nfv'].cursor()

    if vnfdFilename != 'None' and vnfdCfgFilename != 'None' and vnfdParamFilename != 'None':
        print '***********************************************************************************  '
        sql += "VNFD_Filename='" + vnfdFilename + "',VNFD_Path='" + vnfdFilePath + "',VNF_Config_Filename='" + vnfdCfgFilename + "',VNF_Config_Path='" + vnfdCfgFilePath + "', VNF_Param_Filename='" + vnfdParamFilename + "',VNF_Param_Path='" + vnfdParamPath + "'"
    elif vnfdFilename != 'None' and vnfdCfgFilename != 'None':
        sql += "VNFD_Filename='" + vnfdFilename + "',VNFD_Path='" + vnfdFilePath + "',VNF_Config_Filename='" + vnfdCfgFilename + "',VNF_Config_Path='" + vnfdCfgFilePath + "'"
    elif vnfdFilename != 'None' and vnfdParamFilename != 'None':
        sql += "VNFD_Filename='" + vnfdFilename + "',VNFD_Path='" + vnfdFilePath + "', VNF_Param_Filename='" + vnfdParamFilename + "',VNF_Param_Path='" + vnfdParamPath + "'"
    elif vnfdCfgFilename != 'None' and vnfdParamFilename != 'None':
        sql += "VNF_Config_Filename='" + vnfdCfgFilename + "',VNF_Config_Path='" + vnfdCfgFilePath + "', VNF_Param_Filename='" + vnfdParamFilename + "',VNF_Param_Path='" + vnfdParamPath + "'"
    elif vnfdFilename != 'None':
        sql += "VNFD_Filename='" + vnfdFilename + "',VNFD_Path='" + vnfdFilePath + "'"
    elif vnfdCfgFilename != 'None':
        sql += "VNF_Config_Filename='" + vnfdCfgFilename + "',VNF_Config_Path='" + vnfdCfgFilePath + "'"
    if vnfdParamFilename != 'None':
        sql += "VNF_Param_Filename='" + vnfdParamFilename + "',VNF_Param_Path='" + vnfdParamPath + "'"

    sql += " where Catalog_Id='" + catalogId + "'"
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

@api_view(['POST'])
def listInstances(request):
    print "Inside the listInstances API"
    ip = '176.126.90.128'
    # Creating auth_token
    data = {"auth": {"tenantName": "demo", "passwordCredentials": {"username": "admin", "password": "demo"}}}
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    data_json = json.dumps(data)
    response = requests.post('http://' + ip + ':35357/v2.0/tokens', data=data_json, headers=headers)

    # Print(response.text)
    response = response.json()
    auth_token = response["access"]["token"]["id"]
    print auth_token

    # List all Tenants
    headers = {'Content-type': 'application/json','Accept':'application/json','X-Auth-Token': auth_token}
    response = requests.get('http://'+ ip +':35357/v2.0/tenants' , headers=headers)

    tenant_response = response.json()
    tenant_details = tenant_response["tenants"]

    print str(tenant_details)

    tenant_id = 'f1b2b1e196874e9e9e8c24dbfe0ac072'

    # List all stack

    #headers = {'Content-type': 'application/json','Accept':'application/json','X-Auth-Token': auth_token}
    #response = requests.get('http://'+ ip +':8004/v1/' + tenant_id + '/stacks' , headers=headers)

    #stack_response = response.json()

    #print stack_response

    # List all servers

    headers = {'Content-type': 'application/json','Accept':'application/json','X-Auth-Token': auth_token}
    response = requests.get('http://'+ ip +':8774/v2/' + tenant_id + '/servers' , headers=headers)

    server_response = response.json()
    print server_response
    return JsonResponse(server_response)

@api_view(['POST'])
def listHypervisors(request):
    print "Inside the listHypervisors API"
    ip = '31.220.67.128'

    # Creating auth_token
    data = {"auth": {"tenantName": "demo", "passwordCredentials": {"username": "admin", "password": "demo"}}}
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    data_json = json.dumps(data)
    response = requests.post('http://' + ip + ':35357/v2.0/tokens', data=data_json, headers=headers)

    # Print(response.text)
    response = response.json()
    auth_token = response["access"]["token"]["id"]
    print auth_token

    tenant_id = 'f1b2b1e196874e9e9e8c24dbfe0ac072'

    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-Auth-Token': auth_token}
    response = requests.get('http://' + ip + ':8774/v2/' + tenant_id + '/os-hypervisors', headers=headers)

    hyp_response = response.json()

    return JsonResponse(hyp_response)


@api_view(['GET'])
def migrateVM(request):
    print "Inside the migrate VM API"
    ip = '31.220.67.128'

    # Creating auth_token
    data = {"auth": {"tenantName": "demo", "passwordCredentials": {"username": "admin", "password": "demo"}}}
    headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
    data_json = json.dumps(data)
    response = requests.post('http://' + ip + ':35357/v2.0/tokens', data=data_json, headers=headers)

    # Print(response.text)
    response = response.json()
    auth_token = response["access"]["token"]["id"]
    print auth_token
    response = requests.post('http://' + ip + ':35357/v2.0/tokens', data=data_json, headers=headers)
    headers = {'Content-type': 'application/json','Accept':'application/json','X-Auth-Token': auth_token}

    server_id = request.GET.get('server_id')
    print 'server_id'+str(server_id)

    tenant_id = 'f1b2b1e196874e9e9e8c24dbfe0ac072'
    #tenant_id = '9ec3405d16454da28277493f2fd82e31'
    host = request.GET.get('host')

    print 'host'+str(host)

    #host = 'Compute1'
    payload = { "os-migrateLive": {
        "host": host,
        "block_migration": True,
        "disk_over_commit": False}
    }
    response = requests.post('http://'+ ip +':8774/v2.1/'+ tenant_id + '/servers/' + server_id + '/action' ,data=json.dumps(payload),headers=headers)
    status = response.status_code
    print status
    #response = response.json()
    if status ==202:
        print 'Live Migration Success...'
        return JsonResponse({"status":"success"})
    else:
        print 'Live Migration Failure... Status Code:'+status
        return JsonResponse({"status":"failure"})


@api_view(['GET'])
def listEnvironments(request):
    print 'Inside list environments API'
    cursor = connections['nfv'].cursor()
    sql = "SELECT env_ip, env_desc FROM vnf_env"
    print 'sql:' + sql
    cursor.execute(sql)
    results = namedtuplefetchall(cursor)
    json_res = []
    for row in results:
            env_ip = str(row.env_ip)
            env_desc= str(row.env_desc)
            print "Environment IP: " + env_ip
            print "Environment desc:"+ env_desc
            jsonobj = {'Environment_ip': env_ip, 'Environment_Desc': env_desc}
            json_res.append(jsonobj)

    print 'JsonResponse:' + str(json_res)
    return JsonResponse(json_res, safe=False)


def DeployVnfdTemplate(request):
    # Creation of VNF Image using template ID
    vnfd_template_id = request.GET.get('vnfTemplateId')
    vnfd_name = request.GET.get('vndfname')

    ip = ''
    user = ''
    tenant = ''
    password = ''

    cursor = connections['nfv'].cursor()
    envDetailsSql ="SELECT * from vnf_env where id=1"
    cursor.execute(envDetailsSql)
    results = namedtuplefetchall(cursor)

    print 'Invoking Openstack Auth API......'
    for row in results:
        ip = str(row.env_ip)
        user = str(row.user)
        password = str(row.password)
        tenant = str(row.tenant)

    data = {"auth": {"tenantName":tenant, "passwordCredentials": {"username": user, "password": password}}}
    headers = {'Content-type': 'application/json','Accept':'application/json'}
    data_json = json.dumps(data)
    response = requests.post('http://'+ ip +':35357/v2.0/tokens', data=data_json, headers=headers)
    response = response.json()
    auth_token = response["access"]["token"]["id"]
    print auth_token

    print "auth token:" + auth_token
    headers = {'Content-type': 'application/json', 'Accept': 'application/json', 'X-Auth-Token': auth_token}

    vnf_image_payload = {
        "auth": {
            "tenantName": tenant,
            "passwordCredentials": {
                "username": user,
                "password": password
            }
        },
        "vnf": {
            "vnfd_id": vnfd_template_id,
            "name": vnfd_name
        }
    }

    print vnf_image_payload

    response = requests.post('http://' + ip + ':8888/v1.0/vnfs', data=json.dumps(vnf_image_payload),
                                       headers=headers)
    vnf_image_response = response.json()
    print "List create VNF response:" + str(vnf_image_response)

    print response.status_code
    print response
    if response.status_code == 201:
        return JsonResponse({"status":"success"})
    else:
        return JsonResponse({"status": "failed"})
