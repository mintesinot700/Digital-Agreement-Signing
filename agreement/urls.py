from django.urls import path
from django.views.generic import RedirectView 
from .views import (    
                        # home, 
                        AgreementCreateView, 
                        AgreementDetailView , 
                        AgreementListView,
                        pdf_file_view,
                        Pdf_agreementCreateView,
                        Pdf_agreementUpdateDestroyView,
                        Pdf_agreementListView,
                                                )

# Account urls.py
urlpatterns=[
    
   # path for agreement
   path('agreement/', AgreementCreateView.as_view(), name="agreement-create"),
   path('agreement_list/', AgreementListView.as_view(), name="agreement-list"),   
   path('agreement/<int:pk>/', AgreementDetailView.as_view(), name="agreement-datail"),

   # paths for pdf_agreements
   path('pdf/<int:pk>/', pdf_file_view, name='pdf_file_view'),
   path('pdf_agreement/', Pdf_agreementListView.as_view(), name="Pdf_agreement-Create"),
   path('pdf_agreement/create/', Pdf_agreementCreateView.as_view(), name="Pdf_agreement-Create"),
   path('pdf_agreement/<int:pk>/', Pdf_agreementUpdateDestroyView.as_view(), name="Pdf_agreement-Create"),
   
]