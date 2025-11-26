from django.shortcuts import render, redirect
from .forms import AgreementForm, Pdf_agreementForm
from .models import Agreement, Pdf_agreement
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from Accounts.models import UserAccounts
from django.contrib import messages 
from rest_framework.decorators import api_view, permission_classes, APIView
from rest_framework.response import Response
from .serializers import AgreementSerializer, Pdf_agreementSerializer
from rest_framework.permissions import IsAdminUser,IsAuthenticated,IsAdminUser , AllowAny
from rest_framework.generics import ListAPIView, CreateAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import status, serializers
from django.http import HttpResponse 
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser


# Create an Agreement by the Authenticated user
class AgreementCreateView(CreateAPIView):
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    serializer_class = AgreementSerializer
      
    def perform_create(self, serializer):
        print("Received request data:", self.request.data)
        # No need to manually fetch pdf_agreement; serializer handles it
        serializer.save(user=self.request.user)

# View List of Agreements by the Admin
class AgreementListView(ListAPIView):
    permission_classes=[IsAdminUser]
    serializer_class = AgreementSerializer
    
    def get_queryset(self):
        return Agreement.objects.select_related('user').all().order_by('-submited_date')


# Get detail of Agreement and Delete by the Admin
class AgreementDetailView(APIView):

    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        try:
            return Agreement.objects.get(pk=pk)
        except Agreement.DoesNotExist:
            return None

    def get(self, request, pk):
        
        agreement = self.get_object(pk)
        if not agreement:
            return Response(
                {'detail': 'Agreement not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AgreementSerializer(agreement)
        return Response(serializer.data)
    
    def patch(self, request, pk):
        agreement = self.get_object(pk)
        if not agreement:
            return Response(
                {'detail': 'Agreement not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AgreementSerializer(agreement, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        agreement = self.get_object(pk)
        if agreement is None:
            return Response({'detail':'agreement not found'}, status=status.HTTP_404_NOT_FOUND)
        agreement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class Pdf_agreementCreateView(CreateAPIView):
    serializer_class = Pdf_agreementSerializer
    permission_classes = [IsAdminUser] 


class Pdf_agreementUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    serializer_class = Pdf_agreementSerializer
    permission_classes = [IsAdminUser]

    def get_object(self):
        pk = self.kwargs.get('pk')
        try:
            return Pdf_agreement.objects.get(pk=pk)
        except Pdf_agreement.DoesNotExist:
            return None

    def patch(self, request, pk=None):
        pdf = self.get_object()
        if not pdf:
            return Response({'detail': 'pdf not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = Pdf_agreementSerializer(pdf, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        pdf = self.get_object()
        if not pdf:
            return Response({'detail': 'pdf not found'}, status=status.HTTP_404_NOT_FOUND)
        pdf.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class Pdf_agreementListView(ListAPIView):
    queryset = Pdf_agreement.objects.all()
    serializer_class = Pdf_agreementSerializer
    permission_classes = [AllowAny]


    def get_serializer_context(self):
        return {'request': self.request}
    
def pdf_file_view(request, pk):
     
        pdf = get_object_or_404(Pdf_agreement, pk=pk)
        response = FileResponse(pdf.pdf_file.open(), content_type='application/pdf')
        response['X-Frame-Options'] = 'ALLOWALL'   # ✅ allows embedding only for this response
        return response
    
    