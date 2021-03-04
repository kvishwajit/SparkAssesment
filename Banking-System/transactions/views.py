from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView
from django.http import HttpResponse

from transactions.constants import DEPOSIT, WITHDRAWAL
from transactions.forms import (
    DepositForm,
    TransactionDateRangeForm,
    WithdrawForm,
)
from transactions.models import Transaction
import csv
import datetime


class TransactionRepostView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    form_data = {}

    def get(self, request, *args, **kwargs):
        form = TransactionDateRangeForm(request.GET or None)
        trans = Transaction.objects.filter(id = request.user.id)
        print(trans.values())
        print(request.user.id)
        print(request.session.get('id'))
        if form.is_valid():
            self.form_data = form.cleaned_data

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )
        #print(queryset)

        daterange = self.form_data.get("daterange")
        #print(daterange)

        if daterange:
            queryset = queryset.filter(timestamp__date__range=daterange)
            #print("Query set values: "+str(queryset))

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account,
            'form': TransactionDateRangeForm(self.request.GET or None)
        })


        return context


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transactions:transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })
        #print(context,'*'*20)
        return context


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit Money to Your Account'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        email_user = self.request.user

        if not account.initial_deposit_date:
            now = timezone.now()
            next_interest_month = int(
                12 / account.account_type.interest_calculation_per_year
            )
            account.initial_deposit_date = now
            account.interest_start_date = (
                now + relativedelta(
                    months=+next_interest_month
                )
            )

        account.balance += amount
        account.save(
            update_fields=[
                'initial_deposit_date',
                'balance',
                'interest_start_date'
            ]
        )

        send_mail(
            'Deposit Money',
            'thank u for depositing amount {} and Updated balance is {} '.format(amount,self.request.user.account.balance),
            settings.EMAIL_HOST_USER,
            [self.request.user],
            fail_silently=False,
        )

        messages.success(
            self.request,
            f'{amount}$ was deposited to your account successfully'
        )

        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money from Your Account'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        print(self.request.user)

        self.request.user.account.balance -= form.cleaned_data.get('amount')
        self.request.user.account.save(update_fields=['balance'])

        send_mail(
            'Withdraw Money',
            'thank u for amount {} Withdraw  and updated balance is {}'.format(amount,self.request.user.account.balance),
            settings.EMAIL_HOST_USER,
            [self.request.user],
            fail_silently=False,
        )

        messages.success(
            self.request,
            f'Successfully withdrawn {amount}$ from your account'
        )

        return super().form_valid(form)


def export_csv(request):
    print('*'*20)
    User_id = (request.user.id)
    print(request.session.get('account_id'))
    print('*' * 20)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = "attachment"; filename = 'statement'+str(datetime.datetime.now())+'.xlsx'
    write= csv.writer(response)
    write.writerow(['TRANSACTION TYPE','DATE','AMOUNT','BALANCE AFTER TRANSACTION'])
    expenses = Transaction.objects.filter(account_id=User_id)
    print(expenses.values())
    # expenses = queryset.filter(owner=request.user)

    for expense in expenses:
        if expense.transaction_type==1:
            write.writerow(['DEPOSIT', expense.timestamp, expense.amount, expense.balance_after_transaction])
            print('DEPOSIT')
        elif expense.transaction_type==2:
            print('WITHDRAW')
            write.writerow(['WITHDRAW', expense.timestamp, expense.amount, expense.balance_after_transaction])
        #write.writerow([expense.transaction_type, expense.timestamp, expense.amount, expense.balance_after_transaction])
    return response
