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
        sql = "SELECT User_Type FROM VNF_User where User_Id='" + userId + "'"
        print 'sql:' + sql
        cursor.execute(sql)
        results = namedtuplefetchall(cursor)
        for row in results:
            userRole = str(row.User_Type)
            print "User Type " + userRole
            return JsonResponse({'UserRole': userRole, 'UserId': userId})
            # elif request.method == 'POST':
            #     #return HttpResponse("Hello Login API post call response...")
            #     return Response({'received data': request.data})

#
# class loginHandler (views.APIView) :
#     def get(self, request, *args, **kwargs):
#         username = kwargs['username']
#         print 'Logged In User:'+username
#         return HttpResponse(username)
