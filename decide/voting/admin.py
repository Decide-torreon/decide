from django.contrib import admin
from django.utils import timezone


from .models import *

from .filters import StartedFilter


def start(modeladmin, request, queryset):
    for v in queryset.all():
        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()


def stop(ModelAdmin, request, queryset):
    for v in queryset.all():
        v.end_date = timezone.now()
        v.save()


def tally(ModelAdmin, request, queryset):
    for v in queryset.filter(end_date__lt=timezone.now()):
        token = request.session.get('auth-token', '')
        v.tally_votes(token)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption


class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionOptionInline]


class VotingAdmin(admin.ModelAdmin):
    list_display = ('name', 'category','start_date', 'end_date')
    readonly_fields = ('start_date', 'end_date', 'pub_key',
                       'tally', 'postproc')
    date_hierarchy = 'start_date'
    list_filter = (StartedFilter,)
    search_fields = ('name', 'category',)

    actions = [ start, stop, tally ]


 
class MultiOptionLine(admin.TabularInline):
    model = MultiOption
    extra = 1
class MultiQuestionLine(admin.TabularInline):
    model = MultiQuestion
    extra = 1
class MultiVotingAdmin(admin.ModelAdmin):
    list_display=('id','title','desc','numberMultiQuestion')
    lines =[MultiQuestionLine]
    actions = [ start, stop]

class MultiQuestionAdmin(admin.ModelAdmin):
    list_display = ('id','multiVoting','question','number_Options','countMultiOption')
    lines =[MultiOptionLine]

class MultiOptionAdmin(admin.ModelAdmin):
    list_display = ('id','option','numberVoted','multiQuestion')


admin.site.register(Voting, VotingAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(MultiVoting, MultiVotingAdmin)
admin.site.register(MultiQuestion,MultiQuestionAdmin)
admin.site.register(MultiOption, MultiOptionAdmin)

