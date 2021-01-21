from django import forms
from .models import Stock, Portfolio


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['ticker']


class PortfolioForm(forms.ModelForm):
    class Meta:

        model = Portfolio
        fields = ['portfolio']
