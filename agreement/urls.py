from django.urls import path
from .views import (
    AgreementCreateView,
    AgreementDetailView,
    AgreementListView,
    AgreementPDFDownloadView,
    MyAgreementsListView,
    pdf_file_view,
    pdf_sample_view,
    Pdf_agreementCreateView,
    Pdf_agreementUpdateDestroyView,
    Pdf_agreementListView,
    AuditLogListView,
)

urlpatterns = [
    # agreement
    path('agreement/', AgreementCreateView.as_view(), name="agreement-create"),
    path('agreement_list/', AgreementListView.as_view(), name="agreement-list"),
    path('agreement/<int:pk>/', AgreementDetailView.as_view(), name="agreement-datail"),
    path('agreement/<int:pk>/pdf/', AgreementPDFDownloadView.as_view(), name="agreement-pdf"),
    path('my-agreements/', MyAgreementsListView.as_view(), name="my-agreements"),

    # pdf_agreements (templates)
    path('pdf/sample/', pdf_sample_view, name='pdf-sample'),
    path('pdf/<int:pk>/', pdf_file_view, name='pdf_file_view'),
    path('pdf_agreement/', Pdf_agreementListView.as_view(), name="pdf-agreement-list"),
    path('pdf_agreement/create/', Pdf_agreementCreateView.as_view(), name="pdf-agreement-create"),
    path('pdf_agreement/<int:pk>/', Pdf_agreementUpdateDestroyView.as_view(), name="pdf-agreement-detail"),

    # audit trail
    path('audit-log/', AuditLogListView.as_view(), name="audit-log"),
]
