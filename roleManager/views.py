from django.http import JsonResponse, HttpResponse
from HR.models import Team, Role, TeamAllowedRoles, SetTeamAllowedRoleRequest, UserTeamRole, ConstValue, Users, SetTeamAllowedRoleRequest, NewRoleRequest
from django.shortcuts import render, redirect
import json
from Utility.APIManager.Portal.register_document import v2 as register_doc_nCode
from Utility.APIManager.Portal.send_document import ver2 as send_doc_nCode
from Utility.Authentication.Utils import (
    V1_PermissionControl as permission_control,
    V1_get_data_from_token as get_token_data,
    V1_find_token_from_request as find_token
)
import ast


# ################### Views ###################
def setTeamAllowedRoleRequest(request):
    # دریافت اطلاعات کاربر فعلی
    information = get_currentUser_CTO_manager_information(request)

    TEAM = Team.objects.all()
    ROLE = Role.objects.order_by('RoleId')
    ALLOWEDTEAMROLE = list(TeamAllowedRoles.objects.values("TeamCode", "RoleId", "AllowedRoleCount"))
    TEAMNAMES = list(Team.objects.values("TeamName", "TeamCode"))
    ROLENAMES = list(Role.objects.values("RoleName", "RoleId"))
    CURRENTUSER_REQUEST = get_currentUser_request(information["currentUser_nationalCode"])
    CURRENTUSER_REQUEST["Status"] = False

    #محاسبه افرادی که مشغول به کار هستند در آن تیم و سمت
    for item in ALLOWEDTEAMROLE:
        item['EntryCount'] = UserTeamRole.objects.filter(
            TeamCode_id=item['TeamCode'],
            RoleId_id=item['RoleId']
        ).count()
    
    if request.method == "POST":
        document_title = "درخواست سمت های مجاز تیم"
        doc_state = "بررسی مدیر"
        if information["currentUser_role"] != "DEF":
            doc_state = "بررسی مدیر عامل"

        try :
            body_data = json.loads(request.body)
            newRecord = SetTeamAllowedRoleRequest.objects.create(
                TeamAllowedRoles=body_data,
                RequestorId=information["currentUser_nationalCode"],
                ManagerId=information["currentUser_managers"][0],
                CTOId=information["cto_nationalCode"],
                StatusCode="MANREV" if information["currentUser_role"] == "DEF" else "CTOREV"
            )
            RESPONSE = register_send_document(
                information = information,
                newRecord = newRecord,
                document_title = document_title,
                doc_state = doc_state,
            )
            return JsonResponse(RESPONSE)

        except Exception as error:
            return JsonResponse({"Error":True, "Message":"بروز خطا در ایجاد درخواست"})

    return render(request, "roleManager/SetTeamAllowedRoleRequest.html", context={
        "Teams": TEAM,
        "Roles": ROLE,
        "allowedTeam": json.dumps(ALLOWEDTEAMROLE),
        "roleNames": json.dumps(ROLENAMES),
        "teamNames": json.dumps(TEAMNAMES),
        "currentUser_request": CURRENTUSER_REQUEST,
    })

def newRoleRequest(request):
    if request.method == "POST":
        information = get_currentUser_CTO_manager_information(request)
        doc_state = "بررسی مدیر"
        if information["currentUser_role"] != "DEF":
            doc_state = "بررسی مدیر عامل"
        try:
            body_data = json.loads(request.body)
            normalizedText = normalize_persian(body_data["RoleTitle"])
            if Role.objects.filter(RoleName__iexact=normalizedText).exists():
                raise ValueError("نام سمت تکراری میباشد")
            document_title = f"درخواست ایجاد سمت جدید '{body_data["RoleTitle"]}'"
            newRecord = NewRoleRequest.objects.create(
                RoleTitle = body_data["RoleTitle"],
                HasLevel = body_data["HasLevel"],
                HasSuperior = body_data["HasSuperior"],
                AllowedTeams = body_data["AllowedTeams"],
                ConditionsText = body_data["Conditions"],
                DutiesText = body_data["Duties"],
                RequestorId = information["currentUser_nationalCode"],
                ManagerId = information["currentUser_managers"][0],
                CTOId = information["cto_nationalCode"],
                StatusCode="MANREV" if information["currentUser_role"] == "DEF" else "CTOREV"
            )
            RESPONSE = register_send_document(
                information = information,
                newRecord = newRecord,
                document_title = document_title,
                doc_state = doc_state,
            )
            return JsonResponse(RESPONSE)
        except ValueError as error:
            return JsonResponse({"Error": True, "Message": str(error)})
        except Exception as error:
            return JsonResponse({"Error": True, "Message": "بروز خطا در ایجاد درخواست سمت مجاز تیم"})
            
    TEAMS = Team.objects.all()

    return render(request, 'roleManager/newRoleRequest.html', context={
        "teams" : TEAMS,
    })

def showSetTeamAllowedRoleRequest(request, requestID):
    # http://127.0.0.1:8000/RoleManager/AllowRoleTeamRequest/31
    DATA = {
        "error": False,
        "status": "",
        "message": "",
    }

    information = get_currentUser_CTO_manager_information(request)
    REQUEST = SetTeamAllowedRoleRequest.objects.get(id=requestID)
    REQUEST_DATA = ast.literal_eval(REQUEST.TeamAllowedRoles)
    teams = Team.objects.all()
    roles = Role.objects.all()
    for team in REQUEST_DATA:
        team["TeamName"] = teams.filter(TeamCode=team["TeamCode"]).first().TeamName
        for role in team["Roles"]:
            role["RoleName"] = roles.filter(RoleId=role["RoleId"]).first().RoleName

    if request.method == "POST":
        body_data = json.loads(request.body)
        try:
            if body_data["status"] == "AGREE":
                if information["currentUser_role"] == "CTO":
                    for team in REQUEST_DATA:
                        for role in team["Roles"]:
                            teamAllowedRoles_record = TeamAllowedRoles.objects.get(TeamCode=team["TeamCode"],
                                                                                   RoleId=role["RoleId"])
                            teamAllowedRoles_record.AllowedRoleCount = role["RoleCount"]
                            teamAllowedRoles_record.save()
                    REQUEST.StatusCode = "FINSUC"
                    DATA["message"] = "تغییرات با موفقیت ثبت شد"

                elif information["currentUser_role"] == "MAN":
                    REQUEST.StatusCode = "CTOREV"
                    REQUEST.ManagerOpinion = 1
                    REQUEST.save()
                    DATA["message"] = "درخواست با موفقیت تایید شد"
            elif body_data["status"] == "REJECT":
                if information["currentUser_role"] == "CTO":
                    REQUEST.StatusCode = "FINREJ"
                    REQUEST.CTOOpinion = 0
                    DATA["message"] = "درخواست با موفقیت رد شد"
                elif information["currentUser_role"] == "MAN":
                    REQUEST.StatusCode = "FINREJ"
                    REQUEST.ManagerOpinion = 0
                    REQUEST.save()
                    DATA["message"] = "درخواست با موفقیت رد شد"


        except SetTeamAllowedRoleRequest.DoesNotExist:
            DATA["error"] = True
            DATA["message"] = "درخواست مورد نظر یافت نشد"
        except TeamAllowedRoles.DoesNotExist:
            DATA["error"] = True
            DATA["message"] = "اطلاعات نقش تیم مورد نظر یافت نشد"
        except Exception as error:
            DATA["error"] = True
            DATA["message"] = "متاسفانه خطایی رخ داده است"

        return JsonResponse(DATA)
    else:
        if information["error"]:
            DATA["error"] = True
            DATA["message"] = information["message"]
        else:
            match information["currentUser_role"]:
                case "CTO":
                    if REQUEST.StatusCode == "CTOREV":
                        DATA["status"] = "EDIT"
                    else:
                        DATA["status"] = "READONLY"
                case "MAN":
                    if REQUEST.StatusCode == "MANREV":
                        DATA["status"] = "EDIT"
                    else:
                        DATA["status"] = "READONLY"
                case "DEF":
                    if information["currentUser_nationalCode"] == REQUEST.RequestorId:
                        if REQUEST.StatusCode == "DRAFTR":
                            DATA["status"] = "EDIT"
                        else:
                            DATA["status"] = "READONLY"
                    else:
                        DATA["error"] = True
                        DATA["message"] = "متاسفانه شما میتوانید فقط درخواست های خود را مشاهده کنید"
    DATA["status"] = "EDIT"

    return render(request, 'roleManager/showRequest.html', context={
        "request": REQUEST,
        "requestData": REQUEST_DATA,
        'data': json.dumps(DATA),
    })

def showNewRoleRequest(request, requestID):
    PERMISION_DATA = {
        "error": False,
        "status": "",
        "message": "",
    }

    information = get_currentUser_CTO_manager_information(request)
    REQUEST = NewRoleRequest.objects.get(id=requestID)
    request_data = ast.literal_eval(REQUEST.AllowedTeams)
    teams = Team.objects.all()
    for team in request_data:
        team["TeamName"] = teams.filter(TeamCode=team["TeamCode"]).first().TeamName
    REQUEST.AllowedTeams = request_data


    if request.method == "POST":
        body_data = json.loads(request.body)
        try:
            if body_data["status"] == "AGREE":
                if information["currentUser_role"] == "CTO":
                    for team in REQUEST_DATA:
                        for role in team["Roles"]:
                            teamAllowedRoles_record = TeamAllowedRoles.objects.get(TeamCode=team["TeamCode"],
                                                                                   RoleId=role["RoleId"])
                            teamAllowedRoles_record.AllowedRoleCount = role["RoleCount"]
                            teamAllowedRoles_record.save()
                    REQUEST.StatusCode = "FINSUC"
                    DATA["message"] = "تغییرات با موفقیت ثبت شد"

                elif information["currentUser_role"] == "MAN":
                    REQUEST.StatusCode = "CTOREV"
                    REQUEST.ManagerOpinion = 1
                    REQUEST.save()
                    DATA["message"] = "درخواست با موفقیت تایید شد"
            elif body_data["status"] == "REJECT":
                if information["currentUser_role"] == "CTO":
                    REQUEST.StatusCode = "FINREJ"
                    REQUEST.CTOOpinion = 0
                    DATA["message"] = "درخواست با موفقیت رد شد"
                elif information["currentUser_role"] == "MAN":
                    REQUEST.StatusCode = "FINREJ"
                    REQUEST.ManagerOpinion = 0
                    REQUEST.save()
                    DATA["message"] = "درخواست با موفقیت رد شد"


        except SetTeamAllowedRoleRequest.DoesNotExist:
            DATA["error"] = True
            DATA["message"] = "درخواست مورد نظر یافت نشد"
        except TeamAllowedRoles.DoesNotExist:
            DATA["error"] = True
            DATA["message"] = "اطلاعات نقش تیم مورد نظر یافت نشد"
        except Exception as error:
            DATA["error"] = True
            DATA["message"] = "متاسفانه خطایی رخ داده است"

        return JsonResponse(DATA)
    else:
        if information["error"]:
            PERMISION_DATA["error"] = True
            PERMISION_DATA["message"] = information["message"]
        else:
            match information["currentUser_role"]:
                case "CTO":
                    if REQUEST.StatusCode == "CTOREV":
                        PERMISION_DATA["status"] = "EDIT"
                    else:
                        PERMISION_DATA["status"] = "READONLY"
                case "MAN":
                    if REQUEST.StatusCode == "MANREV":
                        PERMISION_DATA["status"] = "EDIT"
                    else:
                        PERMISION_DATA["status"] = "READONLY"
                case "DEF":
                    if information["currentUser_nationalCode"] == REQUEST.RequestorId:
                        if REQUEST.StatusCode == "DRAFTR":
                            PERMISION_DATA["status"] = "EDIT"
                        else:
                            PERMISION_DATA["status"] = "READONLY"
                    else:
                        PERMISION_DATA["error"] = True
                        PERMISION_DATA["message"] = "متاسفانه شما میتوانید فقط درخواست های خود را مشاهده کنید"
    
    TEAMS = Team.objects.all()
    return render(request, 'roleManager/showNewRoleRequest.html', context={
        "teams" : TEAMS,
        "request": REQUEST,
        'permisionDataJson': json.dumps(PERMISION_DATA),
        'permisionData': PERMISION_DATA,
    })

# ################### Functions ###################
def get_currentUser_managers_nationalCode(currentUser_username: str) -> list:
    try:
        if not currentUser_username:
            raise ValueError("نام کاربری کاربر فعلی معتبر نمیباشد.")

        managers_nationalCode = []
        UserTeamRole_currentUser_records = UserTeamRole.objects.filter(UserName=currentUser_username)

        if not UserTeamRole_currentUser_records.exists():
            raise ValueError("اطلاعات شما در پایگاه داده موجود نمیباشد")

        for currentUser in UserTeamRole_currentUser_records:
            currentUser_manager = currentUser.ManagerUserName
            manager_nationalCode = currentUser_manager.NationalCode
            if manager_nationalCode not in managers_nationalCode:
                managers_nationalCode.append(manager_nationalCode)

        return managers_nationalCode
    #هر جایی از روند که درست پیش نرفت خطای مناسب اون رو در خروجی قرار میدیم و status رو false میزاریم
    except ValueError as error:
        raise ValueError(str(error))
    except Exception as error:
        raise Exception(f" خطای نامشخص در دریافت مدیران کاربر: {error}")

def register_send_document(information: dict, newRecord, document_title:str, doc_state:str) -> dict:
    # پیامی که به کاربر نشان خواهیم داد
    RESPONSE = {
        "Error": False,
        "Message":"",
    }
    try:
        # ایجاد داکیومنت
        try:
            registerResult = register_doc_nCode(
                app_doc_id=newRecord.id,
                priority="عادی",
                doc_state= doc_state,
                # پیش نویس
                # بررسی مدیر
                # بررسی مدیر عامل
                # رد شده توسط مدیر
                # رد شده توسط مدیر عامل
                # خاتمه موفق
                document_title=document_title,
                app_code="HROARR",
                owner_nationalcode=information["currentUser_nationalCode"]
            )
        except Exception as error:
            raise Exception("بروز خطای نامشخص در ایجاد داکیومنت")
        if "data" not in registerResult or "id" not in registerResult["data"]:
            raise ValueError("خطا در دریافت اطلاعات داکیومنت")


        # ذخیره شماره رکورد داکیومنت در اطلاعات درخواست
        newRecord.DocId = registerResult["data"]["id"]

        # ارسال داکیومنت
        try:
            sendResult = send_doc_nCode(
                doc_id=registerResult["data"]["id"],
                sender_national_code=information["currentUser_nationalCode"],
                inbox_owners_national_code= information["currentUser_managers"][0]
            )
        except Exception as error:
            raise Exception("بروز خطای نامشخص در ارسال داکیومنت")


        # تغییر وضعیت در صورت تطابق کد ملی مدیرعامل با مدیران کاربر
        if information["currentUser_role"] == "DEF":
            newRecord.StatusCode = "MANREV"
        elif information["currentUser_role"] == "MAN":
            newRecord.StatusCode = "CTOREV"
        elif information["currentUser_role"] == "CTO":
            newRecord.StatusCode = "CTOREV"



        # ثبت تغییرات درخواست
        newRecord.save()

        RESPONSE["Message"] = "درخواست با موفقیت ثبت و ارسال شد."
        return RESPONSE

    #خطاهایی که امکان دارن اتفاق بیوفتن
    except ValueError as error:
        print("Hello ValueError")
        RESPONSE["Error"] = True
        RESPONSE["Message"] = str(error)
        return RESPONSE
    #خطاهایی که نامشخص هستند
    except Exception as error:
        RESPONSE["Error"] = True
        RESPONSE["Message"] = str(error)
        return RESPONSE

@permission_control
def get_currentUser_CTO_manager_information(request)->dict:
    information = {
        "error": False,
        "message": "",
        "currentUser_nationalCode": None,
        "currentUser_username": None,
        "cto_nationalCode": None,
        "currentUser_role": "",
        "currentUser_managers" : None
    }
    
    try:
        token = find_token(request)
        if not token:
            raise ValueError("توکن کاربر یافت نشد")
            
        currentUser_nationalCode = get_token_data(token, "user_NationalCode")
        currentUser_username = get_token_data(token, "username")
        
        # دریافت کد ملی مدیرعامل از جدول تنظیمات
        cto_nationalCode = ConstValue.objects.get(Code="allowedrole_cto").Caption
        
        # دریافت لیست کد ملی مدیران کاربر فعلی
        managers_nationalCode = get_currentUser_managers_nationalCode(currentUser_username)
        
        # تکمیل اطلاعات خروجی
        information.update({
            "currentUser_nationalCode": currentUser_nationalCode,
            "currentUser_username": currentUser_username,
            "cto_nationalCode": cto_nationalCode,
            "currentUser_managers": managers_nationalCode,
        })
        
        # تعیین نقش کاربر در سیستم
        if currentUser_nationalCode == cto_nationalCode:
            information["currentUser_role"] = "CTO"  # مدیرعامل
        elif cto_nationalCode in managers_nationalCode:
            information["currentUser_role"] = "MAN"  # مدیر
        else:
            information["currentUser_role"] = "DEF"  # کاربر عادی

        return information

    except ValueError as error:
        information["error"] = True
        information["message"] = str(error)
        return information
    except ConstValue.DoesNotExist:
        information["error"] = True
        information["message"] = "اطلاعات مدیرعامل در سیستم یافت نشد"
        return information
    except Exception as error:
        information["error"] = True
        information["message"] = f"خطای نامشخص در دریافت اطلاعات: {str(error)}"
        return information

def get_currentUser_request(currentUser_NationalCode: str) -> dict:
    RESPONSE = {
        "Status": True,
        "Error": False,
        "Message": "",
        "requestID": None,
    }
    
    try:
        if not currentUser_NationalCode:
            raise ValueError("کد ملی کاربر نامعتبر است")

        # گرفتن تمام درخواست‌های کاربر فعلی
        user_requests = SetTeamAllowedRoleRequest.objects.filter(
            RequestorId=currentUser_NationalCode
        )
        
        # اگر هیچ درخواستی وجود نداشت
        if not user_requests.exists():
            RESPONSE["Status"] = False
            RESPONSE["Message"] = "درخواستی برای کاربر فعلی یافت نشد"
            return RESPONSE
            
        # بررسی وضعیت تمام درخواست‌ها
        COMPLETED_STATUSES = ["FINSUC", "FINREJ", "FAILED"]
        for request in user_requests:
            if request.StatusCode not in COMPLETED_STATUSES:
                RESPONSE["requestID"] = request.id
                RESPONSE["Status"] = True
                RESPONSE["Message"] = "شما یک درخواست باز دارید"
                return RESPONSE
                
        # اگر همه درخواست‌ها تکمیل شده بودند
        RESPONSE["Status"] = False
        RESPONSE["Message"] = "تمام درخواست های کاربر با موفقیت ثبت شده اند"
        return RESPONSE
        
    except ValueError as error:
        RESPONSE["Status"] = False
        RESPONSE["Error"] = True
        RESPONSE["Message"] = str(error)
        return RESPONSE
    except Exception as error:
        RESPONSE["Status"] = False
        RESPONSE["Error"] = True
        RESPONSE["Message"] = f"خطای نامشخص در بررسی درخواست های کاربر فعلی"
        return RESPONSE
    
def normalize_persian(text):
    return (
        text.replace("ي", "ی")
            .replace("ك", "ک")
            .replace("‌", " ")  
            .strip()
    )
    
    
    
    
    



