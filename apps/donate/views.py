from django.shortcuts import render
from donate.models import prj_development,project
from django.views.generic.base import View
from django.http import HttpResponse,HttpResponseRedirect
from alipay import AliPay
from donate.models import Donation_log
from alipay import ISVAliPay
from userinfo.models import UserMessage
import uuid
from django.template import loader,RequestContext
from django.db.models import Q
from news.models import News
import time
from django.conf import settings
from django.contrib import messages
import os
import re
# Create your views here.

class CrowdFundingDisplay(View):
    def get(self,request,login_form = {}):

        edu = project.objects.filter(proj_class='教育助学', is_display=0, is_delete=1)
        index = edu.latest("project_id")
        index = [i for i in range(index.project_id - 7, index.project_id + 1)]
        edus = []
        for i in range(index.__len__())[::-1]:
            try:
                edu1 = project.objects.get(project_id=index[i])
                edus.append(edu1)
            except Exception:
                pass

        support = project.objects.filter(proj_class='扶贫助困', is_display=0, is_delete=1)
        index2 = support.latest("project_id")
        index2 = [i for i in range(index2.project_id - 7, index2.project_id + 1)]
        supports = []

        for i in range(index2.__len__())[::-1]:
            try:
                support1 = project.objects.get(project_id=index2[i])
                supports.append(support1)
            except Exception:
                pass

        log_index = Donation_log.objects.latest("Donation_log_id")
        index3 = [i for i in range(log_index.Donation_log_id - 5, log_index.Donation_log_id + 1)]
        logs = []

        for i in range(index3.__len__())[::-1]:
            try:
                log = Donation_log.objects.get(Donation_log_id=index3[i])
                logs.append(log)
            except Exception:
                pass

        total_project = project.objects.latest('project_id').project_id
        total_moneys = project.objects.all()
        total_money = 0
        for i in total_moneys:
            total_money = total_money + i.now_money
        total_support = log_index.Donation_log_id
        #新闻
        publish_news = News.objects.filter(is_publish__icontains='publish')
        step = 0
        content = []
        for news in publish_news:
            content.append(news)
            step += 1
            if step >= 6:
                break

        for i in content:
            timeArray = time.strptime(str(i.update_at).split('.')[0], "%Y-%m-%d %H:%M:%S")
            timeStamp = int(time.mktime(timeArray))
            i.update_at = timeStamp
            i.image = '/media/' + str(i.image)

        for i in range(0, len(content)):
            for j in range(i + 1, len(content)):
                if content[i].created_at <= content[j].created_at:
                    content[i], content[j] = content[j], content[i]

        crowdfunding_form = {
            'supports': supports, 'edus': edus,
            'logs': logs,
            'tatal_project': total_project,
            'total_money': total_money, 'total_support': total_support,
            'news': content}
        try:
            username = request.session["username"]
            login_form = {"logined": "1", "msg": username}
        except:
            pass
        all_form = dict(crowdfunding_form,**login_form)

        if  request.GET.get('login_out') == '1':
            try:
                del request.session['username']
            except:
                pass
            return HttpResponseRedirect('/crowdfunding')
        return render(request,'crowdfunding.html',all_form)
        # except Exception:
        #     return HttpResponse("请求的页面不存在")

    def post(self,request):
        user_name = request.POST.get("username")
        pass_word = request.POST.get("password")

        if user_name == "":
            login_from = {"logined": "0", "msg": "用户名不能为空"}
            return CrowdFundingDisplay.get(self,request,login_from)
        elif pass_word == "":
            login_from = {"logined": "0", "msg": "密码不能为空"}
            return CrowdFundingDisplay.get(self,request,login_from)
        else:
            name_pw_massage = UserMessage.objects.filter(username=user_name)
            email_pw_massage = UserMessage.objects.filter(email=user_name)
            if name_pw_massage:
                for name_pw_msg in name_pw_massage:
                    pw = name_pw_msg.password
                if pw == pass_word:
                    request.session["username"] = user_name
                    login_from = {"logined": "1", "msg": user_name}
                else:
                    login_from = {"logined": "0", "msg": "密码错误"}

            elif email_pw_massage:
                for email_pw_msg in email_pw_massage:
                    pw = email_pw_msg.password
                if pw == pass_word:
                    request.session["username"] = user_name
                    login_from = {"logined": "1", "msg": user_name}
                else:
                    login_from = {"logined": "0", "msg": "密码错误"}
            else:
                login_from = {"logined": "0", "msg": "用户名不存在"}

            return CrowdFundingDisplay.get(self, request, login_from)


class Donate(View):

    def get(self,request):
        Donate.project_id = 2
        Donate.subject = ''
        if len(str(request)) < 100:
            # try:
            Donate.project_id = int(request.GET.get("project_id"))
            item = project.objects.get(project_id=Donate.project_id)
            develoment = prj_development.objects.filter(name_id=Donate.project_id)
            percent = '{:.0f}'.format((item.now_money/item.target_money)*100)
            if int(percent) > 100:
                percent = '100'
            project.objects.filter(project_id=Donate.project_id).update(see_num=(item.see_num+1))
            Donate.subject = item.name
            try:

                username = request.session["username"]
                user_hand_portrait = UserMessage.objects.get(username = username).user_hand_portrait
                return render(request,'oncedonate.html',{'item':item,
                                                         'develoment':develoment,
                                                         'percent':percent,
                                                         'username':username,
                                                         'user_hand_portrait':user_hand_portrait})
            except:
                return render(request, 'oncedonate.html', {'item': item,
                                                           'develoment': develoment,
                                                           'percent': percent,
                                                           'username': "未登录",
                                                           'user_hand_portrait': '../media/user_hand_portrait/default.png'
                                                           })

            # except Exception:
            #     return HttpResponse('请求的页面不在哦')
        else:
            '''
            更新数据库
            '''
            try:
                username = request.session['username']
            except Exception:
                pass
            try:
                user_id = UserMessage.objects.get(username=username).id
            except Exception:
                user_id = 1
            money_count =  float(request.GET.get("total_amount"))
            project_id = int(request.GET.get("project_id"))
            Donation_log.objects.create(project_id=project_id,Donation_name_id = user_id,donate_money = money_count)
            item = project.objects.get(project_id=project_id)
            b= Donate.project_id
            a = item.now_money
            now_money = (item.now_money + money_count)
            project.objects.filter(project_id=project_id).update(people_num=item.people_num + 1)
            project.objects.filter(project_id=project_id).update(now_money = now_money)
            #Donation_log.objects.create(project=item,donate_money=money_count,Donation_name_id=user_id)
            #t1 = loader.get_template('oncedonate.html')

            Donate.project_id = int(request.GET.get("project_id"))
            item = project.objects.get(project_id=Donate.project_id)
            develoment = prj_development.objects.filter(name_id=Donate.project_id)
            percent = '{:.0f}'.format((item.now_money / item.target_money) * 100)
            if int(percent) > 100:
                percent = '100'
            project.objects.filter(project_id=Donate.project_id).update(see_num=(item.see_num + 1))
            Donate.subject = item.name
            try:
                username = request.session["username"]
                user_hand_portrait = UserMessage.objects.get(username = username).user_hand_portrait
                return render(request,'oncedonate.html',{'item':item,
                                                         'develoment':develoment,
                                                         'percent':percent,
                                                         'username':username,
                                                         'user_hand_portrait':user_hand_portrait})
            except:
                return  render(request, 'oncedonate.html',{'item': item,
                                                           'develoment': develoment,
                                                           'percent': percent,
                                                           'username': "未登录",
                                                           'user_hand_portrait': '../media/user_hand_portrait/default.png'})




    def post(self,request):
        Donate.project_id = int(request.GET.get("project_id"))
        item = project.objects.get(project_id=Donate.project_id)
        Donate.subject = item.name

        order = pay(request,Donate.project_id,Donate.subject)

        return HttpResponseRedirect('https://openapi.alipaydev.com/gateway.do?' +order )




def pay(request,project_id,subject):
    '''
    支付宝支付
    :param request:
    :return:
    '''
    app_private_key_string = open("F:\\txy\\alipay_private_key.pem").read()
    alipay_public_key_string = open("F:\\txy\\alipay_public_key.pem").read()
    order_id = str(uuid.uuid1())
    money = float(request.POST.get('money', ''))
    alipay = AliPay(
        appid='2016091800539997',
        app_notify_url=None,
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",
        debug=True
    )
    #subject = "测试订单"
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order_id,
        total_amount=money,
        subject=subject,
        return_url="http:127.0.0.1:8000/oncedonate/?project_id="+str(project_id),
        #notify_url="https://example.com/notify"  # 可选, 不填则使用默认notify url
    )
    return order_string

# class donateLog(View):
#     def get(self,request):
#         return HttpResponse(request)

class Personal(View):
    def get(self,request):
        if request.GET.get('login_out') == '1':
            del request.session['username']
            return render(request, "crowdfunding.html", {})
        #user_id = request.uesr.id
        try:
            username = request.session['username']
        except:
            return CrowdFundingDisplay.get(self,request)
        user_id = UserMessage.objects.get(username=username).id
        projects = project.objects.filter(user_name_id = user_id,state = 1)
        project_num = projects.__len__()
        percents = []
        for item in projects:
            num = '{:.0f}'.format((item.now_money/item.target_money)*100)
            if int(num) > 100:
                num = '100'
            percents.append(num)

        helps = Donation_log.objects.filter(Donation_name_id = user_id)
        help_num = helps.__len__()
        audit_projects = project.objects.filter(Q(user_name_id = user_id)&(Q(state=0)|Q(state=2)))
        audit_project_num = audit_projects.__len__()
        all = zip(projects,percents)
        try:
            project_id = request.GET.get('project_id')
            project.objects.filter(project_id = project_id).update(is_delete = 0)
            username = request.session['username']
            user_id = UserMessage.objects.get(username=username).id
            projects = project.objects.filter(user_name_id=user_id, state=1)
            project_num = projects.__len__()
            percents = []
            for item in projects:
                num = '{:.0f}'.format((item.now_money / item.target_money) * 100)
                if int(num) > 100:
                    num = '100'
                percents.append(num)

            helps = Donation_log.objects.filter(Donation_name_id=user_id)
            help_num = helps.__len__()
            audit_projects = project.objects.filter(Q(user_name_id=user_id) & (Q(state=0) | Q(state=2))&Q(is_delete=1))
            audit_project_num = audit_projects.__len__()
            all = zip(projects, percents)
            all_message = UserMessage.objects.filter(username=username)
            for message in all_message:
                return render(request, 'personal.html', {'audit_projects': audit_projects,
                                                           'all': all,
                                                           "username": username,
                                                           "user_signature": message.user_signature,
                                                           "user_hand_portrait": message.user_hand_portrait,
                                                           'project_num': project_num,
                                                           'help_num': help_num,
                                                           'auid_project_num': audit_project_num,

                                                           })
        except Exception:
            HttpResponse('页面被外星人盗走la')

        return render(request,'personal.html',{'project_num':project_num,'help_num':help_num,
                               'auid_project_num':audit_project_num,'audit_projects':audit_projects,'all':all})
    def post(self,request):
        return HttpResponse('页面被外星人盗走la')

class PersonalCenter(View):
    def get(self,request):
        #user_id = request.user.id
        try:
            username = request.session['username']
        except:
            return CrowdFundingDisplay.get(self,request)

        user_id = UserMessage.objects.get(username=username).id
        projects = project.objects.filter(user_name_id=user_id, state=1,is_delete=1)
        project_num = projects.__len__()
        percents = []
        for item in projects:
            num = '{:.0f}'.format((item.now_money / item.target_money) * 100)
            if int(num) > 100:
                num = '100'
            percents.append(num)
        helps = Donation_log.objects.filter(Donation_name_id=user_id,project__is_delete=1)
        all = zip(projects, percents)
        audit_projects = project.objects.filter(Q(user_name_id=user_id) & (Q(state=0) | Q(state=2)))
        try:
            username = request.session["username"]
            project_id = request.GET.get('project_id')
            project.objects.filter(project_id=project_id).update(is_delete=0)
            user_id = UserMessage.objects.get(username=username).id
            projects = project.objects.filter(user_name_id=user_id, state=1)
            project_num = projects.__len__()
            percents = []
            for item in projects:
                num = '{:.0f}'.format((item.now_money / item.target_money) * 100)
                if int(num) > 100:
                    num = '100'
                percents.append(num)
            helps = Donation_log.objects.filter(Donation_name_id=user_id)
            audit_projects = project.objects.filter(Q(user_name_id=user_id) & (Q(state=0) | Q(state=2)) & Q(is_delete=1))
            all = zip(projects, percents)

            all_message = UserMessage.objects.filter(username=username)
            for message in all_message:
                return render(request, 'personalcenter.html', {   'audit_projects': audit_projects,
                                                                   'all': all,
                                                                   "username": username,
                                                                   "user_gender": message.user_gender,
                                                                   "user_signature": message.user_signature,
                                                                   "user_mobile": message.user_mobile,
                                                                   "user_hand_portrait": message.user_hand_portrait,
                                                                  'helps':helps
                                                               })
        except Exception:
            return HttpResponse('页面被外星人盗走la')

        return render(request, 'personalcenter.html', { 'audit_projects': audit_projects, 'all': all})

    def post(self, request):
        # 添加两个错误处理，可以使两个form分开提交
        try:
            username = request.session["username"]

            input_username = request.POST.get("username")
            input_user_signature = request.POST.get("user_signature")
            input_user_mobile = request.POST.get("user_mobile")
            input_user_gender = request.POST.get("user_gender")

            username_list = []
            user_mobile_list = []

            all_message = UserMessage.objects.all()
            for message in all_message:
                username_list.append(message.username)
                user_mobile_list.append(message.user_mobile)

            if input_username != "" and input_username not in username_list and input_username != None:
                UserMessage.objects.filter(username=username).update(username=input_username)
                request.session["username"] = input_username
            if input_user_signature != "" and input_user_signature != None:
                UserMessage.objects.filter(username=username).update(user_signature=input_user_signature)
            if input_user_mobile != "" and input_user_mobile != None and re.search(
                    "^^(13\d|14[57]|15[^4\D]|17[13678]|18\d)\d{8}|170[^346\D]\d{7}",
                    input_user_mobile) is not None and input_user_mobile not in user_mobile_list:
                UserMessage.objects.filter(username=username).update(user_mobile=input_user_mobile)
            if input_user_gender != "" and input_user_gender != None:
                UserMessage.objects.filter(username=username).update(user_gender=input_user_gender)
        except:
            pass

        try:
            if request.method == "POST":
                username = request.session["username"]
                user_hand_portrait = request.FILES['user_hand_portrait']
                user_hand_portrait_path = os.path.join(settings.MEDIA_ROOT, 'user_hand_portrait',
                                                       request.session['username'] + '_hand_portrait.jpg')
                with open(user_hand_portrait_path, 'wb') as pic:
                    for c in user_hand_portrait.chunks():
                        pic.write(c)
                UserMessage.objects.filter(username=username).update(
                    user_hand_portrait=os.path.join('user_hand_portrait',
                                                    request.session['username'] + '_hand_portrait.jpg'))
        except:
            pass

        return self.get(request)


