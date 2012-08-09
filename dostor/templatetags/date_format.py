# This Python file uses the following encoding: utf-8
import os, sys
import pytz
from django import template
from datetime import datetime
register = template.Library()

def format(date):
    if date:
      diff = datetime.now(pytz.utc) - date
      if diff.days < 3 and diff.days > 1:
          return "منذ " +str(diff.days) + " يوم"
      elif diff.days < 1 and diff.seconds/3600 > 1:
          return "منذ " + str(diff.seconds/3600) + " ساعه "
      elif diff.seconds/3600 < 1:
          return "منذ " + str(diff.seconds%3600/60) + " دقيقه"
      else:
        months = {1:"يناير", 2:"فبراير", 3:"مارس", 4:"إبريل", 5:"مايو", 6:"يونيو", 7:"يوليو", 8:"أغسطس", 9:"سبتمبر", 10:"أكتوبر", 11:"نوفمبر", 12:"ديسمبر"}
        return str(date.hour)+":"+str(date.minute)+" دقيقه, "+str(date.day)+"," + months[date.month] +"," +str(date.year)
format = register.filter(format)