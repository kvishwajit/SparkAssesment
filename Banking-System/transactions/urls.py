from django.urls import path

from .views import DepositMoneyView, WithdrawMoneyView, TransactionRepostView
from .views import export_csv

app_name = 'transactions'


urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionRepostView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("report/export_csv/", export_csv),

]
