# coding=utf-8   #默认编码格式为utf-8 
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.forms.models import model_to_dict

from book.models import *
from book.Util.upJiGuang import *
from book.Util.util import *
import simplejson
import random
import datetime
import logging
import sys
#logger = logging.getLogger(__name__)
logger = logging.getLogger("mysite")


def getCurrentTime():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def recordToHistory(user, book_dict):
    if book_dict['action'] == 'borrow':
        if UserCurrentBorrow.checkIsExistThisBook(user.id, book_dict['owner'], book_dict['shop'], book_dict['book'], "borrowing"):
            pass
        else:
            UserCurrentBorrow.createUserCurrentBorrow(user.id, book_dict['owner'], book_dict['shop'], book_dict['book'], "borrowing", book_dict['time'], "", "")

    elif book_dict['action'] == 'accept':
        borrowBook = UserCurrentBorrow.getThisBorrowBook(user.id, book_dict['owner'], book_dict['shop'], book_dict['book'], "borrowing")
        if borrowBook is None:
            logger.info("resp borrow exception")
        else:
            borrowBook.accepttime = book_dict['time']
            borrowBook.state = "borrow"
            borrowBook.save()
        
    elif book_dict['action'] == 'refuse':
        borrowBook = UserCurrentBorrow.getThisBorrowBook(user.id, book_dict['owner'], book_dict['shop'], book_dict['book'], "borrowing")
        if borrowBook is None:
            logger.info("resp borrow exception")
        else:
            borrowBook.accepttime = book_dict['time']
            borrowBook.state = "borrow"
            borrowBook.save()
 
    elif book_dict['action'] == 'return':
        borrowBook = UserCurrentBorrow.getThisBorrowBook(user.id, book_dict['owner'], book_dict['shop'], book_dict['book'], "borrow")
        if borrowBook is None:
            logger.info("return exception")
        else:
            borrowBook.finishtime = book_dict['time']
            borrowBook.state = "finish"
            borrowBook.save()
    else:
        logger.info("no this action")

######################## B O O K #############################	
		
def addBook(request):
    state = "fail" 
    dict = {}

    logger.info(request.POST)
    if request.method == 'POST':
        token = request.POST.get('token', '')
        shopname = request.POST.get('shopname', '')
        bookname = request.POST.get('bookname', '') 
       
        user = User.getUserWithToken(token)
        if user is None:
            state = 'invalid token'
        else:
            shop = Shop.getShopWithNameAndUser(shopname, user.id)
            if shop is None:
                state = 'invalid user shop name'
            else:
                if Book.checkIsExistWithName(shop, bookname):
                    state = 'already have this book in ' + shopname
                else:
                    author = request.POST.get('bookauthor', '')
                    publisher = request.POST.get('bookpublisher', '')
                    detail = request.POST.get('bookcomments', '')
                    isbn = request.POST.get('bookisbn', '')
                    imageurl = request.POST.get('imageurl', '')
                    extlink = request.POST.get('extlink', '')
                    book = Book.createBookRow(bookname, author, publisher, detail, shop.id, 1, isbn, "", imageurl, extlink)
                    shop.Belong_Shop.add(book)
                    shop.changeTag += 1
                    shop.save()
                    state = 'success'

    dict['result'] = state
    json=simplejson.dumps(dict)
    logger.info(dict)
    return HttpResponse(json)


def getBook(request):
    state = "fail"
    dict = {}
    
    logger.info(request.GET)
    if request.method == "GET":
        shopuser = request.GET.get('shopuser', '')
        shopname = request.GET.get('shopname', '')
        bookname = request.GET.get('bookname', '') 

        user = User.getUserWithName(shopuser)
        if user is None:
            state = 'invalid shopuser'
        else:
            shop = Shop.getShopWithNameAndUser(shopname, user.id)
            if shop is None:
                state = 'invalid user shop name'
            else:
                book = Book.getBookWithName(bookname, shop.id)
                dict['book'] = model_to_dict(book)
                state = 'success'
            
    dict['result'] = state
    json=simplejson.dumps(dict)
    logger.info(dict)
    return HttpResponse(json)

def removeBook(request):
    state = "fail" 
    dict = {}
    
    logger.info(request.POST)
    if request.method == "POST":
        token = request.POST.get('token', '')
        shopname = request.POST.get('shopname', '')
        bookname = request.POST.get('bookname', '') 

        user = User.getUserWithToken(token)
        if user is None:
            state = 'invalid token'
        else:
            shop = Shop.getShopWithNameAndUser(shopname, user.id)
            if shop is None:
                state = 'no have this shop in your'
            else:
                Book.objects.filter(name=bookname, shop_id=shop.id).delete()
                shop.changeTag += 1
                shop.save()
                state = 'success'
            
    dict['result'] = state
    json=simplejson.dumps(dict)
    logger.info(dict)
    return HttpResponse(json)


def reqBorrowBook(request):
    state = "fail" 
    dict = {}
    
    logger.info(request.GET)
    if request.method == "GET":
        shopuser = request.GET.get('shopuser', '')
        token = request.GET.get('token', '')
        shopname = request.GET.get('shopname', '')
        bookname = request.GET.get('bookname', '') 
 
        owner = User.getUserWithName(shopuser)
        borrower = User.getUserWithToken(token)
        if owner is None and borrower is None:
            state = 'novalid token'
        else:        
            shop = Shop.getShopWithNameAndUser(shopname, owner.id)
            if shop is None:
                state = 'no have this shop in your'
            else:
                book = Book.getBookWithName(bookname, shop.id)
                curtime = getCurrentTime()
                msgBook = {}
                msg = {}
                action = "borrow"
                msgBook['owner'] = owner.name
                msgBook['shop'] = shopname  # notice hongfei
                msgBook['book'] = bookname
                msgBook['borrower'] = borrower.name
                msgBook['time'] = curtime
                msgBook['action'] = action
                msgList = []
                msgList.append(msgBook)
                msg['messages'] =msgList 
                msg['count'] = 1
                alert =  borrower.name + u'  向你借书： <<'.encode('utf-8').decode('utf-8') + bookname + ">>"
                logger.info(bookname)
                logger.info(alert)
                jpushMessageWithRegId(owner.regid, msg, alert);
                    #userEvent = UserEvent.objects.create(user_id=owner.id, owner=owner.name, borrower=borrower.name, \
                    #        book=bookname, time=curtime, shop=shopname, action="borrow")
#recordToHistory(borrower, model_to_dict(userEvent))
                
                recordToHistory(borrower, {'owner':owner.name,'shop':shopname, 'book':bookname, 'action':action, 'time':curtime})
                state = 'success'
            
    dict['result'] = state
    json=simplejson.dumps(dict)
    logger.info(dict)
    return HttpResponse(json)

def respBorrowAction(request):
    state = "fail"
    dict = {}
    
    logger.info(request.POST)
    if request.method == "POST":
        token = request.POST.get('token', '')
        fromname = request.POST.get('borrower', '')
        shopname = request.POST.get('shopname', '')
        bookname = request.POST.get('bookname', '') 
        action = request.POST.get('action', '') 
 
        borrower = User.getUserWithName(fromname)
        owner = User.getUserWithToken(token)
        if owner is None and borrow is None:
            state = 'novalid token'
        else:        
            shop = Shop.getShopWithNameAndUser(shopname, owner.id)
            if shop is None:
                state = 'no have this shop in your'
            else:
                book = Book.getBookWithName(bookname, shop.id)
                curtime = getCurrentTime() 
                msg = {}
                msgBook = {}
                msgBook['owner'] = owner.name
                msgBook['shop'] = shopname
                msgBook['book'] = bookname
                msgBook['borrower'] = borrower.name
                msgBook['time'] = curtime
                msgBook['action'] = action 
                msgList = []
                msgList.append(msgBook)
                msg['messages'] =msgList 
                msg['count'] = 1
#alert =  owner.name + u'  同意借书请求'.encode('utf-8').decode('utf-8')
                alert =  owner.name + u'  同意借书： <<'.encode('utf-8').decode('utf-8') + bookname + ">>"
                jpushMessageWithRegId(borrower.regid, msg, alert);
                    #userEvent = UserEvent.objects.create(user_id=borrower.id, owner=owner.name, borrower=fromname, book=bookname, time=curtime, shop=shopname, action=action)
#recordToHistory(borrower, model_to_dict(userEvent))
                recordToHistory(borrower, {'owner':owner.name,'shop':shopname, 'book':bookname, 'action':action, 'time':curtime})
                if action == "accept":
                    book.borrower = fromname
                    book.state = 0
                    book.save()
                    shop.changeTag += 1
                    shop.save()

                    state = 'success'
            
    dict['result'] = state
    json=simplejson.dumps(dict)
    logger.info(dict)
    return HttpResponse(json)

def returnBook(request):
    state = "fail"
    dict = {}
    
    logger.info(request.POST)
    if request.method == "POST":
        token = request.POST.get('token', '')
        shopname = request.POST.get('shopname', '')
        bookname = request.POST.get('bookname', '') 
        action = "return"#request.POST.get('action', '') 
 
        owner = User.getUserWithToken(token)
        if owner is None:
            state = 'invalid token'
        else:
            shop = Shop.getShopWithNameAndUser(shopname, owner.id)
            if shop is None:
                state = 'no have this shop in your'
            else:
                book = Book.getBookWithName(bookname, shop.id)
                if book is None: 
                    state = 'no have this book'
                else:
                    borrower = User.getUserWithName(book.borrower)
                    if borrower is None:
                        state = "borrower no exist"
                    else:
                        curtime = getCurrentTime() 
                        recordToHistory(borrower, {'owner':owner.name,'shop':shopname, 'book':bookname, 'action':action, 'time':curtime})
                        book.state = 1
                        book.borrower = ""
                        book.save()
                        shop.changeTag += 1
                        shop.save()

                        state = 'success'
            
    dict['result'] = state
    json=simplejson.dumps(dict)
    logger.info(dict)
    return HttpResponse(json)

def searchBook(request):
    state = None
    dict = {}

    logger.info(request.GET)
    if request.method == 'GET':
        bookname = request.GET.get('bookname', '')		
        if bookname == "*":
            books = Book.objects.all()
        else:
            books = Book.objects.filter(name__contains=bookname);
        if books.count():
            booklist = []
            for book in books:
                book_dict = model_to_dict(book)
                shop = Shop.objects.get(id=book.shop_id) 
                user = User.objects.get(id=shop.user_id) 
                book_dict['shopname'] = shop.name
                book_dict['shopaddr'] = shop.addr
                book_dict['username'] = user.name
                booklist.append(book_dict)
            dict['books'] = booklist
            state = 'success'

    dict['result'] = state
    json=simplejson.dumps(dict)
    logger.info(dict)
    return HttpResponse(json)

def getCurrentBorrowBook(request):
    state = "fail"
    dict = {}

    logger.info(request.GET)
    if request.method == 'GET':
        token = request.GET.get('token', '')
        user = User.getUserWithToken(token)
        if user is None:
            state = 'invalid token'
        else:
            userCurBorrows = UserCurrentBorrow.objects.filter(user_id=user.id).filter(state__contains="borrow")
            userCurBorrowList = []

            for userCurBorrow in userCurBorrows:
                userCurBorrowList.append(model_to_dict(userCurBorrow)) 

            dict['books'] = userCurBorrowList 
            state = 'success'
    
    dict['result'] = state
    json=simplejson.dumps(dict)
    logger.info(dict)
    return HttpResponse(json)

def getHistoryBorrowBook(request):
    state = "fail"
    dict = {}

    logger.info(request.GET)
    if request.method == 'GET':
        token = request.GET.get('token', '')
	
        user = User.getUserWithToken(token)
        if user is None:
            state = 'invalid token'
        else:
            userCurBorrows = UserCurrentBorrow.objects.filter(user_id=user.id).filter(state__contains="finish")
            userCurBorrowList = []
            for userCurBorrow in userCurBorrows:
                userCurBorrowList.append(model_to_dict(userCurBorrow)) 
            dict['books'] = userCurBorrowList 
            state = 'success'
    
    dict['result'] = state
    json=simplejson.dumps(dict)
    logger.info(dict)
    return HttpResponse(json)

